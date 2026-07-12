from __future__ import annotations

from typing import Any, Dict


def build_feature_store_metadata(feature_metadata: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "status": "materialized_in_memory",
        "feature_count": len(feature_metadata.get("created_features", [])),
        "features": feature_metadata.get("created_features", []),
        "imputation": feature_metadata.get("imputation"),
    }
