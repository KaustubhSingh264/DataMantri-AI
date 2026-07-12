from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

try:
    from sklearn.ensemble import RandomForestRegressor
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

try:
    import shap  # type: ignore
    HAS_SHAP = True
except ImportError:
    shap = None
    HAS_SHAP = False


def explain_predictions(df: pd.DataFrame, dataset_profile: Dict[str, Any]) -> Dict[str, Any]:
    numeric_columns = dataset_profile.get("numeric_columns", [])[:12]
    if not HAS_SKLEARN or len(numeric_columns) < 2 or len(df) < 20:
        return {
            "method": "feature_importance",
            "available": False,
            "reasoning": "Explainable AI requires enough rows and at least two numeric fields.",
            "feature_importance": [],
        }

    target = numeric_columns[0]
    features = [column for column in numeric_columns[1:] if column != target]
    matrix = df[[target] + features].apply(pd.to_numeric, errors="coerce").fillna(df[[target] + features].median(numeric_only=True)).fillna(0)
    X = matrix[features]
    y = matrix[target]
    model = RandomForestRegressor(n_estimators=80, random_state=42, min_samples_leaf=max(1, len(df) // 100))
    model.fit(X, y)

    importances = [
        {"feature": feature, "importance": round(float(score), 4)}
        for feature, score in sorted(zip(features, model.feature_importances_), key=lambda item: item[1], reverse=True)
    ]
    method = "Random Forest feature importance"
    shap_values: List[Dict[str, Any]] = []
    if HAS_SHAP:
        try:
            explainer = shap.TreeExplainer(model)
            values = explainer.shap_values(X.head(200))
            means = abs(pd.DataFrame(values, columns=features)).mean().sort_values(ascending=False)
            shap_values = [{"feature": feature, "mean_abs_shap": round(float(value), 4)} for feature, value in means.head(8).items()]
            method = "SHAP"
        except Exception:
            shap_values = []

    top_features = [item["feature"] for item in (shap_values or importances)[:5]]
    return {
        "available": True,
        "method": method,
        "target": target,
        "confidence_score": int(round(min(0.95, max(0.5, model.score(X, y))) * 100)),
        "feature_importance": importances[:10],
        "shap_values": shap_values[:10],
        "contributing_features": top_features,
        "reasoning": f"Feature importance was learned by predicting {target} from other numeric fields.",
        "business_explanation": f"The top drivers indicate which measures move most closely with {_humanize(target)}.",
        "recommended_action": "Use these drivers as hypotheses for drill-downs, experiments, and monitoring alerts.",
    }


def _humanize(value: str) -> str:
    return str(value or "").replace("_", " ").strip().title()
