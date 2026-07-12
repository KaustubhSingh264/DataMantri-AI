from typing import Dict, Any
import pandas as pd


def _as_atomic(kpi_obj: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure the KPI object is atomic (raw_value/display_value as scalars).
    If input is already atomic, return as-is. Otherwise return a safe placeholder.
    """
    if not isinstance(kpi_obj, dict):
        return {"raw_value": kpi_obj, "display_value": kpi_obj, "formula": "", "confidence": 100}
    # prefer provided scalar fields
    raw = kpi_obj.get("raw_value") if "raw_value" in kpi_obj else kpi_obj.get("rawValue")
    disp = kpi_obj.get("display_value") if "display_value" in kpi_obj else kpi_obj.get("displayValue")
    # fallback to raw if display missing
    if disp is None and raw is not None:
        disp = raw
    # final fallback
    if raw is None and disp is None:
        return {"raw_value": None, "display_value": None, "formula": kpi_obj.get("formula", ""), "confidence": kpi_obj.get("confidence", 0)}
    return {"raw_value": raw, "display_value": disp, "formula": kpi_obj.get("formula", ""), "confidence": kpi_obj.get("confidence", 100)}


def discover_kpis(df: pd.DataFrame, profile: Dict[str, Any], kpis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Produce a flat mapping `discovered_kpis` and a small metadata object.

    Rules:
    - Reuse existing atomic KPI objects when available (avoid recomputation).
    - Only include scalar/displayable KPI objects (no nested dicts as display_value/raw_value).
    """
    discovered: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {"priority": [], "domain": None, "charts_suggested": [], "correlations": [], "anomalies": []}

    # Basic business KPIs: row/column counts
    try:
        total_rows = int(len(df))
    except Exception:
        total_rows = None
    try:
        total_cols = int(len(df.columns))
    except Exception:
        total_cols = None

    if total_rows is not None:
        discovered["Row Count"] = {"raw_value": total_rows, "display_value": total_rows, "formula": "len(df)", "confidence": 100}
    if total_cols is not None:
        discovered["Column Count"] = {"raw_value": total_cols, "display_value": total_cols, "formula": "len(df.columns)", "confidence": 100}

    # Data health / missing / duplicate
    try:
        if "data_health" in kpis and isinstance(kpis["data_health"], dict):
            dh = kpis["data_health"].get("health_score")
            if dh:
                discovered["Data Health Score"] = _as_atomic(dh)
    except Exception:
        pass

    try:
        if "missing_metrics" in kpis:
            mp = kpis["missing_metrics"].get("missing_percentage")
            if mp:
                discovered["Missing %"] = _as_atomic(mp)
    except Exception:
        pass

    try:
        if "duplicate_metrics" in kpis:
            dp = kpis["duplicate_metrics"].get("duplicate_percentage")
            if dp:
                discovered["Duplicate %"] = _as_atomic(dp)
    except Exception:
        pass

    # Numeric business-like columns: look for obvious names
    numeric_stats = kpis.get("numeric_stats", {}) or {}
    name_keywords = ["revenue", "sales", "amount", "price", "total", "income", "order", "quantity"]
    for col, stats in numeric_stats.items():
        lc = col.lower()
        is_business = any(k in lc for k in name_keywords)
        # always include basic numeric KPIs but label them clearly
        try:
            s_sum = stats.get("sum")
            s_mean = stats.get("mean")
            if s_sum:
                label_sum = f"{col} Total" if is_business else f"{col} Sum"
                discovered[label_sum] = _as_atomic(s_sum)
            if s_mean:
                label_avg = f"{col} Average"
                discovered[label_avg] = _as_atomic(s_mean)
        except Exception:
            continue

    # Categorical top values
    cat_stats = kpis.get("categorical_stats", {}) or {}
    for col, stats in cat_stats.items():
        try:
            top = stats.get("top_category")
            top_pct = stats.get("top_category_percentage")
            if top:
                discovered[f"Top {col}"] = _as_atomic(top)
            if top_pct:
                discovered[f"Top {col} %"] = _as_atomic(top_pct)
        except Exception:
            continue

    # Trends (if available) -> surface simplified trend KPIs
    trends = kpis.get("trends", {}) or {}
    # trends may contain note or per-column slope dicts
    for key, val in trends.items():
        if key == "note":
            continue
        if isinstance(val, dict) and val.get("slope_per_day") is not None:
            discovered[f"{key} Trend (slope/day)"] = {"raw_value": val.get("slope_per_day"), "display_value": round(val.get("slope_per_day"), 4) if isinstance(val.get("slope_per_day"), (int, float)) else val.get("slope_per_day"), "formula": val.get("formula", ""), "confidence": val.get("confidence", 100)}

    # Domain info placeholder (frontend can use this to prioritize)
    try:
        from app.services.domain_inference import infer_domain

        domain_info = infer_domain(profile, df)
        metadata["domain"] = domain_info
    except Exception:
        metadata["domain"] = {"domain": "generic", "scores": {}}

    # Suggest simple charts based on discovered columns
    try:
        charts = []
        # histogram for first numeric
        if numeric_stats:
            first_num = next(iter(numeric_stats.keys()))
            charts.append({"type": "histogram", "column": first_num})
        if cat_stats:
            first_cat = next(iter(cat_stats.keys()))
            charts.append({"type": "bar", "column": first_cat})
        metadata["charts_suggested"] = charts
    except Exception:
        metadata["charts_suggested"] = []

    metadata["priority"] = list(discovered.keys())[:20]

    return {"discovered_kpis": discovered, "metadata": metadata}
