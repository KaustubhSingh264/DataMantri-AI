import pandas as pd
from app.services.kpi_discovery import discover_kpis


def test_discover_kpis_basic():
    df = pd.DataFrame({
        "order_date": pd.date_range("2020-01-01", periods=5, freq="D"),
        "revenue": [10, 20, 30, 40, 50],
        "product": ["a", "b", "a", "c", "a"],
    })
    profile = {"columns": {"order_date": {"is_date": True}, "revenue": {"is_numeric": True}, "product": {"is_categorical": True}}}
    kpis = {"numeric_stats": {"revenue": {"sum": {"raw_value": 150, "display_value": 150}, "mean": {"raw_value": 30, "display_value": 30}}}, "categorical_stats": {"product": {"top_category": {"raw_value": "a", "display_value": "a"}, "top_category_percentage": {"raw_value": 60, "display_value": 60}}}}
    out = discover_kpis(df, profile, kpis)
    assert "Row Count" in out["discovered_kpis"]
    assert "revenue Total" in out["discovered_kpis"] or "revenue Sum" in out["discovered_kpis"]
