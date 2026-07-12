from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import pandas as pd

try:
    from sklearn.cluster import DBSCAN
    from sklearn.ensemble import IsolationForest
    from sklearn.neighbors import LocalOutlierFactor
    from sklearn.preprocessing import StandardScaler
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


def detect_ml_anomalies(df: pd.DataFrame, dataset_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    numeric_columns = dataset_profile.get("numeric_columns", [])[:12]
    if not numeric_columns or len(df) < 8:
        return []

    matrix = df[numeric_columns].apply(pd.to_numeric, errors="coerce").fillna(df[numeric_columns].median(numeric_only=True)).fillna(0)
    if matrix.empty:
        return []

    results: List[Dict[str, Any]] = []
    if HAS_SKLEARN:
        scaled = StandardScaler().fit_transform(matrix)
        detectors = {
            "Isolation Forest": IsolationForest(contamination="auto", random_state=42),
            "Local Outlier Factor": LocalOutlierFactor(n_neighbors=min(20, max(2, len(matrix) - 1))),
            "DBSCAN": DBSCAN(eps=2.5, min_samples=max(3, min(8, len(matrix) // 10 or 3))),
        }
        for name, detector in detectors.items():
            try:
                labels = detector.fit_predict(scaled)
                mask = labels == -1
                count = int(mask.sum())
                if not count:
                    continue
                feature_scores = matrix.loc[mask].mean(numeric_only=True).subtract(matrix.mean(numeric_only=True)).abs().sort_values(ascending=False)
                contributors = feature_scores.head(4).index.tolist()
                percent = round(count / max(len(matrix), 1) * 100, 2)
                results.append({
                    "model": name,
                    "type": "multivariate_anomaly",
                    "anomaly_count": count,
                    "anomaly_percent": percent,
                    "confidence_score": int(max(55, min(95, 100 - percent))),
                    "contributing_features": contributors,
                    "reasoning": f"{name} marked {count} rows as unusual compared with the overall numeric pattern.",
                    "business_explanation": "These rows behave differently across multiple metrics and may represent data issues, exceptional customers, unusual transactions, or operational events.",
                    "recommended_action": "Review the flagged rows by source system and segment before using them in forecasts or executive KPIs.",
                })
            except Exception:
                continue

    if not results:
        zscores = matrix.sub(matrix.mean()).div(matrix.std().replace(0, np.nan)).abs()
        mask = zscores.max(axis=1).fillna(0) >= 3
        if mask.any():
            contributors = zscores.loc[mask].mean().sort_values(ascending=False).head(4).index.tolist()
            count = int(mask.sum())
            results.append({
                "model": "Z-score fallback",
                "type": "statistical_anomaly",
                "anomaly_count": count,
                "anomaly_percent": round(count / max(len(matrix), 1) * 100, 2),
                "confidence_score": 68,
                "contributing_features": contributors,
                "reasoning": "Rows were flagged because at least one numeric field is three or more standard deviations from normal.",
                "business_explanation": "Extreme values can distort totals, averages, and forecasts.",
                "recommended_action": "Validate these rows and consider separate reporting for exceptional events.",
            })

    return results[:6]
