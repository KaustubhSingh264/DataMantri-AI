from __future__ import annotations

from typing import Any, Dict, List, Tuple

import pandas as pd

try:
    from sklearn.impute import KNNImputer
    from sklearn.preprocessing import StandardScaler
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


def engineer_features(df: pd.DataFrame, dataset_profile: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    frame = df.copy()
    created: List[str] = []
    numeric_columns = list(dataset_profile.get("numeric_columns", []))
    datetime_columns = list(dataset_profile.get("datetime_columns", []))
    categorical_columns = list(dataset_profile.get("categorical_columns", []))

    for column in datetime_columns[:3]:
        parsed = pd.to_datetime(frame[column], errors="coerce")
        for part, values in {
            "year": parsed.dt.year,
            "month": parsed.dt.month,
            "dayofweek": parsed.dt.dayofweek,
        }.items():
            name = f"{column}_{part}"
            frame[name] = values
            created.append(name)

    if numeric_columns:
        if HAS_SKLEARN and len(frame) >= 3:
            imputer = KNNImputer(n_neighbors=min(5, max(1, len(frame) - 1)))
            frame[numeric_columns] = imputer.fit_transform(frame[numeric_columns])
            imputer_name = "KNNImputer"
        else:
            for column in numeric_columns:
                frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(pd.to_numeric(frame[column], errors="coerce").median())
            imputer_name = "median"

        if HAS_SKLEARN:
            scaled = StandardScaler().fit_transform(frame[numeric_columns])
            for idx, column in enumerate(numeric_columns[:12]):
                name = f"{column}_scaled"
                frame[name] = scaled[:, idx]
                created.append(name)
    else:
        imputer_name = "not_applicable"

    encoded_columns: List[str] = []
    for column in categorical_columns[:8]:
        top_values = frame[column].astype("string").fillna("Unknown").value_counts().head(6).index
        for value in top_values:
            name = f"{column}_{str(value)[:24]}".replace(" ", "_")
            frame[name] = (frame[column].astype("string").fillna("Unknown") == value).astype(int)
            encoded_columns.append(name)
            created.append(name)

    metadata = {
        "created_features": created,
        "encoded_columns": encoded_columns,
        "imputation": imputer_name,
        "numeric_features": numeric_columns,
        "datetime_features": datetime_columns,
        "categorical_features": categorical_columns,
    }
    return frame, metadata
