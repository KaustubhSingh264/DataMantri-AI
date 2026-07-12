import pandas as pd
from app.services.data_profiler import profile_data
from app.services.kpi_engine import generate_kpis
from app.services.insight_engine import generate_insights


def _load_df():
    return pd.read_csv("data/cleaned_electronics_dataset.csv")


def test_insights_have_required_fields_and_modes():
    df = _load_df()
    profile = profile_data(df)
    kpis = generate_kpis(df)
    insights = generate_insights(profile, kpis, df)

    assert isinstance(insights, list) and len(insights) > 0

    required = [
        "observation",
        "reasoning",
        "impact",
        "action",
        "confidence",
        "confidence_score",
        "business_impact_score",
        "importance",
        "priority",
        "modes",
    ]

    for ins in insights:
        for r in required:
            assert r in ins, f"Missing {r} in insight {ins.get('title')}"

        # modes should include business/data/eli5
        modes = ins.get("modes") or {}
        assert "business" in modes and "data" in modes and "eli5" in modes
