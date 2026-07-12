import pandas as pd
from app.services.kpi_correlation import top_correlations


def test_top_correlations_basic():
    df = pd.DataFrame({
        "a": [1, 2, 3, 4, 5],
        "b": [2, 4, 6, 8, 10],
        "c": [5, 3, 6, 2, 1],
    })
    out = top_correlations(df, numeric_cols=["a", "b", "c"], top_n=5, threshold=0.5)
    # expect a-b to be strongly correlated
    assert any((o["col_a"] == "a" and o["col_b"] == "b") or (o["col_a"] == "b" and o["col_b"] == "a") for o in out)
