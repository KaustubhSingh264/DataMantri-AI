from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd


def detect_trends(df: pd.DataFrame, profile: Dict[str, Any], time_col: Optional[str] = None, numeric_cols: Optional[List[str]] = None) -> Dict[str, Any]:
    """Detect simple linear trends for numeric columns. Returns mapping col -> {slope_per_day, r2, confidence}

    This is intentionally lightweight — good enough for Phase B skeleton and safe for production.
    """
    out: Dict[str, Any] = {}
    if numeric_cols is None:
        numeric_cols = [c for c, p in profile.get("columns", {}).items() if p.get("is_numeric") and not p.get("is_id")]

    # choose time column heuristically if not provided
    if time_col is None:
        for cname, meta in profile.get("columns", {}).items():
            if meta.get("is_date"):
                time_col = cname
                break

    if time_col is None or time_col not in df.columns:
        return {"note": "no_time_column_found"}

    try:
        ts = pd.to_datetime(df[time_col], errors="coerce")
    except Exception:
        return {"note": "time_parse_failed"}

    df_ts = df.copy()
    df_ts["_time"] = ts
    df_ts = df_ts.dropna(subset=["_time"]).copy()
    if df_ts.empty:
        return {"note": "no_valid_time_points"}

    df_ts["_time_ordinal"] = df_ts["_time"].astype("int64") // 10 ** 9

    for col in numeric_cols:
        try:
            series = df_ts[["_time_ordinal", col]].dropna()
            if len(series) < 4:
                out[col] = {"note": "insufficient_points", "confidence": 50}
                continue
            x = series["_time_ordinal"].values.astype(float)
            y = pd.to_numeric(series[col], errors="coerce").values.astype(float)
            # linear fit
            a, b = np.polyfit(x, y, 1)
            # slope per day
            slope_per_day = float(a * 86400)
            # compute R^2
            yhat = a * x + b
            ss_res = float(((y - yhat) ** 2).sum())
            ss_tot = float(((y - y.mean()) ** 2).sum()) if len(y) > 1 else 0.0
            r2 = 0.0 if ss_tot == 0 else max(0.0, 1.0 - ss_res / ss_tot)
            out[col] = {"slope_per_day": slope_per_day, "r2": round(r2, 4), "confidence": 80 + int(r2 * 20)}
        except Exception:
            out[col] = {"note": "trend_error", "confidence": 20}

    return out
