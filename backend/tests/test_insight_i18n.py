import pandas as pd
from app.services.data_profiler import profile_data
from app.services.kpi_engine import generate_kpis
from app.services.insight_engine import generate_insights


def _load_df():
    return pd.read_csv("data/cleaned_electronics_dataset.csv")


def test_insights_have_localized_modes():
    df = _load_df()
    profile = profile_data(df)
    kpis = generate_kpis(df)
    insights = generate_insights(profile, kpis, df)

    assert isinstance(insights, list) and len(insights) > 0
    for ins in insights:
        modes_i18n = ins.get("modes_i18n")
        assert isinstance(modes_i18n, dict), "modes_i18n missing"
        for mode in ("business", "data", "eli5"):
            langs = modes_i18n.get(mode)
            assert isinstance(langs, dict)
            assert "en" in langs and "hi" in langs and "hinglish" in langs
            # ensure localized strings are non-empty
            assert langs["en"] and isinstance(langs["en"], str)
            assert langs["hi"] and isinstance(langs["hi"], str)
            assert langs["hinglish"] and isinstance(langs["hinglish"], str)
