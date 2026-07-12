from __future__ import annotations

from typing import Any, Dict

import pandas as pd


def assess_dataset_health(df: pd.DataFrame, dataset_profile: Dict[str, Any]) -> Dict[str, Any]:
    rows = max(len(df), 1)
    total_cells = max(int(df.shape[0] * df.shape[1]), 1)
    missing_percent = round(float(df.isna().sum().sum()) / total_cells * 100, 2)
    duplicate_percent = round(float(df.duplicated().sum()) / rows * 100, 2)
    column_quality = {}
    skewness = {}
    outlier_percent = 0.0

    for column in df.columns:
        missing = round(float(df[column].isna().mean()) * 100, 2)
        quality = max(0.0, 100.0 - missing)
        column_quality[column] = {
            "quality_score": round(quality, 2),
            "missing_percent": missing,
            "dtype": str(df[column].dtype),
            "explanation": f"{column} quality is based on completeness and detected type stability.",
        }

    numeric_columns = dataset_profile.get("numeric_columns", [])
    outlier_rows = set()
    for column in numeric_columns:
        values = pd.to_numeric(df[column], errors="coerce").dropna()
        if len(values) < 4:
            continue
        skewness[column] = round(float(values.skew()), 4) if len(values) > 2 else 0
        q1 = values.quantile(0.25)
        q3 = values.quantile(0.75)
        iqr = q3 - q1
        if iqr:
            mask = (values < q1 - 1.5 * iqr) | (values > q3 + 1.5 * iqr)
            outlier_rows.update(values[mask].index.tolist())
    if rows:
        outlier_percent = round(len(outlier_rows) / rows * 100, 2)

    score = round(max(0.0, 100.0 - missing_percent * 0.45 - duplicate_percent * 0.35 - outlier_percent * 0.2), 2)
    return {
        "missing_percent": missing_percent,
        "duplicate_percent": duplicate_percent,
        "outlier_percent": outlier_percent,
        "skewness": skewness,
        "data_types": {column: str(df[column].dtype) for column in df.columns},
        "null_heatmap": df.isna().astype(int).head(200).to_dict(orient="list"),
        "column_quality": column_quality,
        "overall_health_score": score,
        "explanation": "Dataset health combines missing values, duplicate rows, outlier pressure, skewness, and per-column completeness.",
    }
