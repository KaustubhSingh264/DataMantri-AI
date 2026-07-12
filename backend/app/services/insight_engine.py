from typing import List, Optional, Dict, Any
import math
import numpy as np
import pandas as pd


def humanize_label(value: str):
    label = str(value or "").replace("_", " ").strip()
    replacements = {
        "id": "ID",
        "kpi": "KPI",
        "csv": "CSV",
    }
    words = [replacements.get(word.lower(), word.capitalize()) for word in label.split()]
    return " ".join(words)


def make_insight(title: str, detail: str, icon: str = "•", confidence: float = 0.75) -> Dict[str, Any]:
    # Backwards-compatible small insight object used by other code paths.
    return {
        "title": title,
        "detail": detail,
        "icon": icon,
        "confidence": round(min(max(confidence, 0.0), 1.0), 2),
    }


def _eli5_text(text: str) -> str:
    # Very small heuristic simplifier for ELI5 mode.
    t = str(text)
    # Collapse multiple sentences to a single plain sentence
    if "." in t:
        t = t.split(".")[0]
    # remove parenthetical clauses
    t = t.replace("(", "").replace(")", "")
    return t.strip()


def _simple_translate(text: str, lang: str) -> str:
    """Lightweight, rule-based translation for commonly used business phrases.
    This is intentionally conservative (no hallucination) and only maps a small set
    of business-framing phrases into Hindi and Hinglish equivalents.
    """
    if not text:
        return text
    if lang == "en":
        return text

    # common phrase mappings
    mappings_hi = {
        "Concentration risk": "एकाग्रता जोखिम",
        "Opportunity": "अवसर",
        "Anomalies detected": "विसंगतियाँ पाई गईं",
        "Recent growth detected": "हालिया वृद्धि दर्ज की गई है",
        "Data health score": "डेटा स्वास्थ्य स्कोर",
        "Duplicates": "नक़ल प्रविष्टियाँ",
        "Missing data": "लापता डेटा",
        "Investigate": "जांच करें",
        "Recommended action": "अनुशंसित कार्रवाई",
        "Expected outcome": "अपेक्षित परिणाम",
    }

    mappings_hinglish = {
        "Concentration risk": "Concentration risk (ekagraata ka khatra)",
        "Opportunity": "Opportunity (mauka)",
        "Anomalies detected": "Anomalies detected (asamanya values)",
        "Recent growth detected": "Recent growth detected (hal hi ki growth)",
        "Data health score": "Data health score",
        "Duplicates": "Duplicates (duplicate rows)",
        "Missing data": "Missing data (kuch values missing)",
        "Investigate": "Investigate (janch karein)",
        "Recommended action": "Recommended action (sifarish)",
        "Expected outcome": "Expected outcome (umidit parinaam)",
    }

    # apply mapping naively
    if lang == "hi":
        for k, v in mappings_hi.items():
            text = text.replace(k, v)
        return text
    if lang == "hinglish":
        for k, v in mappings_hinglish.items():
            text = text.replace(k, v)
        return text

    return text


def build_structured_insight(
    title: str,
    observation: str,
    evidence: Optional[List[Dict[str, Any]]] = None,
    impact: Optional[str] = None,
    action: Optional[str] = None,
    reasoning: Optional[str] = None,
    confidence: float = 0.75,
    icon: str = "•",
) -> Dict[str, Any]:
    """Return a structured insight while preserving `title`, `detail`, and `confidence` for backward compatibility.

    Fields:
      - observation: one-line factual observation
      - evidence: list of {kpi, column, value}
      - impact: business impact statement
      - action: recommended action
      - modes: dict with 'business','data','eli5' renderings
    """
    evidence = evidence or []
    detail = observation
    # default reasoning derived from evidence when not provided
    if reasoning is None:
        if evidence:
            try:
                reasoning = "Based on observed evidence: " + ", ".join([f"{ev.get('kpi','')}: {ev.get('value')}" for ev in evidence])
            except Exception:
                reasoning = "Evidence supports the observation."
        else:
            reasoning = "Observation derived from dataset signals."
    # business-mode: full detail
    business_text = observation
    if impact:
        business_text = f"{business_text} {impact}"
    if action:
        business_text = f"{business_text} Recommended action: {action}"

    # data-mode: include evidence list
    data_evidence = ", ".join([f"{ev.get('kpi','')}={ev.get('value')}" for ev in evidence]) if evidence else ""
    data_text = f"{observation}. Evidence: {data_evidence}" if data_evidence else observation

    eli5_text = _eli5_text(observation)

    structured = {
        "title": title,
        "detail": detail,
        "icon": icon,
        "confidence": round(min(max(confidence, 0.0), 1.0), 2),
        "observation": observation,
        "reasoning": reasoning,
        "evidence": evidence,
        "impact": impact,
        "action": action,
        # backward-compatible English default strings
        "modes": {"business": business_text, "data": data_text, "eli5": eli5_text},
        # localized variants (conservative mapping)
        "modes_i18n": {
            "business": {"en": business_text, "hi": _simple_translate(business_text, "hi"), "hinglish": _simple_translate(business_text, "hinglish")},
            "data": {"en": data_text, "hi": _simple_translate(data_text, "hi"), "hinglish": _simple_translate(data_text, "hinglish")},
            "eli5": {"en": eli5_text, "hi": _simple_translate(eli5_text, "hi"), "hinglish": _simple_translate(eli5_text, "hinglish")},
        },
    }
    # Attach placeholder scores; these may be updated by scoring functions
    structured["confidence_score"] = int(round(structured["confidence"] * 100))
    structured["business_impact_score"] = None
    structured["importance"] = None
    structured["priority"] = None
    return structured


def _get_row_count(profile: dict, kpis: dict) -> int:
    # prefer profile, then kpis top-level, then before_cleaning
    rows = profile.get("shape", {}).get("rows")
    if rows is not None:
        return int(rows)
    if isinstance(kpis, dict):
        if kpis.get("row_count") is not None:
            return int(kpis.get("row_count"))
        bc = kpis.get("before_cleaning") or {}
        if isinstance(bc, dict) and bc.get("row_count") is not None:
            return int(bc.get("row_count").get("raw_value") if isinstance(bc.get("row_count"), dict) else bc.get("row_count"))
    return 0


def _find_time_column(df: pd.DataFrame, profile: dict) -> Optional[str]:
    # prefer profile datetime columns, else infer from names
    dt_cols = profile.get("datetime_columns") or profile.get("profile", {}).get("datetime_columns")
    if dt_cols:
        return dt_cols[0]
    for col in df.columns:
        lname = col.lower()
        if any(token in lname for token in ["date", "time", "created", "timestamp", "order_date"]):
            try:
                parsed = pd.to_datetime(df[col], errors="coerce")
                if parsed.notna().sum() >= max(3, int(len(df) * 0.01)):
                    return col
            except Exception:
                continue
    return None


def generate_insights(profile: dict, kpis: dict, df: Optional[pd.DataFrame] = None) -> List[dict]:
    """
    Business-focused insight generator.
    - Non-breaking: keeps same signature but accepts optional `df` for richer signals.
    - Produces executive summary, top insights, opportunities, risks, recommendations, trend/correlation/anomaly highlights.
    """
    insights: List[dict] = []

    row_count = _get_row_count(profile, kpis)
    cols = profile.get("shape", {}).get("columns", 0)

    # Executive summary lead (structured + backward-compatible fields)
    insights.append(
        build_structured_insight(
            "Executive summary",
            f"This dataset contains {row_count} records across {cols} columns. The analysis highlights prioritized opportunities, risks, and recommended next steps for business users.",
            evidence=[{"kpi": "row_count", "value": row_count}, {"kpi": "columns", "value": cols}],
            impact=None,
            action=None,
            confidence=0.9,
        )
    )

    # Basic data-quality signals
    duplicate_rows = profile.get("duplicate_rows", 0)
    if duplicate_rows and duplicate_rows > 0:
        insights.append(build_structured_insight(
            "Duplicate rows found",
            f"There are {duplicate_rows} duplicate rows ({profile.get('duplicate_percent', 0)}%). Duplicates can inflate totals and bias segment rankings — deduplicate before reporting totals.",
            evidence=[{"kpi": "duplicate_rows", "value": duplicate_rows}, {"kpi": "duplicate_percent", "value": profile.get('duplicate_percent', 0)}],
            impact="Duplicates may artificially increase totals and distort segment shares.",
            action="Run a deduplication step and reconcile totals before producing business reports.",
            confidence=0.9,
        ))

    missing_per_col = profile.get("missing_percent", {})
    total_missing = sum(profile.get("missing_values", {}).values())
    if total_missing and total_missing > 0:
        # call out worst columns
        worst = sorted(missing_per_col.items(), key=lambda x: x[1], reverse=True)[:3]
        worst_text = ", ".join([f"{k} ({v}%)" for k, v in worst])
        insights.append(build_structured_insight(
            "Missing data hotspots",
            f"{total_missing} missing cells detected. Highest-missing columns: {worst_text}. Address these before using affected KPIs for decisions.",
            evidence=[{"kpi": k, "value": v} for k, v in worst],
            impact="Missing cells reduce KPI reliability for affected segments.",
            action="Impute or collect missing values for prioritized columns, or exclude affected KPIs from trend calculations until resolved.",
            confidence=0.88,
        ))

    # Data health if present
    dh = None
    if isinstance(kpis, dict):
        dh = kpis.get("data_health", {}) or {}
        hs = None
        if isinstance(dh, dict):
            health = dh.get("health_score")
            if isinstance(health, dict):
                hs = health.get("raw_value")
        if hs is not None:
            insights.append(build_structured_insight(
                "Data health score",
                f"Overall data health score is {hs}/100. Use this as a quick indicator of readiness for business reporting — focus on the top data-quality issues to improve this score.",
                evidence=[{"kpi": "data_health.score", "value": hs}],
                impact="Lower data health indicates greater effort required to trust KPIs.",
                action="Prioritize top data-quality issues surfaced in the profile to raise the health score.",
                confidence=0.85,
            ))

    # If df provided, validate counts
    if df is not None:
        try:
            if len(df) != row_count:
                insights.append(build_structured_insight(
                    "Row count mismatch",
                    f"Profile row count ({row_count}) does not match the DataFrame length ({len(df)}). Using the actual DataFrame for downstream signals.",
                    evidence=[{"kpi": "profile_row_count", "value": row_count}, {"kpi": "df_length", "value": len(df)}],
                    impact="Downstream signals should trust the actual DataFrame length.",
                    action="Confirm source of mismatch (truncated export, streaming issues) and re-run profiling after fix.",
                    confidence=0.75,
                ))
                # prefer df length
                row_count = len(df)
        except Exception:
            pass

    # Numeric summaries: find top numeric contributors by total
    numeric_cols = profile.get("numeric_columns") or list((profile.get("summary_stats", {}) or {}).keys()) or []
    totals = []
    if df is not None and numeric_cols:
        for col in numeric_cols:
            if col.lower().endswith("id"):
                continue
            try:
                s = pd.to_numeric(df[col], errors="coerce").fillna(0)
                totals.append((col, float(s.sum())))
            except Exception:
                continue
        totals = sorted(totals, key=lambda x: x[1], reverse=True)
        # top numeric columns
        for col, tot in totals[:5]:
            # business-friendly label and reason
            grand = sum([t for _, t in totals]) or 1
            percent_of_sum = round(tot / grand * 100, 1)
            title = f"Top numeric contributor: {humanize_label(col)}"
            detail = f"{humanize_label(col)} totals {tot:,.0f}, contributing {percent_of_sum}% of combined numeric totals. Investigate this metric for business impact and trending behavior."
            insights.append(build_structured_insight(
                title,
                detail,
                evidence=[{"kpi": top_col if (top_col := col) else col, "value": tot}],
                impact="High contribution indicates this metric drives totals and should be prioritized in drilling/forecasting.",
                action=f"Perform SKU-level, merchant-level, or category-level analysis on {humanize_label(col)}.",
                confidence=0.8,
            ))

    # Categorical concentration and value-based performance
    cat_summary = profile.get("category_summary", {}) or {}
    revenue_col = None
    for candidate in ["revenue", "total_amount", "amount", "sales", "total"]:
        lcands = [c for c in (numeric_cols or []) if isinstance(c, str) and c.lower() == candidate]
        if lcands:
            revenue_col = lcands[0]
            break
    # fallback: look for likely revenue column in df
    if df is not None and revenue_col is None:
        for c in df.select_dtypes(include=["number"]).columns:
            if any(tok in c.lower() for tok in ["amount", "revenue", "sales", "total"]):
                revenue_col = c
                break

    for col, meta in cat_summary.items():
        top_share = meta.get("top_share", 0)
        top_value = meta.get("top_value")
        if top_share >= 40:
            # if revenue present, compute share of revenue by top category
            rev_part = None
            if df is not None and revenue_col is not None:
                try:
                    grp = df.groupby(col)[revenue_col].sum().sort_values(ascending=False)
                    if not grp.empty and top_value in grp.index:
                        rev_part = round(grp.loc[top_value] / grp.sum() * 100, 1)
                except Exception:
                    rev_part = None
            detail = f"{top_value} represents {top_share}% of {col} values."
            if rev_part is not None:
                detail += f" It also accounts for {rev_part}% of {humanize_label(revenue_col)} — prioritize this segment for targeted actions."
            else:
                detail += " Consider checking business metrics (revenue, orders) against this segment to prioritize actions."
            insights.append(build_structured_insight(
                f"Concentration: {humanize_label(col)}",
                detail,
                evidence=[{"kpi": f"concentration.{col}.top_value", "value": top_value}, {"kpi": f"concentration.{col}.top_share", "value": top_share}] + ([{"kpi": f"revenue_share_of_{top_value}", "value": rev_part}] if rev_part is not None else []),
                impact="High concentration can indicate single points of failure or clear prioritization opportunities.",
                action="Consider targeted campaigns or diversification strategies for concentrated segments.",
                confidence=0.9,
            ))

    # Time-based trends and growth if time column present
    if df is not None:
        time_col = _find_time_column(df, profile)
        if time_col:
            try:
                ts = pd.to_datetime(df[time_col], errors="coerce")
                df_time = df.copy()
                df_time["__time"] = ts
                # pick natural business metric to trend: revenue_col or top numeric
                trend_col = revenue_col or (totals[0][0] if totals else None)
                if trend_col:
                    # monthly aggregates
                    agg = df_time.dropna(subset=["__time"]).set_index("__time")[trend_col].resample("M").sum()
                    if len(agg) >= 3:
                        recent = agg[-3:].mean()
                        prev = agg[-6:-3].mean() if len(agg) >= 6 else (agg[:-3].mean() if len(agg) > 3 else None)
                        if prev and prev > 0:
                            growth = round((recent - prev) / prev * 100, 1)
                            insights.append(build_structured_insight(
                                f"{humanize_label(trend_col)} growth",
                                f"{humanize_label(trend_col)} has changed by {growth}% comparing the most recent 3-month period to the previous 3 months.",
                                evidence=[{"kpi": trend_col, "value": growth, "unit": "%"}, {"kpi": "period_recent_mean", "value": float(recent)}, {"kpi": "period_previous_mean", "value": float(prev)}],
                                impact="Recent growth may indicate accelerating demand or seasonality that affects planning.",
                                action="Investigate drivers for the growth and adjust forecasts and inventory accordingly.",
                                confidence=0.88,
                            ))
            except Exception:
                pass

    # Correlation highlights
    if df is not None:
        try:
            num_df = df.select_dtypes(include=[np.number]).copy()
            if not num_df.empty and num_df.shape[1] >= 2:
                corr = num_df.corr().abs()
                # find top off-diagonal correlations
                pairs = []
                for i, c1 in enumerate(corr.columns):
                    for j, c2 in enumerate(corr.columns):
                        if j <= i:
                            continue
                        val = corr.iloc[i, j]
                        pairs.append((c1, c2, float(val)))
                pairs = sorted(pairs, key=lambda x: x[2], reverse=True)
                for c1, c2, val in pairs[:5]:
                    if val >= 0.6:
                        sign = "positively" if (df[c1].corr(df[c2]) > 0) else "negatively"
                        insights.append(build_structured_insight(
                            f"Correlation: {humanize_label(c1)} & {humanize_label(c2)}",
                            f"{humanize_label(c1)} is {sign} correlated with {humanize_label(c2)} (r={round(val,2)}). Consider causal checks and controlled experiments before acting on this relationship.",
                            evidence=[{"kpi": f"corr.{c1}.{c2}", "value": round(val,2)}],
                            impact="Correlation suggests a relationship worth investigating for causal links.",
                            action="Run controlled experiments or causal inference checks before committing to operational changes based on this correlation.",
                            confidence=0.8,
                        ))
        except Exception:
            pass

    # Outliers / anomalies (z-score)
    if df is not None:
        try:
            for col in df.select_dtypes(include=[np.number]).columns:
                if col.lower().endswith("id"):
                    continue
                s = pd.to_numeric(df[col], errors="coerce").dropna()
                if s.empty or len(s) < 10:
                    continue
                z = (s - s.mean()) / (s.std() if s.std() != 0 else 1)
                high = (z > 4).sum()
                low = (z < -4).sum()
                if high + low > 0:
                    insights.append(build_structured_insight(
                        f"Anomalies in {humanize_label(col)}",
                        f"Detected {high} high and {low} low extreme values in {humanize_label(col)}. These outliers can skew averages and totals; investigate and validate source rows.",
                        evidence=[{"kpi": f"anomaly.{col}.high", "value": int(high)}, {"kpi": f"anomaly.{col}.low", "value": int(low)}],
                        impact="Outliers can distort aggregated KPIs and forecasts.",
                        action="Inspect source rows and decide whether to cap, exclude, or correct anomalous values.",
                        confidence=0.78,
                    ))
        except Exception:
            pass

    # Recommendations & opportunities derived from above signals
    # - If top contributor exists: recommend targeted actions
    if df is not None and numeric_cols and totals:
        try:
            top_col, top_val = totals[0]
            rec_title = f"Opportunity: focus on {humanize_label(top_col)}"
            rec_detail = f"{humanize_label(top_col)} contributes the largest numeric total ({top_val:,.0f}). Consider targeted promotions, inventory prioritization, or deeper SKU-level analysis to grow revenue."
            insights.append(build_structured_insight(
                rec_title,
                rec_detail,
                evidence=[{"kpi": top_col, "value": top_val}],
                impact="Targeting the top contributor can yield outsized revenue or efficiency gains.",
                action=f"Design promotions or analyses specifically around {humanize_label(top_col)}.",
                confidence=0.82,
            ))
        except Exception:
            pass

    # Ensure we don't return trivial-only messages — add fallback
    if len(insights) < 6:
        insights.append(build_structured_insight(
            "Additional analysis recommended",
            "Provide a larger dataset or include explicit business metrics (revenue, profit) to surface more prioritized business insights and trend forecasts.",
            evidence=[],
            impact=None,
            action="Upload richer business metrics (revenue, orders) or longer time series for more prioritized insights.",
            confidence=0.5,
        ))

    # Post-process: compute business impact score, importance and priority for each insight
    def _compute_scores(ins: dict):
        # Confidence already present (0..1)
        conf = ins.get("confidence", 0.5)
        evidence = ins.get("evidence") or []

        # Evidence strength: number of evidence items and presence of numeric shares
        count_evidence = len(evidence)
        numeric_strength = 0.0
        for ev in evidence:
            try:
                v = ev.get("value")
                if isinstance(v, (int, float)):
                    # percent-like evidence (0..100) increases strength by proportion
                    if 0 <= v <= 100:
                        numeric_strength = max(numeric_strength, min(1.0, float(v) / 100.0))
                    else:
                        numeric_strength = max(numeric_strength, 0.5)
            except Exception:
                continue

        # Data coverage signal from profile: if many non-null in evidence-referenced columns
        coverage = 0.5
        try:
            cols = [ev.get("kpi") or ev.get("column") for ev in evidence if isinstance(ev, dict)]
            non_null_counts = []
            for c in cols:
                if isinstance(c, str) and profile.get("columns", {}).get(c):
                    non_null_counts.append(profile["columns"][c].get("non_null_count", 0))
            if non_null_counts:
                avg_non_null = sum(non_null_counts) / len(non_null_counts)
                total_rows = profile.get("shape", {}).get("rows") or _get_row_count(profile, kpis) or 1
                coverage = min(1.0, avg_non_null / max(1, total_rows))
        except Exception:
            coverage = 0.5

        # Business impact score heuristic: combine numeric_strength, confidence, and coverage
        biz_score = int(round(min(100, (numeric_strength * 60 + conf * 30 + coverage * 10) * 100 / 100)))
        ins["business_impact_score"] = biz_score

        # importance numeric: factor evidence count and biz_score
        importance = int(round(min(100, biz_score * (1 + count_evidence * 0.1))))
        ins["importance"] = importance

        # priority: High/Medium/Low
        if biz_score >= 70 or (conf >= 0.85 and numeric_strength >= 0.4):
            ins["priority"] = "High"
        elif biz_score >= 45 or conf >= 0.65:
            ins["priority"] = "Medium"
        else:
            ins["priority"] = "Low"

        # ensure confidence_score consistent
        try:
            ins["confidence_score"] = int(round(conf * 100))
        except Exception:
            ins["confidence_score"] = int(round(50))

    for ins in insights:
        try:
            _compute_scores(ins)
        except Exception:
            continue

    return insights
