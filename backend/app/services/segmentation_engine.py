from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

try:
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    from sklearn.preprocessing import StandardScaler
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


def segment_records(df: pd.DataFrame, dataset_profile: Dict[str, Any]) -> Dict[str, Any]:
    numeric_columns = dataset_profile.get("numeric_columns", [])[:10]
    if not HAS_SKLEARN or len(numeric_columns) < 2 or len(df) < 10:
        return {
            "model": "KMeans",
            "segments": [],
            "confidence_score": 0,
            "reasoning": "Segmentation requires at least 10 rows and two numeric measures.",
        }

    matrix = df[numeric_columns].apply(pd.to_numeric, errors="coerce").fillna(df[numeric_columns].median(numeric_only=True)).fillna(0)
    scaled = StandardScaler().fit_transform(matrix)
    k = min(5, max(2, len(df) // 25 or 2))
    model = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = model.fit_predict(scaled)
    silhouette = silhouette_score(scaled, labels) if len(set(labels)) > 1 and len(df) > k else 0

    frame = matrix.copy()
    frame["_segment"] = labels
    segments: List[Dict[str, Any]] = []
    global_mean = matrix.mean(numeric_only=True)
    for segment_id, group in frame.groupby("_segment"):
        size = len(group)
        profile_delta = group[numeric_columns].mean(numeric_only=True).subtract(global_mean).sort_values(key=lambda s: s.abs(), ascending=False)
        contributors = profile_delta.head(4).index.tolist()
        segments.append({
            "segment": int(segment_id),
            "size": int(size),
            "share_percent": round(size / max(len(df), 1) * 100, 2),
            "contributing_features": contributors,
            "reasoning": f"Segment {int(segment_id) + 1} differs most on {', '.join(contributors) or 'numeric measures'}.",
            "business_explanation": "This group has a distinct metric pattern and may need targeted reporting, pricing, retention, or operations actions.",
            "recommended_action": "Compare this segment against top dimensions and recent time periods to identify controllable drivers.",
        })

    return {
        "model": "KMeans",
        "segment_count": k,
        "confidence_score": int(round(max(0.0, min(1.0, (silhouette + 1) / 2)) * 100)),
        "contributing_features": numeric_columns,
        "segments": segments,
    }
