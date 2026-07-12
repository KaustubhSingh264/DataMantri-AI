from typing import Dict, Any
import pandas as pd


def infer_domain(profile: Dict[str, Any], df) -> Dict[str, Any]:
    """
    Infer dataset domain using simple heuristics on column names and types.
    Returns a dict: {"domain": str, "scores": {domain:score, ...}}
    """
    cols = [c.lower().replace("_", " ") for c in (list(df.columns) if df is not None else [])]
    scores = {
        "retail": 0.0,
        "ecommerce": 0.0,
        "sales": 0.0,
        "finance": 0.0,
        "hr": 0.0,
        "healthcare": 0.0,
        "banking": 0.0,
        "marketing": 0.0,
        "operations": 0.0,
        "generic": 0.0,
    }

    keywords = {
        "retail": ["store", "product", "sku", "inventory", "category", "price", "discount"],
        "ecommerce": ["cart", "checkout", "conversion", "session", "online", "product", "order"],
        "sales": ["revenue", "sales", "lead", "pipeline", "deal", "quota", "order", "customer"],
        "finance": ["expense", "cost", "profit", "margin", "cash", "budget", "invoice", "amount"],
        "hr": ["employee", "salary", "hire", "attrition", "department"],
        "healthcare": ["patient", "diagnosis", "treatment", "admission", "doctor", "claim"],
        "banking": ["transaction", "balance", "account", "txn", "loan", "deposit", "credit"],
        "marketing": ["campaign", "click", "impression", "lead", "channel", "ctr", "cpc"],
        "operations": ["ticket", "sla", "throughput", "defect", "machine", "delivery", "capacity"],
    }

    for col in cols:
        for domain, keys in keywords.items():
            for k in keys:
                if k in col:
                    scores[domain] += 1.0

    try:
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist() if df is not None else []
        categorical_cols = df.select_dtypes(include=["object", "category", "string"]).columns.tolist() if df is not None else []
        if any("date" in col or "time" in col for col in cols) and numeric_cols:
            scores["sales"] += 0.5
            scores["operations"] += 0.25
        if len(categorical_cols) >= 2 and any(any(term in col for term in ["product", "category", "sku"]) for col in cols):
            scores["retail"] += 0.75
            scores["ecommerce"] += 0.5
        if any(any(term in col for term in ["amount", "balance", "transaction"]) for col in cols):
            scores["finance"] += 0.4
            scores["banking"] += 0.4
    except Exception:
        pass

    # simple normalization
    total = sum(scores.values())
    if total > 0:
        for k in scores:
            scores[k] = round(scores[k] / total, 4)
        domain = max(scores.items(), key=lambda x: x[1])[0]
    else:
        domain = "generic"
        scores["generic"] = 1.0

    confidence = scores.get(domain, 0.0)
    return {"domain": domain, "confidence": confidence, "scores": scores}
