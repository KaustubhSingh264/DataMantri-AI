from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd

from app.services.analytics_pipeline import PipelineContext, build_validation_report, normalize_dataframe, run_analysis
from app.services.localization_service import language_prompt_context, localize_analysis_payload, normalize_language


def _confidence(item: Dict[str, Any], fallback: int = 70) -> int:
    value = item.get("confidence_score", item.get("confidence", fallback))
    try:
        if value <= 1:
            value *= 100
        return int(round(max(0, min(100, float(value)))))
    except Exception:
        return fallback


def _action_from_ml_item(item: Dict[str, Any], source: str) -> Dict[str, Any]:
    title = item.get("title") or item.get("type") or item.get("column") or source
    finding = item.get("business_finding") or item.get("reasoning") or item.get("business_explanation") or item.get("detail") or item.get("observation")
    why = item.get("why_it_matters") or item.get("business_impact") or item.get("impact") or "This signal can affect revenue, profit, risk, customers, or operating reliability."
    action = item.get("recommended_action") or item.get("recommendation") or "Review the supporting ML evidence before taking action."
    confidence = _confidence(item)
    priority = item.get("priority") or ("High" if confidence >= 85 else "Medium" if confidence >= 65 else "Low")
    return {
        "title": str(title).replace("_", " ").title(),
        "business_finding": finding,
        "why_it_matters": why,
        "priority": priority,
        "expected_impact": item.get("expected_business_impact") or item.get("expected_impact") or item.get("impact") or "Depends on the affected metric and segment size.",
        "confidence": confidence,
        "ai_confidence": item.get("ai_confidence") or {"label": priority if priority in {"High", "Medium", "Low"} else "Medium", "percent": confidence},
        "reason": finding,
        "recommended_action": action,
        "source": source,
        "contributing_features": item.get("contributing_features") or item.get("source_columns") or [],
        "risk": item.get("severity") or item.get("risk"),
    }


def generate_business_advisor_report(df: Optional[pd.DataFrame] = None, analysis: Optional[Dict[str, Any]] = None, language: str = "en") -> Dict[str, Any]:
    language = normalize_language(language)
    if analysis is None:
        if df is None:
            raise ValueError("Either df or analysis is required.")
        ctx = PipelineContext("business_advisor_report")
        normalized, normalize_report = normalize_dataframe(df, ctx)
        validation_report = build_validation_report(normalized, normalize_report)
        analysis = run_analysis(normalized, ctx, validation_report=validation_report, language=language)
    else:
        analysis = localize_analysis_payload(analysis, language)

    forecasts = analysis.get("forecasts", []) or []
    anomalies = analysis.get("anomaly_engine", []) or []
    recommendations = analysis.get("recommendations", []) or []
    insights = analysis.get("insights", []) or []
    kpis = analysis.get("business_kpis", []) or []
    explanation = analysis.get("explanation_engine", {}) or {}
    lifecycle = analysis.get("dataset_lifecycle", {}) or {}

    actions: List[Dict[str, Any]] = []
    for item in anomalies[:4]:
        actions.append(_action_from_ml_item(item, "anomaly_engine"))
    for item in forecasts[:4]:
        actions.append(_action_from_ml_item(item, "forecast_engine"))
    for item in recommendations[:6]:
        actions.append(_action_from_ml_item(item, "recommendation_engine"))

    if explanation.get("available"):
        actions.append(_action_from_ml_item(explanation, "explanation_engine"))

    actions = sorted(actions, key=lambda item: ({"High": 3, "Medium": 2, "Low": 1}.get(item["priority"], 1), item["confidence"]), reverse=True)
    overview = analysis.get("executive_summary") or (
        f"Data Mantri analyzed {lifecycle.get('current_dataset', 'the selected dataset')} and generated ML-backed KPIs, risks, opportunities, and actions."
    )
    consultant_summary = (
        f"{overview} The recommended action plan focuses on the highest-confidence business signals first, "
        "so the team can protect downside risk while capturing the clearest growth opportunities."
    )

    return localize_analysis_payload({
        "status": "success",
        "language": language,
        "ai_prompt_context": language_prompt_context(language, mode="business_advisor", tone="consultative"),
        "dataset_lifecycle": lifecycle,
        "business_overview": consultant_summary,
        "executive_summary": consultant_summary,
        "top_risks": analysis.get("risks", []),
        "top_opportunities": analysis.get("opportunities", []),
        "growth_drivers": explanation.get("contributing_features", []),
        "revenue_drivers": explanation.get("feature_importance", []),
        "action_plan": actions[:8],
        "top_actions": [
            {"rank": index + 1, "action": item["recommended_action"], "detail": item.get("reason"), "confidence": item["confidence"]}
            for index, item in enumerate(actions[:5])
        ],
        "kpis": kpis,
        "insights": insights,
        "recommendations": actions[:8],
        "forecasts": forecasts,
        "confidence": _confidence(explanation, 72),
        "message": "Business Advisor report generated from saved ML analysis only.",
    }, language)
