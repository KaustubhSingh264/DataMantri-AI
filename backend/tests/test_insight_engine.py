import pandas as pd
from app.services.data_profiler import profile_data
from app.services.kpi_engine import generate_kpis
from app.services.insight_engine import generate_insights


def test_generate_insights_on_sample_dataset():
    # prefer backend/data if available, else fallback to repo-level data/
    from pathlib import Path
    candidates = [Path("backend/data/cleaned_electronics_dataset.csv"), Path("data/cleaned_electronics_dataset.csv")]
    path = next((str(p) for p in candidates if p.exists()), None)
    assert path is not None, "Sample dataset not found in backend/data or data/"
    df = pd.read_csv(path)

    profile = profile_data(df)
    kpis = generate_kpis(df)
    insights = generate_insights(profile, kpis, df)

    # Minimum expectations
    assert isinstance(insights, list)
    assert len(insights) >= 6, f"Expected at least 6 insights, got {len(insights)}"

    titles = [ins.get("title", "") for ins in insights]
    assert any("Executive summary" in t or "Executive" in t for t in titles), "Missing executive summary insight"
