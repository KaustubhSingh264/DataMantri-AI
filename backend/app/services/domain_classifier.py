from __future__ import annotations

from typing import Any, Dict

import pandas as pd


DOMAIN_KEYWORDS = {
    "retail": ["store", "sku", "product", "category", "inventory", "stock", "price", "discount", "return"],
    "sales": ["sales", "revenue", "deal", "lead", "pipeline", "quota", "order", "customer", "invoice"],
    "finance": ["expense", "cost", "profit", "margin", "budget", "cash", "ledger", "amount", "tax"],
    "hr": ["employee", "salary", "hire", "attrition", "department", "attendance", "performance", "manager"],
    "manufacturing": ["machine", "defect", "batch", "plant", "downtime", "yield", "production", "workorder"],
    "healthcare": ["patient", "diagnosis", "treatment", "admission", "doctor", "claim", "procedure", "hospital"],
    "logistics": ["shipment", "delivery", "route", "warehouse", "carrier", "freight", "tracking", "vehicle"],
    "banking": ["account", "transaction", "balance", "loan", "deposit", "credit", "debit", "branch"],
    "marketing": ["campaign", "impression", "click", "conversion", "channel", "ctr", "cpc", "lead"],
}


def classify_domain(df: pd.DataFrame, dataset_profile: Dict[str, Any] | None = None) -> Dict[str, Any]:
    columns = [str(column).lower().replace("_", " ") for column in df.columns]
    scores = {domain: 0.0 for domain in DOMAIN_KEYWORDS}

    for column in columns:
        for domain, keywords in DOMAIN_KEYWORDS.items():
            for keyword in keywords:
                if keyword in column:
                    scores[domain] += 1.0

    numeric_count = len((dataset_profile or {}).get("numeric_columns", []))
    datetime_count = len((dataset_profile or {}).get("datetime_columns", []))
    if numeric_count and datetime_count:
        for domain in ["sales", "finance", "logistics", "marketing"]:
            scores[domain] += 0.25
    if any("patient" in column or "claim" in column for column in columns):
        scores["healthcare"] += 0.75
    if any("employee" in column or "salary" in column for column in columns):
        scores["hr"] += 0.75

    total = sum(scores.values())
    if not total:
        return {
            "domain": "generic",
            "confidence": 0.35,
            "scores": scores,
            "reasoning": "No strong industry-specific column signals were found, so the dataset is treated as a generic business dataset.",
        }

    normalized = {domain: round(score / total, 4) for domain, score in scores.items()}
    domain = max(normalized.items(), key=lambda item: item[1])[0]
    matched = [column for column in columns if any(keyword in column for keyword in DOMAIN_KEYWORDS[domain])]
    return {
        "domain": domain,
        "confidence": round(normalized[domain], 4),
        "scores": normalized,
        "reasoning": f"Classified as {domain} because matching fields include {', '.join(matched[:5]) or 'business measures'}.",
    }
