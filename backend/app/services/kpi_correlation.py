from typing import List, Dict, Any, Optional, Tuple
import pandas as pd


def top_correlations(df: pd.DataFrame, numeric_cols: Optional[List[str]] = None, top_n: int = 10, threshold: float = 0.5) -> List[Dict[str, Any]]:
    """Compute top pairwise Pearson correlations among numeric columns.

    Returns a list of {col_a, col_b, corr} ordered by absolute correlation.
    """
    if numeric_cols is None:
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if len(numeric_cols) < 2:
        return []

    sub = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
    corr = sub.corr(method="pearson")
    pairs: List[Tuple[str, str, float]] = []
    for i, a in enumerate(corr.columns):
        for j, b in enumerate(corr.columns):
            if j <= i:
                continue
            val = corr.iloc[i, j]
            if pd.isna(val):
                continue
            pairs.append((a, b, float(val)))

    # sort by absolute value desc
    pairs.sort(key=lambda t: abs(t[2]), reverse=True)
    out: List[Dict[str, Any]] = []
    for a, b, v in pairs[:top_n]:
        if abs(v) < threshold:
            continue
        out.append({"col_a": a, "col_b": b, "corr": round(v, 4)})

    return out
