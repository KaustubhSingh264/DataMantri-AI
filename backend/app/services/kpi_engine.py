import math
from typing import Optional

import numpy as np
import pandas as pd


def _to_native(value):
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        # convert NaN to None for JSON safety
        if math.isnan(value):
            return None
        return float(value)
    if pd.isna(value):
        return None
    return value


def _round_display(value):
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        # default display rounding to 2 decimals for floats
        return round(value, 2)
    return value


def _safe_div(numerator, denominator):
    try:
        if denominator == 0:
            return None
        return numerator / denominator
    except Exception:
        return None


def _validate_percent(value):
    if value is None:
        return None
    if value < 0:
        return 0.0
    if value > 100:
        return 100.0
    return float(value)


def generate_kpis(df: pd.DataFrame, cleaned_df: Optional[pd.DataFrame] = None) -> dict:
    """
    Generate strict, auditable KPIs following the platform rules.

    Returns a dictionary with clearly structured KPI groups. Each scalar KPI is an object:
      {"raw_value": ..., "display_value": ..., "formula": "...", "confidence": 100}

    If `cleaned_df` is provided, an `after_cleaning` section is included and improvement metrics computed.
    """

    if not isinstance(df, pd.DataFrame):
        raise ValueError("df must be a pandas DataFrame")

    result = {
        "profile": {},
        "missing_metrics": {},
        "duplicate_metrics": {},
        "numeric_stats": {},
        "categorical_stats": {},
        "trends": {},
        "data_health": {},
        "before_cleaning": {},
        "after_cleaning": None,
        "validation": {"ok": True, "errors": []},
    }

    total_rows = int(len(df))
    total_columns = int(len(df.columns)) if total_rows >= 0 else 0

    # ------------------
    # Section: Profiling
    # ------------------
    profile = {}
    dtypes = df.dtypes.astype(str).to_dict()
    profile["columns"] = {}
    for col in df.columns:
        col_series = df[col]
        col_dtype = str(col_series.dtype)
        is_id = False
        cname = str(col).lower()
        if cname.endswith("id") or cname == "id" or "_id" in cname or cname.startswith("id_"):
            is_id = True

        # detect dates
        is_date = False
        try:
            if pd.api.types.is_datetime64_any_dtype(col_series):
                is_date = True
            else:
                parsed = pd.to_datetime(col_series.dropna().head(50), errors="coerce")
                if parsed.notna().sum() >= 5:
                    is_date = True
        except Exception:
            is_date = False

        is_bool = pd.api.types.is_bool_dtype(col_series)
        is_numeric = pd.api.types.is_numeric_dtype(col_series) and not is_bool
        is_integer = False
        is_float = False
        if is_numeric:
            is_integer = pd.api.types.is_integer_dtype(col_series.dropna())
            is_float = not is_integer

        is_categorical = (not is_numeric) and (col_series.nunique(dropna=True) < max(50, total_rows * 0.5))
        is_text = (not is_numeric) and (col_series.map(lambda x: isinstance(x, str)).sum() > 0)

        profile["columns"][col] = {
            "dtype": col_dtype,
            "is_id": bool(is_id),
            "is_date": bool(is_date),
            "is_boolean": bool(is_bool),
            "is_numeric": bool(is_numeric),
            "is_integer": bool(is_integer),
            "is_float": bool(is_float),
            "is_categorical": bool(is_categorical),
            "is_text": bool(is_text),
            "non_null_count": int(col_series.count()),
            "unique_count": int(col_series.nunique(dropna=True)),
        }

    result["profile"] = profile

    # ------------------
    # Section: Missing data
    # ------------------
    missing_cells = int(df.isna().sum().sum())
    rows_with_missing = int(df.isna().any(axis=1).sum())
    cols_with_missing = int((df.isna().sum() > 0).sum())
    missing_percentage = _safe_div(missing_cells, total_rows * total_columns)
    missing_percentage = None if missing_percentage is None else round(missing_percentage * 100, 4)
    missing_percentage = _validate_percent(missing_percentage)

    result["missing_metrics"] = {
        "missing_cells": {"raw_value": missing_cells, "display_value": missing_cells, "formula": "sum(isna())", "confidence": 100},
        "missing_rows": {"raw_value": rows_with_missing, "display_value": rows_with_missing, "formula": "count(rows where any isna)", "confidence": 100},
        "missing_columns": {"raw_value": cols_with_missing, "display_value": cols_with_missing, "formula": "count(columns where any isna)", "confidence": 100},
        "missing_percentage": {"raw_value": missing_percentage, "display_value": _round_display(missing_percentage), "formula": "missing_cells / (total_rows * total_columns) * 100", "confidence": 100},
    }

    # ------------------
    # Section: Duplicates
    # ------------------
    duplicate_rows = int(df.duplicated().sum())
    duplicate_percentage = _safe_div(duplicate_rows, total_rows)
    duplicate_percentage = None if duplicate_percentage is None else round(duplicate_percentage * 100, 4)
    duplicate_percentage = _validate_percent(duplicate_percentage)

    result["duplicate_metrics"] = {
        "duplicate_rows": {"raw_value": duplicate_rows, "display_value": duplicate_rows, "formula": "count(duplicated rows)", "confidence": 100},
        "duplicate_percentage": {"raw_value": duplicate_percentage, "display_value": _round_display(duplicate_percentage), "formula": "duplicate_rows / total_rows * 100", "confidence": 100},
    }

    # ------------------
    # Section: Numeric KPIs
    # ------------------
    numeric_cols = [c for c, p in profile["columns"].items() if p["is_numeric"] and not p["is_id"]]
    for col in numeric_cols:
        series = pd.to_numeric(df[col], errors="coerce")
        non_null_count = int(series.count())
        raw_sum = _to_native(series.sum())
        raw_mean = _to_native(_safe_div(series.sum(), non_null_count))
        raw_median = _to_native(series.median())
        raw_min = _to_native(series.min())
        raw_max = _to_native(series.max())
        raw_std = _to_native(series.std())
        raw_var = _to_native(series.var())
        missing_count = int(series.isna().sum())

        result["numeric_stats"][col] = {
            "sum": {"raw_value": raw_sum, "display_value": _round_display(raw_sum), "formula": "sum(non-null values)", "confidence": 100},
            "mean": {"raw_value": raw_mean, "display_value": _round_display(raw_mean), "formula": "sum(non-null values) / count(non-null)", "confidence": 100},
            "median": {"raw_value": raw_median, "display_value": _round_display(raw_median), "formula": "median(non-null values)", "confidence": 100},
            "min": {"raw_value": raw_min, "display_value": _round_display(raw_min), "formula": "min(non-null values)", "confidence": 100},
            "max": {"raw_value": raw_max, "display_value": _round_display(raw_max), "formula": "max(non-null values)", "confidence": 100},
            "std_dev": {"raw_value": raw_std, "display_value": _round_display(raw_std), "formula": "std(non-null values)", "confidence": 100},
            "variance": {"raw_value": raw_var, "display_value": _round_display(raw_var), "formula": "var(non-null values)", "confidence": 100},
            "missing_count": {"raw_value": missing_count, "display_value": missing_count, "formula": "count(isna)", "confidence": 100},
            "non_null_count": {"raw_value": non_null_count, "display_value": non_null_count, "formula": "count(non-null)", "confidence": 100},
        }

    # ------------------
    # Section: Categorical KPIs
    # ------------------
    categorical_cols = [c for c, p in profile["columns"].items() if p["is_categorical"] or (p["is_text"] and not p["is_id"])]
    for col in categorical_cols:
        series = df[col]
        non_null = int(series.count())
        if non_null == 0:
            top_val = None
            top_count = 0
            top_percent = None
        else:
            top_val = None
            try:
                top_series = series.dropna().value_counts()
                if not top_series.empty:
                    top_val = _to_native(top_series.index[0])
                    top_count = int(top_series.iloc[0])
                    top_percent = _validate_percent(round(_safe_div(top_count, non_null) * 100, 4))
                else:
                    top_count = 0
                    top_percent = None
            except Exception:
                top_val = None
                top_count = 0
                top_percent = None

        result["categorical_stats"][col] = {
            "top_category": {"raw_value": top_val, "display_value": top_val, "formula": "mode(non-null values)", "confidence": 100},
            "top_category_count": {"raw_value": top_count, "display_value": top_count, "formula": "count(top category occurrences)", "confidence": 100},
            "top_category_percentage": {"raw_value": top_percent, "display_value": _round_display(top_percent), "formula": "top_count / non_null_values * 100", "confidence": 100},
            "unique_count": {"raw_value": int(series.nunique(dropna=True)), "display_value": int(series.nunique(dropna=True)), "formula": "nunique(non-null)", "confidence": 100},
            "non_null_count": {"raw_value": non_null, "display_value": non_null, "formula": "count(non-null)", "confidence": 100},
        }

    # ------------------
    # Trends: only when valid time dimension exists
    # ------------------
    accepted_time_names = ["date", "created_at", "timestamp", "order_date", "month", "year"]
    time_cols = []
    for col in df.columns:
        lname = col.lower()
        if any(name in lname for name in accepted_time_names):
            try:
                parsed = pd.to_datetime(df[col], errors="coerce")
                if parsed.notna().sum() >= max(3, int(total_rows * 0.01)):
                    time_cols.append(col)
            except Exception:
                continue

    if not time_cols:
        result["trends"]["note"] = "No valid time dimension available."
    else:
        # pick the first valid time col
        time_col = time_cols[0]
        ts = pd.to_datetime(df[time_col], errors="coerce")
        timeline = pd.DataFrame({"_time": ts})
        timeline["__row_index"] = df.index
        timeline = timeline.dropna(subset=["_time"]) 
        if timeline.empty:
            result["trends"]["note"] = "No valid time dimension available after parsing."
        else:
            # aggregate by day for stability, then compute linear slope per numeric column
            timeline_indexed = timeline.set_index("__row_index")
            merged = df.join(timeline_indexed["_time"], how="left")
            merged = merged.dropna(subset=["_time"]) 
            merged["_time_ordinal"] = merged["_time"].astype("int64") // 10 ** 9
            for num in numeric_cols:
                series = merged[["_time_ordinal", num]].dropna()
                if len(series) < 3:
                    result["trends"][num] = {"note": "insufficient time-series points"}
                    continue
                x = series["_time_ordinal"].values
                y = pd.to_numeric(series[num], errors="coerce").values
                # simple linear fit (y = a*x + b)
                try:
                    a, b = np.polyfit(x, y, 1)
                    # slope per second -> convert to per day approx
                    slope_per_day = a * 86400
                    result["trends"][num] = {
                        "slope_per_day": _to_native(slope_per_day),
                        "formula": "linear_regression_slope_on(aggregated_time_series)",
                        "confidence": 100,
                    }
                except Exception:
                    result["trends"][num] = {"note": "could not compute trend"}

    # ------------------
    # Data Health Score
    # ------------------
    # Penalties normalized 0..1
    missing_penalty = (_safe_div(missing_cells, total_rows * total_columns) or 0)  # proportion
    duplicate_penalty = (_safe_div(duplicate_rows, total_rows) or 0)

    # invalid values: for numeric columns, count non-null entries that coerce to NaN
    invalid_values = 0
    for col in numeric_cols:
        coerced = pd.to_numeric(df[col], errors="coerce")
        invalid_values += int(df[col].notna().sum() - coerced.notna().sum())
    invalid_penalty = _safe_div(invalid_values, total_rows * max(1, len(numeric_cols))) or 0

    # outliers: IQR method per numeric column, count distinct rows flagged
    outlier_rows = set()
    for col in numeric_cols:
        s = pd.to_numeric(df[col], errors="coerce")
        s = s.dropna()
        if len(s) < 4:
            continue
        q1 = s.quantile(0.25)
        q3 = s.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        mask = (df[col] < lower) | (df[col] > upper)
        outlier_rows.update(df.index[mask.fillna(False)].tolist())
    outlier_count = len(outlier_rows)
    outlier_penalty = _safe_div(outlier_count, total_rows) or 0

    # weights
    missing_weight = 0.4
    duplicate_weight = 0.3
    invalid_weight = 0.2
    outlier_weight = 0.1

    health_penalty = missing_penalty * missing_weight + duplicate_penalty * duplicate_weight + invalid_penalty * invalid_weight + outlier_penalty * outlier_weight
    health_score_raw = max(0.0, min(100.0, round((1 - health_penalty) * 100, 4)))

    result["data_health"] = {
        "missing_penalty": {"raw_value": _to_native(missing_penalty), "display_value": _round_display(missing_penalty), "formula": "missing_cells / (rows*cols)", "confidence": 100},
        "duplicate_penalty": {"raw_value": _to_native(duplicate_penalty), "display_value": _round_display(duplicate_penalty), "formula": "duplicate_rows / rows", "confidence": 100},
        "invalid_penalty": {"raw_value": _to_native(invalid_penalty), "display_value": _round_display(invalid_penalty), "formula": "invalid_values / (rows * numeric_columns)", "confidence": 100},
        "outlier_penalty": {"raw_value": _to_native(outlier_penalty), "display_value": _round_display(outlier_penalty), "formula": "outlier_rows / rows", "confidence": 100},
        "health_score": {"raw_value": health_score_raw, "display_value": _round_display(health_score_raw), "formula": "health_score = 100 * (1 - (missing_penalty*0.4 + duplicate_penalty*0.3 + invalid_penalty*0.2 + outlier_penalty*0.1))", "confidence": 100},
    }

    # ------------------
    # Before cleaning summary
    # ------------------
    result["before_cleaning"] = {
        "row_count": {"raw_value": total_rows, "display_value": total_rows, "formula": "len(df)", "confidence": 100},
        "column_count": {"raw_value": total_columns, "display_value": total_columns, "formula": "len(df.columns)", "confidence": 100},
        "missing_percentage": result["missing_metrics"]["missing_percentage"],
        "duplicate_percentage": result["duplicate_metrics"]["duplicate_percentage"],
        "data_health_score": result["data_health"]["health_score"],
    }

    # ------------------
    # After cleaning (optional)
    # ------------------
    if cleaned_df is not None and isinstance(cleaned_df, pd.DataFrame):
        after = generate_kpis(cleaned_df, cleaned_df=None)
        # only include selected improvement metrics to avoid recursion
        try:
            before_missing = result["missing_metrics"]["missing_percentage"]["raw_value"]
            after_missing = after["missing_metrics"]["missing_percentage"]["raw_value"]
            improvement_missing = None
            if before_missing is not None and after_missing is not None:
                improvement_missing = round(after_missing - before_missing, 4)
        except Exception:
            improvement_missing = None

        result["after_cleaning"] = {
            "rows_removed": {"raw_value": total_rows - len(cleaned_df), "display_value": int(total_rows - len(cleaned_df)), "formula": "before_rows - after_rows", "confidence": 100},
            "duplicates_removed": {"raw_value": duplicate_rows - int(cleaned_df.duplicated().sum()), "display_value": _round_display(duplicate_rows - int(cleaned_df.duplicated().sum())), "formula": "before_duplicates - after_duplicates", "confidence": 100},
            "missing_before": result["missing_metrics"]["missing_percentage"],
            "missing_after": after["missing_metrics"]["missing_percentage"],
            "missing_improvement": {"raw_value": improvement_missing, "display_value": _round_display(improvement_missing), "formula": "missing_after - missing_before", "confidence": 100},
        }

    # ------------------
    # Validation checks
    # ------------------
    errors = []
    mp = result["missing_metrics"]["missing_percentage"]["raw_value"]
    dp = result["duplicate_metrics"]["duplicate_percentage"]["raw_value"]
    hs = result["data_health"]["health_score"]["raw_value"]
    if mp is not None and (mp < 0 or mp > 100):
        errors.append("missing_percentage out of bounds")
    if dp is not None and (dp < 0 or dp > 100):
        errors.append("duplicate_percentage out of bounds")
    # check categorical percentages
    for c, stats in result["categorical_stats"].items():
        pct = stats["top_category_percentage"]["raw_value"]
        if pct is not None and (pct < 0 or pct > 100):
            errors.append(f"top_category_percentage out of bounds for {c}")
    if hs is not None and (hs < 0 or hs > 100):
        errors.append("health_score out of bounds")
    if total_rows < 0:
        errors.append("row count negative")
    if total_columns < 1:
        errors.append("column count < 1")

    result["validation"]["ok"] = len(errors) == 0
    result["validation"]["errors"] = errors

    # ------------------
    # Discovery: add a flat list of discovered business KPIs and metadata
    # This is additive and preserves existing structure.
    try:
        from app.services.kpi_discovery import discover_kpis

        try:
            discovery = discover_kpis(df, profile, result)
            result["discovered_kpis"] = discovery.get("discovered_kpis", {})
            result["discovery_metadata"] = discovery.get("metadata", {})
        except Exception as e:
            result["discovered_kpis"] = {}
            result["discovery_metadata"] = {"error": str(e)}
        # Phase B: attach lightweight advanced insights (trends, correlations, anomalies)
        try:
            from app.services.kpi_trends import detect_trends
            from app.services.kpi_correlation import top_correlations
            from app.services.anomaly_detection import detect_anomalies

            adv = {}
            # trends: use profile to pick time col and numeric cols
            try:
                trends_out = detect_trends(df, profile)
                adv["trends"] = trends_out
            except Exception:
                adv["trends"] = {"error": "trend_detection_failed"}

            # correlations: top pairs
            try:
                numeric_cols = [c for c, p in profile.get("columns", {}).items() if p.get("is_numeric") and not p.get("is_id")]
                corr_out = top_correlations(df, numeric_cols=numeric_cols, top_n=10, threshold=0.45)
                adv["correlations"] = corr_out
            except Exception:
                adv["correlations"] = []

            # anomalies
            try:
                anom_out = detect_anomalies(df, numeric_cols=numeric_cols, z_threshold=3.0)
                adv["anomalies"] = anom_out
            except Exception:
                adv["anomalies"] = []

            # merge into discovery metadata for backward-compatible access
            if isinstance(result.get("discovery_metadata"), dict):
                result["discovery_metadata"]["advanced_insights"] = adv
            else:
                result["discovery_metadata"] = {"advanced_insights": adv}
        except Exception:
            # non-fatal: do not break primary KPI generation
            try:
                if isinstance(result.get("discovery_metadata"), dict):
                    result["discovery_metadata"]["advanced_insights"] = {"error": "phase_b_modules_unavailable"}
                else:
                    result["discovery_metadata"] = {"advanced_insights": {"error": "phase_b_modules_unavailable"}}
            except Exception:
                pass
    except Exception:
        # discovery module not available or failed import; keep response unchanged
        result["discovered_kpis"] = {}
        result["discovery_metadata"] = {}

    return result
