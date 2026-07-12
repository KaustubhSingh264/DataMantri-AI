from typing import List, Dict, Any, Optional


def _humanize(col: str) -> str:
    return str(col or "").replace("_", " ").title()


def _priority_from_confidence(conf: float, severity: Optional[float] = None) -> str:
    # severity and confidence drive priority; keep deterministic, no invented numbers
    if severity is not None and severity >= 0.6:
        return "High"
    if conf >= 0.85:
        return "High"
    if conf >= 0.65:
        return "Medium"
    return "Low"


def _format_confidence(conf: float) -> int:
    try:
        return int(round(max(0.0, min(1.0, float(conf))) * 100))
    except Exception:
        return 50


def _extract_numeric_evidence(evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
    out = {}
    for ev in evidence or []:
        k = ev.get("kpi") or ev.get("column")
        v = ev.get("value")
        if isinstance(v, (int, float)):
            out[str(k)] = v
    return out


def _build_recommendation_from_insight(insight: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    # Required fields: Title, Observation, Evidence, Business Impact, Recommended Action,
    # Expected Outcome, Priority, Confidence
    title = insight.get("title") or "Recommendation"
    observation = insight.get("observation") or insight.get("detail") or ""
    evidence = insight.get("evidence") or []
    conf = insight.get("confidence") or 0.6

    # Derive severity for priority when possible from evidence numeric shares
    numeric_evidence = _extract_numeric_evidence(evidence)
    severity = None
    # common keys: concentration.* or a percentage value
    for k, v in numeric_evidence.items():
        if isinstance(v, (int, float)):
            try:
                # if evidence is a percent share between 0 and 100
                if 0 <= v <= 100:
                    severity = max(severity or 0.0, float(v) / 100.0)
                else:
                    # large absolute revenue numbers increase severity when they dominate
                    severity = max(severity or 0.0, 0.5)
            except Exception:
                continue

    priority = _priority_from_confidence(conf, severity)

    # Map insight types to consultant-grade recommendation templates
    low = title.lower()

    if "concentration" in low or "top numeric contributor" in low or "opportunity: focus on" in low:
        # Revenue / concentration style recommendation
        metric = None
        metric_value = None
        # pick first numeric evidence key/value
        if numeric_evidence:
            metric, metric_value = next(iter(numeric_evidence.items()))

        rec_title = "Revenue Concentration Risk" if "revenue" in (metric or "") or "total" in (metric or "") else f"Concentration Risk: {_humanize(metric) if metric else title}"
        business_impact = (
            "High: revenue or core metric is concentrated in a narrow segment, exposing the business to concentration risk."
            if (severity or 0) >= 0.5 else
            "Medium: a single segment contributes materially to totals and should be monitored."
        )

        recommended_action = (
            "Identify the top contributing entities (customers, products, or regions) using group-by revenue or transaction counts; run a sensitivity analysis to quantify dependence on the top segment; design targeted tests or diversification strategies."
        )

        expected_outcome = (
            "Reduced concentration exposure and clearer, prioritized growth levers. Improved resilience to single-segment shocks and more predictable forecasting."
        )

        rec = {
            "title": rec_title,
            "observation": observation,
            "evidence": evidence,
            "business_impact": business_impact,
            "recommended_action": recommended_action,
            "expected_outcome": expected_outcome,
            "priority": priority,
            "confidence": _format_confidence(conf),
        }
        return rec

    if "missing" in low or any("missing" in (str(ev.get("kpi") or "").lower()) for ev in evidence):
        rows = None
        cols = None
        # attempt to extract a missing count
        missing_cells = None
        for ev in evidence:
            if ev.get("kpi") in ("missing_cells", "missing"):
                missing_cells = ev.get("value")
        rec_title = "Data Quality: Missing Values"
        business_impact = "High: missing values reduce KPI reliability and can bias aggregations and segment-level analyses when concentrated in key columns."
        recommended_action = (
            "Prioritize columns by business impact, apply targeted imputation or collection for critical fields, and implement a monitoring alert for missing-rate regressions."
        )
        expected_outcome = (
            "Improved KPI reliability and reduced decision risk for metrics that depend on the imputed or collected fields."
        )
        rec = {
            "title": rec_title,
            "observation": observation,
            "evidence": evidence,
            "business_impact": business_impact,
            "recommended_action": recommended_action,
            "expected_outcome": expected_outcome,
            "priority": priority,
            "confidence": _format_confidence(conf),
        }
        return rec

    if "duplicate" in low:
        rec_title = "Data Integrity: Duplicate Rows"
        business_impact = "High: duplicates can inflate totals and distort customer/product rankings, affecting revenue attribution."
        recommended_action = "Detect canonical keys, deduplicate source data, and reconcile post-cleaning totals with business reports. Implement ingestion guards to prevent re-ingest."
        expected_outcome = "Accurate totals, consistent KPIs, and stronger trust in downstream reports."
        rec = {
            "title": rec_title,
            "observation": observation,
            "evidence": evidence,
            "business_impact": business_impact,
            "recommended_action": recommended_action,
            "expected_outcome": expected_outcome,
            "priority": priority,
            "confidence": _format_confidence(conf),
        }
        return rec

    if "anomal" in low or "anomalies" in low:
        # anomaly investigation
        rec_title = "Anomaly Investigation"
        recommended_action = (
            "Perform row-level investigation to validate outliers; check source system logs, joins, and transformations; create deterministic rules or statistical detectors to flag future anomalies."
        )
        expected_outcome = (
            "Fewer spurious spikes in KPIs, more robust forecasts, and faster incident resolution when upstream data changes."
        )
        business_impact = "Medium: anomalies can skew short-term forecasts and hide true trends until resolved."
        rec = {
            "title": rec_title,
            "observation": observation,
            "evidence": evidence,
            "business_impact": business_impact,
            "recommended_action": recommended_action,
            "expected_outcome": expected_outcome,
            "priority": priority,
            "confidence": _format_confidence(conf),
        }
        return rec

    if "correlation" in low or "correlated" in low:
        rec_title = "Correlation: Investigate Causality"
        recommended_action = (
            "Run causal checks (lag analysis, controlled experiments, or causal inference methods) and search for confounders before acting on correlated metrics."
        )
        expected_outcome = (
            "Clearer understanding of which relationships are actionable versus coincidental, reducing wasted investment in non-causal initiatives."
        )
        business_impact = "Medium: correlations suggest hypotheses but require validation to avoid incorrect operational changes."
        rec = {
            "title": rec_title,
            "observation": observation,
            "evidence": evidence,
            "business_impact": business_impact,
            "recommended_action": recommended_action,
            "expected_outcome": expected_outcome,
            "priority": priority,
            "confidence": _format_confidence(conf),
        }
        return rec

    if "growth" in low or "trend" in low or "growth" in (insight.get("observation") or "").lower():
        rec_title = "Growth Signal: Decompose Drivers"
        recommended_action = (
            "Break down recent growth by channel, product, and customer cohort; run attribution and cohort analyses to identify the highest-leverage drivers."
        )
        expected_outcome = (
            "Targeted investments in top-performing channels/products and more accurate short-term forecasts."
        )
        business_impact = "High if growth is revenue-related; otherwise Medium."
        rec = {
            "title": rec_title,
            "observation": observation,
            "evidence": evidence,
            "business_impact": business_impact,
            "recommended_action": recommended_action,
            "expected_outcome": expected_outcome,
            "priority": priority,
            "confidence": _format_confidence(conf),
        }
        return rec

    # For any other insight types produce a measured, specific recommendation only when insight contains concrete evidence
    if evidence:
        rec_title = f"Action: {_humanize(title)}"
        recommended_action = "Translate the finding into a focused analysis or operational test relevant to the evidence above."
        expected_outcome = "Actionable clarity for downstream reporting and operational decision-making."
        business_impact = "Depends on the metric and context; prioritize by revenue exposure and confidence."
        rec = {
            "title": rec_title,
            "observation": observation,
            "evidence": evidence,
            "business_impact": business_impact,
            "recommended_action": recommended_action,
            "expected_outcome": expected_outcome,
            "priority": priority,
            "confidence": _format_confidence(conf),
        }
        return rec

    # otherwise do not return a generic placeholder recommendation
    return None


def generate_recommendations(profile: Dict[str, Any], insights: List[Dict[str, Any]], df: Optional[Any] = None) -> List[Dict[str, Any]]:
    """
    Produce consulting-grade, evidence-driven recommendations derived from structured insights.
    This replaces previous generic patterns and only emits recommendations grounded in evidence.
    """
    recs: List[Dict[str, Any]] = []

    # Process each insight and generate a focused recommendation where applicable
    for ins in insights:
        try:
            rec = _build_recommendation_from_insight(ins)
            if rec:
                recs.append(rec)
        except Exception:
            continue

    # Remove duplicates by title
    seen = set()
    filtered = []
    for r in recs:
        t = r.get("title")
        if t in seen:
            continue
        seen.add(t)
        filtered.append(r)

    # Sort by priority then confidence
    priority_weight = {"High": 3, "Medium": 2, "Low": 1}

    def _rank(item):
        p = priority_weight.get(item.get("priority"), 1)
        c = item.get("confidence", 50)
        return (p, c)

    filtered = sorted(filtered, key=_rank, reverse=True)

    return filtered

