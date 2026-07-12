import pandas as pd
from app.services.kpi_trends import detect_trends


def test_detect_trends_simple():
    # create simple increasing series
    df = pd.DataFrame({
        "date": pd.date_range("2020-01-01", periods=10, freq="D"),
        "value": list(range(10)),
    })
    profile = {"columns": {"date": {"is_date": True}, "value": {"is_numeric": True}}}
    out = detect_trends(df, profile, time_col="date", numeric_cols=["value"])
    assert "value" in out
    assert isinstance(out["value"].get("slope_per_day"), float)
