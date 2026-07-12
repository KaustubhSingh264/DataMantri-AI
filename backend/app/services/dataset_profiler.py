from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import pandas as pd


BUSINESS_MEASURE_HINTS = {
    "money": ["amount", "revenue", "sales", "price", "cost", "profit", "expense", "salary", "budget", "balance", "invoice"],
    "volume": ["quantity", "qty", "units", "orders", "transactions", "volume", "count"],
    "rate": ["rate", "ratio", "percent", "percentage", "margin", "conversion", "ctr", "cpc"],
    "score": ["score", "rating", "nps", "satisfaction"],
}


def _humanize(value: str) -> str:
    return str(value or "").replace("_", " ").strip().title()


def _semantic_type(column: str, series: pd.Series, row_count: int) -> str:
    lower = str(column).lower().replace("_", " ")
    unique_count = int(series.nunique(dropna=True))

    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_numeric_dtype(series):
        if lower == "id" or lower.endswith(" id") or lower.endswith("_id") or lower.endswith("id"):
            return "identifier"
        for semantic, hints in BUSINESS_MEASURE_HINTS.items():
            if any(hint in lower for hint in hints):
                return semantic
        return "measure"
    if any(term in lower for term in ["date", "time", "month", "year"]):
        return "datetime_candidate"
    if unique_count <= min(50, max(2, row_count * 0.4)):
        return "dimension"
    return "text"


def inspect_dataset(df: pd.DataFrame) -> Dict[str, Any]:
    row_count = int(len(df))
    column_profiles: Dict[str, Dict[str, Any]] = {}
    numeric_columns: List[str] = []
    categorical_columns: List[str] = []
    datetime_columns: List[str] = []
    measure_columns: List[str] = []
    dimension_columns: List[str] = []

    for column in df.columns:
        series = df[column]
        semantic = _semantic_type(column, series, row_count)
        if pd.api.types.is_numeric_dtype(series) and semantic != "identifier":
            numeric_columns.append(column)
            measure_columns.append(column)
        if semantic in {"dimension", "text"}:
            categorical_columns.append(column)
        if semantic == "datetime":
            datetime_columns.append(column)
        if semantic == "dimension":
            dimension_columns.append(column)

        completeness = 1.0 - float(series.isna().mean()) if row_count else 0.0
        cardinality = int(series.nunique(dropna=True))
        column_profiles[column] = {
            "name": column,
            "label": _humanize(column),
            "dtype": str(series.dtype),
            "semantic_type": semantic,
            "missing_count": int(series.isna().sum()),
            "missing_percent": round(float(series.isna().mean() * 100), 2) if row_count else 0,
            "unique_count": cardinality,
            "cardinality_ratio": round(cardinality / max(row_count, 1), 4),
            "completeness": round(completeness, 4),
            "sample_values": [str(value) for value in series.dropna().head(3).tolist()],
        }

        if column in numeric_columns:
            values = pd.to_numeric(series, errors="coerce").dropna()
            if not values.empty:
                column_profiles[column]["stats"] = {
                    "sum": round(float(values.sum()), 4),
                    "mean": round(float(values.mean()), 4),
                    "median": round(float(values.median()), 4),
                    "min": round(float(values.min()), 4),
                    "max": round(float(values.max()), 4),
                    "std": round(float(values.std()), 4) if len(values) > 1 else 0,
                }

    return {
        "row_count": row_count,
        "column_count": int(len(df.columns)),
        "columns": column_profiles,
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "datetime_columns": datetime_columns,
        "measure_columns": measure_columns,
        "dimension_columns": dimension_columns,
        "missing_cells": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
    }


def discover_dynamic_kpis(df: pd.DataFrame, dataset_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    kpis: List[Dict[str, Any]] = []
    columns = dataset_profile.get("columns", {})
    row_count = max(int(dataset_profile.get("row_count") or len(df)), 1)

    for column in dataset_profile.get("measure_columns", [])[:12]:
        meta = columns.get(column, {})
        values = pd.to_numeric(df[column], errors="coerce").dropna()
        if values.empty:
            continue
        completeness = float(meta.get("completeness", 0.75))
        semantic = meta.get("semantic_type", "measure")
        aggregation = "mean" if semantic in {"rate", "score"} else "sum"
        value = float(values.mean() if aggregation == "mean" else values.sum())
        confidence = int(round(min(0.98, max(0.55, completeness * min(1.0, len(values) / row_count))) * 100))
        kpis.append({
            "name": f"{meta.get('label') or _humanize(column)} {'Average' if aggregation == 'mean' else 'Total'}",
            "value": round(value, 2),
            "source_columns": [column],
            "aggregation": aggregation,
            "confidence": confidence,
            "reasoning": f"Selected because {meta.get('label') or column} is a numeric business measure with {round(completeness * 100, 1)}% completeness.",
            "contributing_features": [column],
            "business_explanation": f"This KPI summarizes {_humanize(column)} directly from the uploaded dataset.",
            "recommended_action": "Track this metric by time period and top business segments before making operational decisions.",
        })

    for column in dataset_profile.get("dimension_columns", [])[:8]:
        meta = columns.get(column, {})
        unique_count = int(df[column].nunique(dropna=True))
        confidence = int(round(min(0.95, max(0.55, float(meta.get("completeness", 0.75)))) * 100))
        kpis.append({
            "name": f"Unique {meta.get('label') or _humanize(column)}",
            "value": unique_count,
            "source_columns": [column],
            "aggregation": "nunique",
            "confidence": confidence,
            "reasoning": f"Selected because {meta.get('label') or column} behaves like a business segment or entity.",
            "contributing_features": [column],
            "business_explanation": f"This KPI shows how many distinct {_humanize(column)} values exist in the uploaded data.",
            "recommended_action": "Use this dimension for segmentation and drill-down analysis.",
        })

    return kpis[:16]
