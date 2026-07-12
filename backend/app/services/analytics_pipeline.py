import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from app.services.anomaly_detection import detect_anomalies
from app.services.anomaly_engine import detect_ml_anomalies
from app.services.data_profiler import profile_data
from app.analytics.dataset_health import assess_dataset_health
from app.analytics.feature_store import build_feature_store_metadata
from app.services.dataset_profiler import discover_dynamic_kpis, inspect_dataset
from app.services.domain_classifier import classify_domain
from app.services.explanation_engine import explain_predictions
from app.services.feature_engineering import engineer_features
from app.services.forecast_engine import generate_forecast_chart, generate_ml_forecasts
from app.services.insight_engine import generate_insights
from app.services.kpi_correlation import top_correlations
from app.services.kpi_engine import generate_kpis
from app.services.kpi_trends import detect_trends
from app.services.recommendation_engine import generate_recommendations
from app.services.segmentation_engine import segment_records
from app.services.visualization_engine import generate_visualizations
from app.services.localization_service import language_prompt_context, localize_analysis_payload, normalize_language

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".json"}
MAX_PROFILE_ROWS = 100_000
MAX_CHART_ROWS = 25_000
KPI_ROLE_KEYWORDS = {
    "Revenue": ["revenue", "sales", "amount", "gmv", "gross", "net sales", "total"],
    "Profit": ["profit", "earnings", "net income", "contribution"],
    "Cost": ["cost", "expense", "spend", "cogs"],
    "Orders": ["order", "invoice", "transaction"],
    "Units": ["unit", "quantity", "qty", "volume"],
    "Customers": ["customer", "client", "buyer", "user"],
    "Products": ["product", "sku", "item", "category"],
    "Categories": ["category", "segment", "department", "brand"],
    "Headcount": ["employee", "headcount", "staff"],
    "Attrition": ["attrition", "churn", "termination", "resigned"],
    "Margins": ["margin", "margin_rate", "gross margin"],
    "Inventory": ["inventory", "stock", "on hand"],
    "Conversion Rate": ["conversion", "converted", "rate"],
    "Discount": ["discount", "coupon", "markdown"],
    "Returns": ["return", "refund", "cancel"],
    "Ratings": ["rating", "review", "stars", "score"],
    "Cities": ["city", "town"],
    "Regions": ["region", "state", "zone", "territory"],
    "Stores": ["store", "branch", "outlet"],
}


@dataclass
class PipelineContext:
    function_name: str
    dataset_id: Optional[int] = None
    upload_id: Optional[int] = None
    user_id: Optional[int] = None

    def as_extra(self) -> Dict[str, Any]:
        return {
            "function_name": self.function_name,
            "dataset_id": self.dataset_id,
            "upload_id": self.upload_id,
            "user_id": self.user_id,
        }


def log_stage(stage: str, ctx: PipelineContext, **fields: Any) -> None:
    payload = {"stage": stage, **ctx.as_extra(), **fields}
    logger.info("analytics_pipeline_stage", extra={"analytics": payload})


def log_exception(stage: str, ctx: PipelineContext, exc: Exception, **fields: Any) -> None:
    payload = {"stage": stage, **ctx.as_extra(), **fields}
    logger.exception("analytics_pipeline_exception", extra={"analytics": payload})


def sanitize_columns(columns: List[Any]) -> Tuple[List[str], Dict[str, str], List[str]]:
    clean_columns: List[str] = []
    rename_map: Dict[str, str] = {}
    duplicates: List[str] = []
    seen: Dict[str, int] = {}

    for raw_column in columns:
        original = str(raw_column).strip() or "column"
        normalized = re.sub(r"\s+", " ", original)
        count = seen.get(normalized, 0)
        seen[normalized] = count + 1
        final_name = normalized if count == 0 else f"{normalized}_{count + 1}"
        if count > 0:
            duplicates.append(normalized)
        clean_columns.append(final_name)
        rename_map[str(raw_column)] = final_name

    return clean_columns, rename_map, duplicates


def normalize_dataframe(df: pd.DataFrame, ctx: PipelineContext) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    log_stage("normalize_dataframe:start", ctx, rows=len(df), columns=len(df.columns))
    normalized = df.copy()
    normalized.columns, rename_map, duplicate_columns = sanitize_columns(list(normalized.columns))
    empty_columns = [col for col in normalized.columns if normalized[col].isna().all()]
    converted_numeric: List[str] = []
    converted_datetime: List[str] = []

    for column in normalized.columns:
        series = normalized[column]
        if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
            stripped = series.map(lambda value: value.strip() if isinstance(value, str) else value)
            normalized[column] = stripped
            non_null = stripped.dropna()
            if non_null.empty:
                continue

            numeric_candidate = pd.to_numeric(
                non_null.astype(str)
                .str.replace(",", "", regex=False)
                .str.replace("$", "", regex=False)
                .str.replace("₹", "", regex=False)
                .str.replace("%", "", regex=False),
                errors="coerce",
            )
            if numeric_candidate.notna().mean() >= 0.85:
                normalized[column] = pd.to_numeric(
                    stripped.astype(str)
                    .str.replace(",", "", regex=False)
                    .str.replace("$", "", regex=False)
                    .str.replace("₹", "", regex=False)
                    .str.replace("%", "", regex=False),
                    errors="coerce",
                )
                converted_numeric.append(column)
                continue

            try:
                parsed = pd.to_datetime(stripped, errors="coerce", format="mixed")
            except TypeError:
                parsed = pd.to_datetime(stripped, errors="coerce")
            if parsed.notna().mean() >= 0.85:
                normalized[column] = parsed
                converted_datetime.append(column)

    normalized = normalized.convert_dtypes()
    report = {
        "renamed_columns": rename_map,
        "duplicate_columns": duplicate_columns,
        "empty_columns": empty_columns,
        "numeric_columns_converted": converted_numeric,
        "datetime_columns_converted": converted_datetime,
    }
    log_stage("normalize_dataframe:complete", ctx, **report)
    return normalized, report


def read_dataset(file_path: Path, original_filename: str, ctx: PipelineContext) -> pd.DataFrame:
    extension = Path(original_filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError("Unsupported file type. Upload CSV, XLSX, or JSON.")

    log_stage("read_dataset:start", ctx, filename=original_filename, extension=extension)
    try:
        if extension == ".csv":
            try:
                df = pd.read_csv(file_path, low_memory=False, on_bad_lines="warn")
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, encoding="latin1", low_memory=False, on_bad_lines="warn")
        elif extension in {".xlsx", ".xls"}:
            df = pd.read_excel(file_path)
        else:
            df = pd.read_json(file_path)
            if isinstance(df, pd.Series):
                df = df.to_frame()
    except ValueError:
        raise
    except Exception as exc:
        log_exception("read_dataset:failed", ctx, exc, filename=original_filename)
        raise ValueError(f"Could not read dataset: {exc}") from exc

    if df.empty or len(df.columns) == 0:
        raise ValueError("Dataset is empty or has no columns.")

    log_stage("read_dataset:complete", ctx, rows=len(df), columns=len(df.columns))
    return df


def infer_semantic_schema(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    schema: Dict[str, Dict[str, Any]] = {}
    row_count = max(len(df), 1)
    for column in df.columns:
        series = df[column]
        lower = str(column).lower()
        non_null = series.dropna()
        unique_count = int(series.nunique(dropna=True))
        semantic_type = "text"
        if pd.api.types.is_datetime64_any_dtype(series):
            semantic_type = "datetime"
        elif pd.api.types.is_numeric_dtype(series):
            if "id" == lower or lower.endswith("_id") or lower.endswith(" id") or unique_count / row_count > 0.9:
                semantic_type = "id"
            elif any(term in lower for term in ["percent", "percentage", "rate", "margin"]):
                semantic_type = "percentage"
            elif any(term in lower for term in ["revenue", "sales", "amount", "price", "cost", "salary", "expense", "profit", "cash"]):
                semantic_type = "currency"
            else:
                semantic_type = "numeric"
        elif any(term in lower for term in ["date", "time", "created", "updated"]):
            semantic_type = "datetime_candidate"
        elif any(term in lower for term in ["city", "state", "country", "region", "location", "market"]):
            semantic_type = "location"
        elif unique_count <= min(50, row_count * 0.5):
            semantic_type = "categorical"

        schema[column] = {
            "dtype": str(series.dtype),
            "semantic_type": semantic_type,
            "non_null_count": int(series.count()),
            "missing_count": int(series.isna().sum()),
            "missing_percent": round(float(series.isna().mean() * 100), 2),
            "unique_count": unique_count,
            "sample_values": [str(value) for value in non_null.head(3).tolist()],
        }
    return schema


def build_validation_report(df: pd.DataFrame, normalize_report: Dict[str, Any]) -> Dict[str, Any]:
    total_cells = max(int(df.shape[0] * df.shape[1]), 1)
    missing_cells = int(df.isna().sum().sum())
    duplicate_rows = int(df.duplicated().sum())
    issues: List[Dict[str, Any]] = []

    if missing_cells:
        issues.append({"severity": "medium", "type": "missing_values", "message": f"{missing_cells} cells are missing."})
    if duplicate_rows:
        issues.append({"severity": "medium", "type": "duplicate_rows", "message": f"{duplicate_rows} duplicate rows detected."})
    for column in normalize_report.get("empty_columns", []):
        issues.append({"severity": "high", "type": "empty_column", "column": column, "message": f"{column} is completely empty."})
    for column in normalize_report.get("duplicate_columns", []):
        issues.append({"severity": "high", "type": "duplicate_column", "column": column, "message": f"{column} appeared more than once and was renamed."})

    return {
        "row_count": int(df.shape[0]),
        "column_count": int(df.shape[1]),
        "missing_percent": round(missing_cells / total_cells * 100, 2),
        "duplicate_percent": round(duplicate_rows / max(len(df), 1) * 100, 2),
        "detected_issues": issues,
        "inferred_schema": infer_semantic_schema(df),
        "normalization": normalize_report,
    }


def _humanize(value: str) -> str:
    return str(value or "").replace("_", " ").strip().title()


def _numeric_value(value: Any) -> Optional[float]:
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


def _safe_percent(numerator: float, denominator: float) -> Optional[float]:
    if denominator in (0, None):
        return None
    return round(float(numerator) / abs(float(denominator)) * 100, 2)


def _safe_divide(numerator: float, denominator: float) -> Optional[float]:
    if denominator in (0, None):
        return None
    return round(float(numerator) / float(denominator), 2)


def find_role_columns(df: pd.DataFrame) -> Dict[str, List[str]]:
    roles: Dict[str, List[str]] = {role: [] for role in KPI_ROLE_KEYWORDS}
    columns = list(df.columns)
    for role, keywords in KPI_ROLE_KEYWORDS.items():
        for column in columns:
            lower = str(column).lower().replace("_", " ")
            if any(keyword in lower for keyword in keywords):
                roles[role].append(column)
    return roles


def choose_measure(df: pd.DataFrame, roles: Dict[str, List[str]]) -> Optional[str]:
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    for role in ["Revenue", "Profit", "Cost", "Units", "Inventory", "Margins", "Conversion Rate"]:
        for column in roles.get(role, []):
            if column in numeric_cols:
                return column
    return numeric_cols[0] if numeric_cols else None


def choose_dimension(df: pd.DataFrame, roles: Dict[str, List[str]]) -> Optional[str]:
    categorical_cols = df.select_dtypes(include=["object", "category", "string"]).columns.tolist()
    for role in ["Products", "Customers", "Orders"]:
        for column in roles.get(role, []):
            if column in categorical_cols:
                return column
    return categorical_cols[0] if categorical_cols else None


def detect_dataset_profile(df: pd.DataFrame, validation_report: Dict[str, Any]) -> Dict[str, Any]:
    schema = validation_report.get("inferred_schema", {})
    return {
        "rows": validation_report.get("row_count", len(df)),
        "columns": validation_report.get("column_count", len(df.columns)),
        "schema": schema,
        "missing_statistics": {
            column: {
                "missing_count": meta.get("missing_count", 0),
                "missing_percent": meta.get("missing_percent", 0),
            }
            for column, meta in schema.items()
        },
        "duplicate_statistics": {
            "duplicate_rows": int(df.duplicated().sum()),
            "duplicate_percent": validation_report.get("duplicate_percent", 0),
        },
        "cardinality": {column: int(df[column].nunique(dropna=True)) for column in df.columns},
        "inferred_data_types": {column: meta.get("semantic_type") for column, meta in schema.items()},
    }


def discover_business_kpis(df: pd.DataFrame, profile: Dict[str, Any], trend_engine: Dict[str, Any]) -> List[Dict[str, Any]]:
    roles = find_role_columns(df)
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category", "string"]).columns.tolist()
    kpis: List[Dict[str, Any]] = []

    def add_kpi(name: str, value: Any, source_columns: List[str], explanation: str, confidence: int = 80):
        if value is None:
            return
        trend_card = next((card for card in trend_engine.get("cards", []) if any(col in card.get("label", "") for col in source_columns)), None)
        kpis.append({
            "name": name,
            "value": round(value, 2) if isinstance(value, float) else value,
            "trend": trend_card.get("trend", 0) if trend_card else 0,
            "trend_direction": trend_card.get("trend_direction", "flat") if trend_card else "flat",
            "confidence": confidence,
            "business_explanation": explanation,
            "evidence": [{"column": column, "aggregation": "sum" if column in numeric_cols else "nunique"} for column in source_columns],
        })

    for role in ["Revenue", "Profit", "Cost", "Units", "Inventory", "Discount", "Returns"]:
        for column in roles.get(role, []):
            if column in numeric_cols:
                total = _numeric_value(pd.to_numeric(df[column], errors="coerce").sum())
                add_kpi(role, total, [column], f"{role} is inferred from {_humanize(column)} and summed across all valid rows.", 88)
                break

    for role in ["Orders", "Customers", "Products", "Headcount", "Categories", "Cities", "Regions", "Stores"]:
        for column in roles.get(role, []):
            if column in df.columns:
                value = int(df[column].nunique(dropna=True))
                add_kpi(role, value, [column], f"{role} is inferred from distinct values in {_humanize(column)}.", 82)
                break

    revenue_col = next((col for col in roles.get("Revenue", []) if col in numeric_cols), None)
    profit_col = next((col for col in roles.get("Profit", []) if col in numeric_cols), None)
    cost_col = next((col for col in roles.get("Cost", []) if col in numeric_cols), None)
    if revenue_col and profit_col:
        revenue = pd.to_numeric(df[revenue_col], errors="coerce").sum()
        profit = pd.to_numeric(df[profit_col], errors="coerce").sum()
        margin = _safe_percent(profit, revenue)
        add_kpi("Margins", margin, [profit_col, revenue_col], f"Margin is calculated as {_humanize(profit_col)} divided by {_humanize(revenue_col)}.", 90)
    elif revenue_col and cost_col:
        revenue = pd.to_numeric(df[revenue_col], errors="coerce").sum()
        cost = pd.to_numeric(df[cost_col], errors="coerce").sum()
        margin = _safe_percent(revenue - cost, revenue)
        add_kpi("Margins", margin, [revenue_col, cost_col], f"Margin is calculated from {_humanize(revenue_col)} minus {_humanize(cost_col)}, divided by revenue.", 84)

    conversion_col = next((col for col in roles.get("Conversion Rate", []) if col in numeric_cols), None)
    if conversion_col:
        avg_conversion = _numeric_value(pd.to_numeric(df[conversion_col], errors="coerce").mean())
        add_kpi("Conversion Rate", avg_conversion, [conversion_col], f"Conversion Rate is inferred from average {_humanize(conversion_col)}.", 82)

    rating_col = next((col for col in roles.get("Ratings", []) if col in numeric_cols), None)
    if rating_col:
        add_kpi("Average Rating", _numeric_value(pd.to_numeric(df[rating_col], errors="coerce").mean()), [rating_col], f"Average Rating is calculated from {_humanize(rating_col)}.", 84)

    order_col = next((col for col in roles.get("Orders", []) if col in df.columns), None)
    customer_col = next((col for col in roles.get("Customers", []) if col in df.columns), None)
    product_col = next((col for col in roles.get("Products", []) if col in df.columns), None)
    unit_col = next((col for col in roles.get("Units", []) if col in numeric_cols), None)
    inventory_col = next((col for col in roles.get("Inventory", []) if col in numeric_cols), None)

    if revenue_col and order_col:
        orders = df[order_col].nunique(dropna=True)
        revenue = pd.to_numeric(df[revenue_col], errors="coerce").sum()
        add_kpi("Average Order Value", _safe_divide(revenue, orders) if orders else None, [revenue_col, order_col], f"Average Order Value is {_humanize(revenue_col)} divided by unique {_humanize(order_col)}.", 88)
    if revenue_col and customer_col:
        customers = df[customer_col].nunique(dropna=True)
        revenue = pd.to_numeric(df[revenue_col], errors="coerce").sum()
        add_kpi("Revenue Per Customer", _safe_divide(revenue, customers) if customers else None, [revenue_col, customer_col], f"Revenue Per Customer is total {_humanize(revenue_col)} divided by unique {_humanize(customer_col)}.", 86)
    if revenue_col and product_col:
        products = df[product_col].nunique(dropna=True)
        revenue = pd.to_numeric(df[revenue_col], errors="coerce").sum()
        add_kpi("Revenue Per Product", _safe_divide(revenue, products) if products else None, [revenue_col, product_col], f"Revenue Per Product is total {_humanize(revenue_col)} divided by unique {_humanize(product_col)}.", 86)
    if unit_col and inventory_col:
        sold = pd.to_numeric(df[unit_col], errors="coerce").sum()
        inventory = pd.to_numeric(df[inventory_col], errors="coerce").mean()
        add_kpi("Inventory Turnover", _safe_divide(sold, inventory) if inventory else None, [unit_col, inventory_col], f"Inventory Turnover compares sold units with available inventory.", 76)

    date_cols = profile.get("datetime_columns", [])
    if revenue_col and date_cols:
        frame = df.copy()
        frame["__time"] = pd.to_datetime(frame[date_cols[0]], errors="coerce")
        monthly = frame.dropna(subset=["__time"]).set_index("__time")[revenue_col].resample("ME").sum().dropna()
        if len(monthly) >= 2:
            previous = float(monthly.iloc[-2])
            current = float(monthly.iloc[-1])
            add_kpi("Growth Rate", None if previous == 0 else round((current - previous) / abs(previous) * 100, 2), [revenue_col, date_cols[0]], f"Growth Rate compares the latest period with the previous period.", 82)
        if len(monthly) >= 3:
            forecast = float(monthly.tail(3).mean())
            add_kpi("Forecast Revenue", round(forecast, 2), [revenue_col, date_cols[0]], f"Forecast Revenue uses the recent 3-period average of {_humanize(revenue_col)}.", 70)
    if unit_col and date_cols:
        days = max(1, (pd.to_datetime(df[date_cols[0]], errors="coerce").max() - pd.to_datetime(df[date_cols[0]], errors="coerce").min()).days)
        velocity = pd.to_numeric(df[unit_col], errors="coerce").sum() / days
        add_kpi("Sales Velocity", round(float(velocity), 2), [unit_col, date_cols[0]], "Sales Velocity is units sold per day in the observed period.", 78)

    if not kpis:
        for column in numeric_cols[:6]:
            add_kpi(f"{_humanize(column)} Total", _numeric_value(pd.to_numeric(df[column], errors="coerce").sum()), [column], f"Metric is dynamically surfaced because {_humanize(column)} is numeric and complete enough for aggregation.", 70)

    return kpis[:12]


def build_advanced_profile(df: pd.DataFrame, profile: Dict[str, Any], roles: Dict[str, List[str]]) -> Dict[str, Any]:
    numeric_cols = profile.get("numeric_columns", [])
    categorical_cols = profile.get("categorical_columns", [])
    date_cols = profile.get("datetime_columns", [])
    measure = choose_measure(df, roles)
    dimension = choose_dimension(df, roles)
    advanced: Dict[str, Any] = {
        "distributions": {},
        "correlations": profile.get("correlations", {}),
        "seasonality": {},
        "outliers": profile.get("outliers", {}),
        "missingness_map": profile.get("missing_percent", {}),
        "concentration_metrics": {},
        "pareto_analysis": {},
        "cohort_analysis": {},
    }

    for column in numeric_cols[:20]:
        values = pd.to_numeric(df[column], errors="coerce").dropna()
        if values.empty:
            continue
        advanced["distributions"][column] = {
            "mean": round(float(values.mean()), 4),
            "median": round(float(values.median()), 4),
            "std": round(float(values.std()), 4) if len(values) > 1 else 0,
            "p25": round(float(values.quantile(0.25)), 4),
            "p75": round(float(values.quantile(0.75)), 4),
            "skew": round(float(values.skew()), 4) if len(values) > 2 else 0,
        }

    for column in categorical_cols[:20]:
        counts = df[column].value_counts(dropna=True)
        if counts.empty:
            continue
        top = counts.head(3)
        advanced["concentration_metrics"][column] = {
            "top_value": str(top.index[0]),
            "top_share": round(float(top.iloc[0] / counts.sum() * 100), 2),
            "top_3_share": round(float(top.sum() / counts.sum() * 100), 2),
        }

    if measure and dimension:
        grouped = df.groupby(dimension)[measure].sum(numeric_only=True).sort_values(ascending=False)
        total = float(grouped.sum())
        if total:
            top3 = grouped.head(3)
            advanced["pareto_analysis"] = {
                "measure": measure,
                "dimension": dimension,
                "top_3_share": round(float(top3.sum() / total * 100), 2),
                "top_contributors": [
                    {"value": str(index), "amount": round(float(value), 2), "share": round(float(value / total * 100), 2)}
                    for index, value in top3.items()
                ],
            }

    if date_cols and measure:
        time_col = date_cols[0]
        frame = df.copy()
        frame["__time"] = pd.to_datetime(frame[time_col], errors="coerce")
        monthly = frame.dropna(subset=["__time"]).set_index("__time")[measure].resample("ME").sum().dropna()
        if len(monthly) >= 4:
            by_month = monthly.groupby(monthly.index.month).mean()
            if not by_month.empty:
                advanced["seasonality"] = {
                    "measure": measure,
                    "peak_month": int(by_month.idxmax()),
                    "low_month": int(by_month.idxmin()),
                    "peak_value": round(float(by_month.max()), 2),
                    "low_value": round(float(by_month.min()), 2),
                }

        customer_col = next((col for col in roles.get("Customers", []) if col in df.columns), None)
        if customer_col:
            cohort = frame.dropna(subset=["__time", customer_col]).copy()
            if not cohort.empty:
                cohort["cohort_month"] = cohort.groupby(customer_col)["__time"].transform("min").dt.to_period("M").astype(str)
                advanced["cohort_analysis"] = {
                    "cohort_column": customer_col,
                    "cohorts": cohort["cohort_month"].value_counts().head(6).to_dict(),
                }

    return advanced


def enrich_profile(df: pd.DataFrame, base_profile: Dict[str, Any], validation_report: Dict[str, Any]) -> Dict[str, Any]:
    profile = dict(base_profile or {})
    profile["validation_report"] = validation_report
    profile["inferred_schema"] = validation_report.get("inferred_schema", {})
    profile["semantic_columns"] = {}
    for column, meta in profile["inferred_schema"].items():
        profile["semantic_columns"].setdefault(meta["semantic_type"], []).append(column)

    numeric_cols = profile.get("numeric_columns", [])
    if numeric_cols:
        profile["correlations"] = df[numeric_cols].corr(numeric_only=True).round(4).replace({np.nan: None}).to_dict()
        profile["outliers"] = {}
        for column in numeric_cols:
            values = pd.to_numeric(df[column], errors="coerce").dropna()
            if len(values) < 4:
                continue
            q1 = values.quantile(0.25)
            q3 = values.quantile(0.75)
            iqr = q3 - q1
            if iqr == 0 or pd.isna(iqr):
                continue
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            profile["outliers"][column] = {
                "lower_bound": round(float(lower), 4),
                "upper_bound": round(float(upper), 4),
                "count": int(((values < lower) | (values > upper)).sum()),
            }
    return profile


def attach_kpi_explanations(kpis: Dict[str, Any]) -> Dict[str, Any]:
    discovered = kpis.get("discovered_kpis") or {}
    advanced = kpis.get("discovery_metadata", {}).get("advanced_insights", {})
    trends = advanced.get("trends", {}) if isinstance(advanced, dict) else {}

    enriched = {}
    for name, payload in discovered.items():
        item = dict(payload) if isinstance(payload, dict) else {"raw_value": payload, "display_value": payload}
        trend = trends.get(name) or trends.get(str(name).replace(" Total", "").replace(" Sum", "").replace(" Average", ""))
        trend_value = None
        if isinstance(trend, dict) and trend.get("slope_per_day") is not None:
            trend_value = round(float(trend["slope_per_day"]), 4)
        item["trend"] = trend_value if trend_value is not None else 0
        item["trend_direction"] = "up" if (trend_value or 0) > 0 else "down" if (trend_value or 0) < 0 else "flat"
        item["business_explanation"] = f"{name} is calculated directly from uploaded data and tracked for downstream decisions."
        item["confidence_score"] = int(item.get("confidence", 90) or 90)
        enriched[name] = item

    kpis["discovered_kpis"] = enriched
    return kpis


def build_trend_engine_output(df: pd.DataFrame, profile: Dict[str, Any], ctx: PipelineContext) -> Dict[str, Any]:
    numeric_cols = profile.get("numeric_columns", [])[:12]
    date_cols = profile.get("datetime_columns", [])
    output = {"time_based": {}, "comparative": {}, "cards": []}

    if date_cols and numeric_cols:
        time_col = date_cols[0]
        frame = df.copy()
        frame["__time"] = pd.to_datetime(frame[time_col], errors="coerce")
        frame = frame.dropna(subset=["__time"])
        for frequency, label in [("W", "WoW"), ("ME", "MoM"), ("QE", "QoQ"), ("YE", "YoY")]:
            output["time_based"][label] = {}
            for column in numeric_cols[:5]:
                series = frame.set_index("__time")[column].resample(frequency).sum().dropna()
                if len(series) < 2:
                    continue
                current = float(series.iloc[-1])
                previous = float(series.iloc[-2])
                growth = None if previous == 0 else round((current - previous) / abs(previous) * 100, 2)
                output["time_based"][label][column] = {
                    "current": round(current, 4),
                    "previous": round(previous, 4),
                    "growth_percent": growth,
                    "direction": "up" if current > previous else "down" if current < previous else "flat",
                }
                if len(output["cards"]) < 6:
                    output["cards"].append({
                        "label": f"{column} {label}",
                        "value": round(current, 2),
                        "trend": growth if growth is not None else 0,
                        "trend_direction": "up" if current > previous else "down" if current < previous else "flat",
                    })
    elif numeric_cols:
        categorical_cols = profile.get("categorical_columns", [])
        segment_col = categorical_cols[0] if categorical_cols else None
        for column in numeric_cols[:6]:
            if segment_col:
                grouped = df.groupby(segment_col)[column].sum(numeric_only=True).sort_values(ascending=False).head(2)
                if len(grouped) >= 2:
                    current = float(grouped.iloc[0])
                    previous = float(grouped.iloc[1])
                    output["comparative"][column] = {
                        "dimension": segment_col,
                        "leader": str(grouped.index[0]),
                        "runner_up": str(grouped.index[1]),
                        "difference_percent": None if previous == 0 else round((current - previous) / abs(previous) * 100, 2),
                    }
                    output["cards"].append({
                        "label": f"{column} by {segment_col}",
                        "value": round(current, 2),
                        "trend": output["comparative"][column]["difference_percent"] or 0,
                        "trend_direction": "up" if current >= previous else "down",
                    })
            else:
                values = pd.to_numeric(df[column], errors="coerce").dropna()
                if len(values) >= 2:
                    output["cards"].append({
                        "label": f"{column} range",
                        "value": round(float(values.mean()), 2),
                        "trend": round(float(values.max() - values.min()), 2),
                        "trend_direction": "flat",
                    })

    if not output["cards"]:
        output["cards"].append({"label": "Dataset Rows", "value": len(df), "trend": 0, "trend_direction": "flat"})
    log_stage("trend_engine:complete", ctx, cards=len(output["cards"]))
    return output


def build_ai_modes(insights: List[Dict[str, Any]], trend_engine: Dict[str, Any], validation_report: Dict[str, Any]) -> Dict[str, Any]:
    evidence_line = f"{validation_report['row_count']} rows, {validation_report['column_count']} columns, {validation_report['missing_percent']}% missing cells, {validation_report['duplicate_percent']}% duplicate rows"
    top_observations = [item.get("observation") or item.get("detail") or item.get("title") for item in insights[:3]]
    top_observations = [item for item in top_observations if item]
    return {
        "business": {
            "tone": "executive",
            "summary": f"Decision summary: the dataset shows {evidence_line}. Focus on the highest-confidence findings that affect revenue, risk, and operating quality.",
            "bullets": top_observations,
            "recommended_decision": "Prioritize high-confidence KPI and data-quality actions before using the output for executive reporting.",
        },
        "data": {
            "tone": "technical",
            "summary": f"Methodology: schema inference, missingness, duplicate checks, dynamic KPI discovery, trend comparisons, correlations, and anomaly detectors were run on uploaded data. Evidence: {evidence_line}.",
            "trend_cards": trend_engine.get("cards", []),
            "validation": validation_report,
        },
        "eli5": {
            "tone": "simple",
            "summary": f"Think of this file like a spreadsheet box with {validation_report['row_count']} rows. Some spots may be blank, and repeated rows can make totals look bigger than they are.",
            "bullets": [str(item).split(".")[0] for item in top_observations[:3]],
        },
    }


def normalize_recommendations(recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized = []
    for item in recommendations or []:
        rec = dict(item)
        rec["title"] = rec.get("title") or rec.get("action") or "Recommended action"
        rec["detail"] = (
            rec.get("detail")
            or rec.get("recommended_action")
            or rec.get("observation")
            or rec.get("expected_outcome")
            or "Review the supporting evidence before acting."
        )
        rec["impact"] = rec.get("impact") or rec.get("priority") or rec.get("business_impact") or "Medium"
        normalized.append(rec)
    return normalized


def build_evidence_insights(df: pd.DataFrame, advanced_profile: Dict[str, Any], business_kpis: List[Dict[str, Any]], anomalies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    insights: List[Dict[str, Any]] = []
    pareto = advanced_profile.get("pareto_analysis") or {}
    if pareto.get("top_contributors"):
        contributors = pareto["top_contributors"]
        top3_share = pareto.get("top_3_share")
        leader = contributors[0]
        observation = (
            f"Top 3 {pareto['dimension']} values generate {top3_share}% of {pareto['measure']}. "
            f"{leader['value']} alone contributes {leader['share']}%."
        )
        insights.append({
            "title": f"{_humanize(pareto['measure'])} concentration",
            "observation": observation,
            "detail": observation,
            "evidence": contributors,
            "impact": "High concentration can make performance dependent on a narrow segment.",
            "recommendation": f"Monitor the top {pareto['dimension']} contributors separately and grow the long tail to reduce dependency.",
            "confidence": 0.9,
            "icon": "chart",
        })

    for column, concentration in (advanced_profile.get("concentration_metrics") or {}).items():
        if concentration.get("top_3_share", 0) >= 65:
            observation = (
                f"Top 3 values in {_humanize(column)} represent {concentration['top_3_share']}% of records. "
                f"{concentration['top_value']} is the largest group at {concentration['top_share']}%."
            )
            insights.append({
                "title": f"{_humanize(column)} concentration",
                "observation": observation,
                "detail": observation,
                "evidence": [{"column": column, **concentration}],
                "impact": "A concentrated segment can hide smaller but important groups.",
                "recommendation": f"Break reporting for {_humanize(column)} into leader versus long-tail segments.",
                "confidence": 0.84,
                "icon": "chart",
            })

    for column, distribution in (advanced_profile.get("distributions") or {}).items():
        skew = distribution.get("skew", 0)
        if abs(skew) >= 1.25:
            direction = "large values pull averages upward" if skew > 0 else "small values pull averages downward"
            observation = f"{_humanize(column)} is skewed ({skew}), so {direction}."
            insights.append({
                "title": f"{_humanize(column)} skew",
                "observation": observation,
                "detail": observation,
                "evidence": [{"column": column, **distribution}],
                "impact": "Average-based KPIs may be misleading for this metric.",
                "recommendation": f"Use median, percentiles, and segment-level views for {_humanize(column)}.",
                "confidence": 0.78,
                "icon": "analytics",
            })

    for anomaly in anomalies[:5]:
        observation = anomaly.get("explanation")
        if not observation:
            continue
        insights.append({
            "title": f"Anomaly in {_humanize(anomaly.get('column'))}",
            "observation": observation,
            "detail": observation,
            "evidence": [anomaly],
            "impact": anomaly.get("business_impact", "Anomalies can distort totals, averages, and forecasts."),
            "recommendation": f"Inspect source rows for {_humanize(anomaly.get('column'))} before using this metric for decisions.",
            "confidence": 0.76,
            "icon": "alert",
        })

    for kpi in business_kpis[:6]:
        if kpi.get("trend_direction") in {"up", "down"} and kpi.get("trend"):
            direction = "increased" if kpi["trend_direction"] == "up" else "decreased"
            observation = f"{kpi['name']} {direction} by {kpi['trend']} based on the detected comparison period."
            insights.append({
                "title": f"{kpi['name']} movement",
                "observation": observation,
                "detail": observation,
                "evidence": [{"kpi": kpi["name"], "value": kpi["value"], "trend": kpi["trend"]}],
                "impact": "Directional movement can affect revenue, profitability, capacity, or planning.",
                "recommendation": f"Review drivers behind {kpi['name']} movement before setting targets.",
                "confidence": min(0.9, (kpi.get("confidence", 70) / 100)),
                "icon": "trend",
            })

    return insights[:12]


def build_root_causes(anomalies: List[Dict[str, Any]], business_kpis: List[Dict[str, Any]], roles: Dict[str, List[str]]) -> List[Dict[str, Any]]:
    root_causes: List[Dict[str, Any]] = []
    role_names = [role for role, columns in roles.items() if columns]
    for anomaly in anomalies:
        column = anomaly.get("column")
        affected = [kpi["name"] for kpi in business_kpis if column in [ev.get("column") for ev in kpi.get("evidence", [])]]
        possible_causes = []
        if any(role in role_names for role in ["Orders", "Customers"]):
            possible_causes.append("order volume or customer mix changed")
        if any(role in role_names for role in ["Inventory", "Products"]):
            possible_causes.append("product availability or inventory mix changed")
        if any(role in role_names for role in ["Cost", "Profit", "Margins"]):
            possible_causes.append("cost, margin, or pricing pressure changed")
        if not possible_causes:
            possible_causes.append("source data, outlier rows, or upstream transformation changed")
        root_causes.append({
            "what_happened": anomaly.get("explanation"),
            "possible_causes": possible_causes,
            "affected_metrics": affected or [column],
            "severity": anomaly.get("severity", "medium"),
            "confidence": 72 if anomaly.get("severity") == "high" else 62,
            "supporting_evidence": anomaly,
        })
    return root_causes


def enrich_anomalies_for_business(
    anomalies: List[Dict[str, Any]],
    df: pd.DataFrame,
    roles: Dict[str, List[str]],
) -> List[Dict[str, Any]]:
    """Add business-language anomaly fields without removing detector metadata."""
    measure = choose_measure(df, roles)
    dimension = choose_dimension(df, roles)
    date_cols = df.select_dtypes(include=["datetime", "datetimetz"]).columns.tolist()
    if not date_cols:
        date_cols = [
            col for col in df.columns
            if any(token in str(col).lower() for token in ["date", "time", "created", "month", "day"])
        ]

    enriched: List[Dict[str, Any]] = []
    seen_events = set()
    for anomaly in anomalies or []:
        item = dict(anomaly)
        contributors = item.get("contributing_features") or []
        focus_col = item.get("column") or (contributors[0] if contributors else measure) or "business metric"
        focus = _humanize(focus_col)
        confidence = int(item.get("confidence_score") or item.get("confidence") or 70)
        severity = str(item.get("severity") or ("high" if confidence >= 85 else "medium")).lower()
        percent = item.get("anomaly_percent")
        count = item.get("anomaly_count")

        headline = f"{focus} Needs Immediate Attention"
        explanation = f"{focus} changed enough to affect planning, margin, or customer commitments."
        possible_cause = "One-off transactions, stock availability, pricing changes, channel mix, or source-data entry issues."
        action = f"Check the highest-impact {focus} rows, compare them by segment, and confirm whether they reflect a real business event."
        impact = "High" if severity == "high" else "Medium"

        if dimension and measure and dimension in df.columns and measure in df.columns:
            try:
                grouped = df.groupby(dimension)[measure].sum(numeric_only=True).sort_values(ascending=False)
                if len(grouped) >= 2:
                    leader = str(grouped.index[0])
                    runner_up = float(grouped.iloc[1])
                    leader_value = float(grouped.iloc[0])
                    lift = None if runner_up == 0 else round((leader_value - runner_up) / abs(runner_up) * 100, 1)
                    if lift is not None and abs(lift) >= 25:
                        headline = f"{_humanize(measure)} Is Unusually Concentrated in {leader}"
                        explanation = f"{leader} is materially ahead of the next {dimension} segment for {_humanize(measure)}."
                        possible_cause = "A successful promotion, bulk order, local demand shift, or uneven stock allocation."
                        action = f"Validate {leader} demand, secure supply, and test whether the same play can grow the next-best segments."
            except Exception:
                pass

        if date_cols and measure and measure in df.columns:
            try:
                frame = df.copy()
                frame["__time"] = pd.to_datetime(frame[date_cols[0]], errors="coerce")
                daily = frame.dropna(subset=["__time"]).set_index("__time")[measure].resample("D").sum().dropna()
                if len(daily) >= 8:
                    recent = float(daily.tail(7).mean())
                    previous = float(daily.iloc[-14:-7].mean()) if len(daily) >= 14 else float(daily.iloc[:-7].mean())
                    change = None if previous == 0 else round((recent - previous) / abs(previous) * 100, 1)
                    if change is not None and abs(change) >= 20:
                        direction = "jumped" if change > 0 else "dropped"
                        headline = f"{_humanize(measure)} {direction.title()} {abs(change)}% Recently"
                        explanation = f"The latest period is {abs(change)}% {'higher' if change > 0 else 'lower'} than the earlier baseline."
                        possible_cause = "Demand shift, campaign timing, stock movement, pricing change, holiday effect, or delayed data capture."
                        action = "Compare the affected dates with promotions, inventory, staffing, and source-system logs before planning the next period."
                        impact = "High" if abs(change) >= 35 else "Medium"
            except Exception:
                pass

        existing_action = str(item.get("recommended_action") or "")
        business_action = action if any(word in existing_action.lower() for word in ["review", "monitor", "track", "consider", "validate"]) else (existing_action or action)
        event_key = re.sub(r"\W+", " ", f"{headline} {focus_col}").strip().lower()
        if event_key in seen_events:
            continue
        seen_events.add(event_key)

        item.update({
            "headline": item.get("headline") or headline,
            "business_headline": item.get("business_headline") or headline,
            "business_explanation": item.get("business_explanation") if item.get("business_headline") else explanation,
            "possible_cause": item.get("possible_cause") or possible_cause,
            "business_impact": item.get("business_impact") or impact,
            "severity": item.get("severity") or severity,
            "estimated_loss": item.get("estimated_loss") or ("Medium exposure" if impact == "High" else "Low to medium exposure"),
            "estimated_opportunity": item.get("estimated_opportunity") or ("Recover lost revenue or protect margin leakage" if impact == "High" else "Improve planning confidence"),
            "timeline": item.get("timeline") or "Next 7 days",
            "recommended_action": business_action,
            "suggested_action": business_action,
            "ai_confidence": item.get("ai_confidence") or {
                "label": "High" if confidence >= 80 else "Medium" if confidence >= 60 else "Low",
                "percent": confidence,
            },
            "evidence": item.get("evidence") or [
                {"metric": focus_col, "unusual_records": count, "dataset_share_percent": percent}
            ],
        })
        enriched.append(item)
    return enriched


def build_prioritized_recommendations(insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    recommendations: List[Dict[str, Any]] = []
    impact_rank = {"High": 3, "Medium": 2, "Low": 1}
    for insight in insights:
        evidence = insight.get("evidence") or []
        impact_text = insight.get("impact") or "Medium"
        expected_impact = "High" if any(str(value).lower().startswith("high") for value in [impact_text]) else "Medium"
        confidence = int(round(float(insight.get("confidence", 0.65)) * 100))
        finding = insight.get("observation") or insight.get("detail") or insight.get("title", "A business signal changed in the uploaded dataset.")
        metric = insight.get("title") or "Business performance"
        evidence_columns = [
            str(item.get("column") or item.get("kpi") or item.get("feature"))
            for item in evidence
            if isinstance(item, dict) and (item.get("column") or item.get("kpi") or item.get("feature"))
        ]
        focus = _humanize(evidence_columns[0] if evidence_columns else metric)
        lower_finding = str(finding).lower()
        if any(word in lower_finding for word in ["drop", "declin", "risk", "anomal", "missing", "duplicate"]):
            action = f"Assign an owner to fix the {focus} issue this week, validate the affected rows, and protect the highest-value segment before the next reporting cycle."
            risk_reduction = "High"
            revenue_improvement = "Medium"
        elif any(word in lower_finding for word in ["concentration", "top 3", "largest", "dependency"]):
            action = f"Reduce dependence on {focus} by creating two growth plays for the next-best segments and shifting promotion, inventory, or sales effort toward them."
            risk_reduction = "High"
            revenue_improvement = "Medium"
        elif any(word in lower_finding for word in ["growth", "increased", "momentum", "opportunity"]):
            action = f"Double down on {focus}: allocate more stock, sales attention, or campaign budget to the segment driving the improvement, then measure lift over the next period."
            risk_reduction = "Medium"
            revenue_improvement = "High"
        else:
            action = f"Turn the {focus} signal into an operating move: segment the affected rows, prioritize the largest business driver, and launch one targeted action in the next planning cycle."
            risk_reduction = "Medium"
            revenue_improvement = "Medium"

        why = insight.get("impact") or f"This matters because {focus} can influence revenue, margin, customer demand, or operating reliability."
        title = f"Act on {_humanize(metric)}"
        confidence_label = "High" if confidence >= 80 else "Medium" if confidence >= 60 else "Low"
        recommendations.append({
            "title": title,
            "business_finding": finding,
            "why_it_matters": why,
            "business_impact": why,
            "evidence_summary": f"Based on {len(evidence)} supporting evidence point{'s' if len(evidence) != 1 else ''} from the current dataset.",
            "recommended_action": action,
            "detail": action,
            "expected_business_impact": {
                "revenue_increase": revenue_improvement,
                "profit_increase": "Medium" if revenue_improvement == "High" else "Low",
                "cost_reduction": "Low",
                "risk_reduction": risk_reduction,
                "implementation_time": "7-14 days" if expected_impact == "High" else "2-4 weeks",
                "difficulty": "Medium",
                "roi": "High" if expected_impact == "High" and confidence >= 75 else "Medium",
            },
            "estimated_revenue_increase": revenue_improvement,
            "estimated_profit_increase": "Medium" if revenue_improvement == "High" else "Low",
            "estimated_cost_reduction": "Low",
            "implementation_time": "7-14 days" if expected_impact == "High" else "2-4 weeks",
            "implementation_difficulty": "Medium",
            "roi": "High" if expected_impact == "High" and confidence >= 75 else "Medium",
            "ai_confidence": {"label": confidence_label, "percent": confidence},
            "expected_impact": expected_impact,
            "impact": expected_impact,
            "confidence": confidence,
            "supporting_evidence": evidence,
            "evidence": evidence,
            "reason": finding,
            "risk_if_ignored": "The same pattern may keep affecting revenue, profit, or planning confidence if no owner acts on it.",
        })

    recommendations.sort(key=lambda rec: (impact_rank.get(rec["expected_impact"], 1), rec["confidence"]), reverse=True)
    return recommendations[:8]


def enrich_kpis_for_business(
    business_kpis: List[Dict[str, Any]],
    forecasts: List[Dict[str, Any]],
    trend_engine: Dict[str, Any],
    explanations: Dict[str, Any],
) -> List[Dict[str, Any]]:
    forecast_by_column = {
        str(item.get("column")): item
        for item in forecasts
        if isinstance(item, dict) and item.get("column")
    }
    trend_cards = trend_engine.get("cards", []) if isinstance(trend_engine, dict) else []
    top_features = explanations.get("contributing_features", []) if isinstance(explanations, dict) else []
    enriched: List[Dict[str, Any]] = []

    for kpi in business_kpis:
        item = dict(kpi)
        source_columns = item.get("source_columns") or item.get("contributing_features") or []
        source = str(source_columns[0]) if source_columns else str(item.get("name", "metric"))
        forecast = forecast_by_column.get(source)
        trend_card = next((card for card in trend_cards if source in str(card.get("label", ""))), None)
        trend = item.get("trend", 0) or (trend_card or {}).get("trend", 0) or (forecast or {}).get("change_percent", 0) or 0
        trend_direction = "up" if trend > 0 else "down" if trend < 0 else "flat"
        previous = (trend_card or {}).get("previous")
        current = item.get("value")
        forecast_value = (forecast or {}).get("predicted_value")
        confidence = int(item.get("confidence", (forecast or {}).get("confidence_score", 70)))
        label = "High" if confidence >= 80 else "Medium" if confidence >= 60 else "Low"
        is_good = trend_direction == "up" if item.get("aggregation") != "nunique" else True

        if forecast and forecast.get("change_percent") is not None:
            action = (
                f"Prepare capacity for {_humanize(source)} growth and protect service levels in the next {forecast.get('horizon_periods', 30)} periods."
                if forecast["change_percent"] >= 0
                else f"Investigate the drivers behind the expected {_humanize(source)} decline and run a targeted recovery action before the next planning period."
            )
            impact = f"Forecast points to {forecast['change_percent']}% movement, so acting early can protect revenue, margin, or operating capacity."
        elif trend_direction == "down":
            action = f"Launch a focused recovery plan for {_humanize(source)}: identify the weakest segment, fix availability or pricing issues, and recheck performance next period."
            impact = f"{_humanize(source)} is moving down, which can reduce business momentum if not corrected."
        elif trend_direction == "up":
            action = f"Scale the driver behind {_humanize(source)} by expanding supply, sales focus, or campaign spend in the strongest segment."
            impact = f"{_humanize(source)} is moving up, creating a chance to capture more growth while demand is favorable."
        else:
            action = f"Use {_humanize(source)} as a decision metric: compare it across segments and move resources to the highest-return area."
            impact = f"{_humanize(source)} is stable enough to use as a planning signal."

        item.update({
            "current_value": current,
            "trend": round(float(trend), 2) if isinstance(trend, (int, float)) else 0,
            "trend_direction": trend_direction,
            "previous_period_comparison": previous,
            "forecast": forecast_value,
            "business_impact": impact,
            "confidence": confidence,
            "ai_confidence": {"label": label, "percent": confidence},
            "is_good": is_good,
            "should_act": bool(forecast or trend_direction != "flat"),
            "recommended_action": action,
            "positive_drivers": [feature for feature in top_features[:3] if feature != source],
            "negative_drivers": [],
        })
        enriched.append(item)
    return enriched


def build_executive_outputs(
    insights: List[Dict[str, Any]],
    recommendations: List[Dict[str, Any]],
    forecasts: List[Dict[str, Any]],
    anomalies: List[Dict[str, Any]],
    business_kpis: List[Dict[str, Any]],
    domain: Dict[str, Any],
    validation_report: Dict[str, Any],
) -> Dict[str, Any]:
    top_kpis = ", ".join([f"{item.get('name')}: {item.get('value')}" for item in business_kpis[:4]]) or "no KPI candidates detected"
    domain_name = str(domain.get("domain", "generic")).title()
    risks = []
    opportunities = []

    if validation_report.get("missing_percent", 0) > 5:
        risks.append({
            "title": "Data completeness risk",
            "detail": f"{validation_report.get('missing_percent')}% of cells are missing, which can weaken KPI confidence.",
            "recommended_action": "Prioritize filling high-impact business fields before executive reporting.",
        })
    for anomaly in anomalies[:3]:
        risks.append({
            "title": anomaly.get("type", "Anomaly risk"),
            "detail": anomaly.get("business_explanation") or anomaly.get("business_impact") or anomaly.get("reasoning"),
            "recommended_action": anomaly.get("recommended_action", "Review anomaly evidence before decisions."),
        })
    for forecast in forecasts[:3]:
        change = forecast.get("change_percent")
        if change is not None:
            opportunities.append({
                "title": f"{_humanize(forecast.get('column'))} forecast movement",
                "detail": f"Forecasted movement is {change}% over the model horizon.",
                "recommended_action": forecast.get("recommended_action"),
            })
    for insight in insights[:3]:
        opportunities.append({
            "title": insight.get("title", "Business opportunity"),
            "detail": insight.get("observation") or insight.get("detail"),
            "recommended_action": insight.get("recommendation", "Turn this insight into a focused business review."),
        })

    high_risks = len([item for item in risks if "risk" in str(item.get("title", "")).lower() or "missing" in str(item.get("detail", "")).lower()])
    action_count = len(recommendations[:3])
    health_score = max(
        35,
        min(
            95,
            int(100 - validation_report.get("missing_percent", 0) - validation_report.get("duplicate_percent", 0) - len(anomalies[:5]) * 3),
        ),
    )
    current_trend = "Improving" if any((kpi.get("trend") or 0) > 0 for kpi in business_kpis[:5]) else "Needs attention" if anomalies or high_risks else "Stable"
    top_opportunity = (opportunities[0]["title"] if opportunities else (recommendations[0].get("title") if recommendations else "Build more history for stronger growth signals"))
    top_risk = (risks[0]["title"] if risks else "No major risk detected in the current analysis")

    ceo_takeaway = (
        f"CEO takeaway: focus the next operating cycle on {top_opportunity.lower()} while keeping {top_risk.lower()} under control."
    )
    executive_summary = (
        f"The business is in a {('strong' if health_score >= 80 else 'recoverable' if health_score >= 60 else 'fragile')} position. "
        f"The clearest upside is {top_opportunity.lower()}, while the main management risk is {top_risk.lower()}. "
        f"Leadership should execute the top {max(action_count, 1)} priorities first and use the remaining analysis as supporting evidence, not a second agenda. "
        f"{ceo_takeaway}"
    )

    return {
        "executive_summary": executive_summary,
        "executive_dashboard": {
            "business_health": "Strong" if health_score >= 80 else "Watchlist" if health_score >= 60 else "At Risk",
            "overall_score": health_score,
            "current_trend": current_trend,
            "top_opportunity": top_opportunity,
            "top_risk": top_risk,
            "expected_revenue_growth": "High" if any((rec.get("estimated_revenue_increase") == "High") for rec in recommendations[:3]) else "Medium",
            "overall_ai_confidence": "High" if health_score >= 75 else "Medium",
            "ceo_takeaway": ceo_takeaway,
            "immediate_actions": [
                rec.get("recommended_action") or rec.get("title")
                for rec in recommendations[:3]
                if rec.get("recommended_action") or rec.get("title")
            ][:3],
            "action_count": action_count,
        },
        "risks": risks[:6],
        "opportunities": opportunities[:6],
        "business_advice": [
            item.get("title") or item.get("recommended_action")
            for item in recommendations[:5]
            if item.get("title") or item.get("recommended_action")
        ],
    }


def build_distinct_modes(
    insights: List[Dict[str, Any]],
    business_kpis: List[Dict[str, Any]],
    advanced_profile: Dict[str, Any],
    root_causes: List[Dict[str, Any]],
    validation_report: Dict[str, Any],
) -> Dict[str, Any]:
    top_insight = insights[0]["observation"] if insights else f"Dataset contains {validation_report['row_count']} rows and {validation_report['column_count']} columns."
    top_kpis = ", ".join([f"{kpi['name']}: {kpi['value']}" for kpi in business_kpis[:4]]) or "No business KPI detected"
    return {
        "business": {
            "tone": "executive",
            "summary": f"{top_insight} KPI focus: {top_kpis}. Prioritize actions that improve growth, profitability, and risk control.",
            "focus": ["ROI", "profitability", "growth", "risk"],
            "insights": [item["observation"] for item in insights[:5]],
            "recommendations": [item.get("recommendation") for item in insights[:5] if item.get("recommendation")],
        },
        "data": {
            "tone": "technical",
            "summary": "Analysis used schema inference, missingness checks, duplicate detection, distributions, correlations, Pareto concentration, trend comparisons, and anomaly rules.",
            "statistics": {
                "dataset": {
                    "rows": validation_report["row_count"],
                    "columns": validation_report["column_count"],
                    "missing_percent": validation_report["missing_percent"],
                    "duplicate_percent": validation_report["duplicate_percent"],
                },
                "distributions": advanced_profile.get("distributions", {}),
                "correlations": advanced_profile.get("correlations", {}),
                "root_causes": root_causes,
            },
        },
        "eli5": {
            "tone": "simple",
            "summary": f"Think of the data like a shop notebook. The biggest clue is: {top_insight}",
            "examples": [f"{kpi['name']} is like a scorecard number: {kpi['value']}." for kpi in business_kpis[:3]],
            "no_jargon": True,
        },
    }


def sanitize_for_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): sanitize_for_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize_for_json(item) for item in value]
    if isinstance(value, tuple):
        return [sanitize_for_json(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        if np.isnan(value) or np.isinf(value):
            return None
        return float(value)
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    if not isinstance(value, (str, bytes)):
        try:
            if pd.isna(value):
                return None
        except Exception:
            pass
    return value


def run_analysis(df: pd.DataFrame, ctx: PipelineContext, validation_report: Optional[Dict[str, Any]] = None, language: str = "en") -> Dict[str, Any]:
    language = normalize_language(language)
    analysis_df = df if len(df) <= MAX_PROFILE_ROWS else df.sample(MAX_PROFILE_ROWS, random_state=42)
    chart_df = df if len(df) <= MAX_CHART_ROWS else df.sample(MAX_CHART_ROWS, random_state=42)

    stages: Dict[str, Any] = {}
    profile: Dict[str, Any] = {}
    kpis: Dict[str, Any] = {}
    insights: List[Dict[str, Any]] = []
    recommendations: List[Dict[str, Any]] = []

    for stage, fn in [
        ("profile", lambda: profile_data(analysis_df)),
        ("kpis", lambda: generate_kpis(analysis_df)),
    ]:
        try:
            stages[stage] = "ok"
            if stage == "profile":
                profile = fn()
            else:
                kpis = fn()
        except Exception as exc:
            stages[stage] = f"failed: {exc}"
            log_exception(stage, ctx, exc)

    if not profile:
        profile = {"shape": {"rows": len(df), "columns": len(df.columns)}, "numeric_columns": [], "categorical_columns": [], "datetime_columns": []}
    if not kpis:
        kpis = {"discovered_kpis": {}, "validation": {"ok": False, "errors": ["KPI generation failed"]}}

    validation_report = validation_report or build_validation_report(df, {})
    profile = enrich_profile(analysis_df, profile, validation_report)
    dataset_profile = detect_dataset_profile(df, validation_report)
    ml_dataset_profile = inspect_dataset(analysis_df)
    dataset_profile.update(ml_dataset_profile)
    roles = find_role_columns(analysis_df)
    domain = classify_domain(analysis_df, ml_dataset_profile)

    try:
        feature_frame, feature_metadata = engineer_features(analysis_df, ml_dataset_profile)
        feature_store = build_feature_store_metadata(feature_metadata)
        stages["feature_engineering"] = "ok"
    except Exception as exc:
        log_exception("feature_engineering", ctx, exc)
        feature_frame = analysis_df
        feature_metadata = {"created_features": [], "error": str(exc)}
        feature_store = {"status": "unavailable", "feature_count": 0, "features": []}

    advanced = kpis.setdefault("discovery_metadata", {}).setdefault("advanced_insights", {})
    try:
        advanced["trends"] = detect_trends(analysis_df, kpis.get("profile", {}))
        advanced["correlations"] = top_correlations(analysis_df, numeric_cols=profile.get("numeric_columns", []), top_n=10, threshold=0.35)
        rule_anomalies = detect_anomalies(analysis_df, numeric_cols=profile.get("numeric_columns", []))
        ml_anomalies = detect_ml_anomalies(feature_frame, ml_dataset_profile)
        advanced["anomalies"] = rule_anomalies
        advanced["ml_anomalies"] = ml_anomalies
        stages["advanced"] = "ok"
    except Exception as exc:
        stages["advanced"] = f"failed: {exc}"
        log_exception("advanced_signals", ctx, exc)

    kpis = attach_kpi_explanations(kpis)
    trend_engine = build_trend_engine_output(analysis_df, profile, ctx)
    anomaly_engine = advanced.get("ml_anomalies", []) or advanced.get("anomalies", [])
    anomaly_engine = enrich_anomalies_for_business(anomaly_engine, analysis_df, roles)
    business_kpis = discover_dynamic_kpis(analysis_df, ml_dataset_profile)
    advanced_profile = build_advanced_profile(analysis_df, profile, roles)
    dataset_health = assess_dataset_health(analysis_df, ml_dataset_profile)
    segmentation = segment_records(feature_frame, ml_dataset_profile)
    explanations = explain_predictions(feature_frame, ml_dataset_profile)

    try:
        charts = generate_visualizations(chart_df)
    except Exception as exc:
        log_exception("visualizations", ctx, exc)
        charts = []
    try:
        forecasts = generate_ml_forecasts(analysis_df, ml_dataset_profile)
        if not forecasts:
            forecasts = generate_forecast_chart(analysis_df)
    except Exception as exc:
        log_exception("forecasts", ctx, exc)
        forecasts = []
    business_kpis = enrich_kpis_for_business(business_kpis, forecasts, trend_engine, explanations)
    try:
        insights = generate_insights(profile, kpis, analysis_df)
    except Exception as exc:
        log_exception("insights", ctx, exc)
        insights = []
    evidence_insights = build_evidence_insights(analysis_df, advanced_profile, business_kpis, anomaly_engine)
    if evidence_insights:
        insights = evidence_insights
    try:
        recommendations = generate_recommendations(profile, insights, analysis_df)
    except Exception as exc:
        log_exception("recommendations", ctx, exc)
        recommendations = []
    prioritized_recommendations = build_prioritized_recommendations(insights)
    recommendations = prioritized_recommendations or normalize_recommendations(recommendations)
    root_causes = build_root_causes(anomaly_engine, business_kpis, roles)
    executive_outputs = build_executive_outputs(
        insights,
        recommendations,
        forecasts,
        anomaly_engine,
        business_kpis,
        domain,
        validation_report,
    )

    data_quality = {
        "missing_values": profile.get("missing_values", {}),
        "missing_percent": profile.get("missing_percent", {}),
        "duplicate_rows": profile.get("duplicate_rows", 0),
        "duplicate_percent": profile.get("duplicate_percent", 0),
        "health_engine": dataset_health,
    }

    models_used = sorted({
        *(forecast.get("model") for forecast in forecasts if isinstance(forecast, dict) and forecast.get("model")),
        *(anomaly.get("model") for anomaly in anomaly_engine if isinstance(anomaly, dict) and anomaly.get("model")),
        segmentation.get("model") if isinstance(segmentation, dict) and segmentation.get("segments") else None,
        explanations.get("method") if isinstance(explanations, dict) and explanations.get("available") else None,
    } - {None})

    analysis = {
        "profile": profile,
        "dataset_profile": dataset_profile,
        "domain_detection": domain,
        "feature_engineering": feature_metadata,
        "feature_store": feature_store,
        "models_used": models_used,
        "analysis_status": "complete",
        "kpis": kpis,
        "business_kpis": business_kpis,
        "charts": charts,
        "forecasts": forecasts,
        "insights": insights,
        "recommendations": recommendations,
        "executive_summary": executive_outputs["executive_summary"],
        "executive_dashboard": executive_outputs["executive_dashboard"],
        "risks": executive_outputs["risks"],
        "opportunities": executive_outputs["opportunities"],
        "business_advice": executive_outputs["business_advice"],
        "data_quality": data_quality,
        "dataset_health": dataset_health,
        "validation_report": validation_report,
        "advanced_profile": advanced_profile,
        "trend_engine": trend_engine,
        "anomaly_engine": anomaly_engine,
        "segmentation_engine": segmentation,
        "explanation_engine": explanations,
        "root_cause_engine": root_causes,
        "ai_modes": build_distinct_modes(insights, business_kpis, advanced_profile, root_causes, validation_report),
        "ai_prompt_context": language_prompt_context(language, mode="analysis", tone="executive"),
        "qa_checks": validate_analysis_payload(kpis, insights, recommendations, trend_engine, validation_report),
        "pipeline_stages": stages,
    }
    return sanitize_for_json(localize_analysis_payload(analysis, language))


def validate_analysis_payload(
    kpis: Dict[str, Any],
    insights: List[Dict[str, Any]],
    recommendations: List[Dict[str, Any]],
    trend_engine: Dict[str, Any],
    validation_report: Dict[str, Any],
) -> Dict[str, Any]:
    checks = []
    discovered = kpis.get("discovered_kpis", {})
    checks.append({"name": "kpi_non_empty", "passed": bool(discovered), "detail": f"{len(discovered)} discovered KPIs"})
    checks.append({"name": "kpi_values_not_null", "passed": all(v.get("display_value") is not None for v in discovered.values() if isinstance(v, dict)), "detail": "All discovered KPI cards have display values."})
    checks.append({"name": "insights_grounded", "passed": all(item.get("evidence") for item in insights[:8]) if insights else False, "detail": "Insights include evidence objects."})
    checks.append({"name": "recommendations_grounded", "passed": all(item.get("evidence") or item.get("observation") for item in recommendations[:8]) if recommendations else True, "detail": "Recommendations are derived from insights."})
    checks.append({"name": "trend_cards_present", "passed": bool(trend_engine.get("cards")), "detail": f"{len(trend_engine.get('cards', []))} trend cards"})
    checks.append({"name": "dataset_integrity", "passed": validation_report.get("row_count", 0) > 0 and validation_report.get("column_count", 0) > 0, "detail": "Dataset has rows and columns."})
    return {"passed": all(check["passed"] for check in checks), "checks": checks}
