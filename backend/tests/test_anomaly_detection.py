import pandas as pd
from app.services.anomaly_detection import detect_anomalies


def test_detect_anomalies_basic():
    # create series with a clear outlier
    df = pd.DataFrame({"x": [1, 1, 1, 1, 100]})
    # use a lower z-threshold to reliably detect the extreme value in small sample
    out = detect_anomalies(df, numeric_cols=["x"], z_threshold=1.5)
    assert any(d["column"] == "x" and d["anomaly_count"] >= 1 for d in out)
