import pandas as pd
from app.services.data_profiler import profile_data
from app.services.kpi_engine import generate_kpis
from app.services.insight_engine import generate_insights
from app.services.recommendation_engine import generate_recommendations


def _load_df():
    return pd.read_csv("data/cleaned_electronics_dataset.csv")


def test_recommendation_schema_and_no_generic_phrases():
    df = _load_df()
    profile = profile_data(df)
    kpis = generate_kpis(df)
    insights = generate_insights(profile, kpis, df)
    recs = generate_recommendations(profile, insights, df)

    assert isinstance(recs, list)

    # If there are no recommendations (allowed), test passes as long as type is list.
    if not recs:
        return

    forbidden = [
        "check the numbers",
        "check numbers",
        "please verify",
        "check for",
        "check the data",
        "verify the data"
    ]

    for r in recs:
        assert isinstance(r, dict)
        for key in (
            "title",
            "observation",
            "evidence",
            "business_impact",
            "recommended_action",
            "expected_outcome",
            "priority",
            "confidence",
        ):
            assert key in r, f"Missing required key: {key} in recommendation {r}"

        assert isinstance(r["evidence"], list)
        assert len(r["evidence"]) >= 1

        assert r["priority"] in ("High", "Medium", "Low")
        assert isinstance(r["confidence"], int) and 0 <= r["confidence"] <= 100

        text = " ".join([str(r.get(k, "")).lower() for k in ("title", "observation", "recommended_action")])
        for phrase in forbidden:
            assert phrase not in text, f"Found forbidden phrase '{phrase}' in recommendation: {r.get('title')}"
