from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np


def detect_anomalies(df: pd.DataFrame, numeric_cols: Optional[List[str]] = None, z_threshold: float = 3.0) -> List[Dict[str, Any]]:
    """Detect z-score, IQR, sudden spike, and sudden drop anomalies."""
    if numeric_cols is None:
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    out: List[Dict[str, Any]] = []
    nrows = len(df)
    if nrows == 0:
        return out

    for col in numeric_cols:
        try:
            vals = pd.to_numeric(df[col], errors="coerce").dropna()
            if vals.empty or len(vals) < 4:
                continue
            mean = float(vals.mean())
            std = float(vals.std())
            detected_indexes = set()
            methods = []

            if std and not np.isnan(std):
                z = (vals - mean) / std
                z_anomalies = z[abs(z) >= z_threshold]
                detected_indexes.update(z_anomalies.index.tolist())
                if len(z_anomalies):
                    methods.append("z_score")

            q1 = vals.quantile(0.25)
            q3 = vals.quantile(0.75)
            iqr = q3 - q1
            if iqr and not np.isnan(iqr):
                iqr_mask = (vals < q1 - 1.5 * iqr) | (vals > q3 + 1.5 * iqr)
                iqr_indexes = vals[iqr_mask].index.tolist()
                detected_indexes.update(iqr_indexes)
                if iqr_indexes:
                    methods.append("iqr")

            pct_change = vals.pct_change().replace([np.inf, -np.inf], np.nan).dropna()
            spike_indexes = pct_change[pct_change >= 1.0].index.tolist()
            drop_indexes = pct_change[pct_change <= -0.5].index.tolist()
            detected_indexes.update(spike_indexes)
            detected_indexes.update(drop_indexes)
            if spike_indexes:
                methods.append("sudden_spike")
            if drop_indexes:
                methods.append("sudden_drop")

            count = int(len(detected_indexes))
            if count == 0:
                continue
            percent = round(100.0 * count / max(1, nrows), 4)
            severity = "high" if percent >= 5 or count >= 25 else "medium" if percent >= 1 else "low"
            sample = vals.loc[list(detected_indexes)[:5]].to_dict()
            anomaly_type = ", ".join(sorted(set(methods)))
            out.append({
                "column": col,
                "type": anomaly_type,
                "severity": severity,
                "anomaly_count": count,
                "anomaly_percent": percent,
                "sample_values": sample,
                "confidence_score": 82 if severity == "high" else 72 if severity == "medium" else 62,
                "contributing_features": [col],
                "reasoning": f"{col} has {count} unusual values detected by {anomaly_type}.",
                "explanation": f"{col} has {count} unusual values detected by {anomaly_type}.",
                "business_impact": "Unusual values can distort averages, totals, forecasts, and segment rankings.",
                "business_explanation": "Unusual values can distort averages, totals, forecasts, and segment rankings.",
                "recommended_action": f"Review source rows for {col} and decide whether to correct, exclude, or report them separately.",
            })
        except Exception:
            continue

    return out
