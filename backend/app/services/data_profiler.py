import pandas as pd


def profile_data(df: pd.DataFrame):
    profile = {}

    for col in df.columns:
        if df[col].dtype == "object" and any(term in col.lower() for term in ["date", "time", "created", "updated"]):
            try:
                parsed = pd.to_datetime(df[col], errors="coerce", format="mixed")
            except TypeError:
                parsed = pd.to_datetime(df[col], errors="coerce")
            if parsed.notna().mean() >= 0.8:
                df[col] = parsed

    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category', 'string']).columns.tolist()
    datetime_cols = df.select_dtypes(include=['datetime64[ns]', 'datetime64[ns, UTC]']).columns.tolist()

    profile['numeric_columns'] = numeric_cols
    profile['categorical_columns'] = categorical_cols
    profile['datetime_columns'] = datetime_cols

    profile['shape'] = {
        'rows': df.shape[0],
        'columns': df.shape[1],
    }

    missing_values = df.isnull().sum().to_dict()
    profile['missing_values'] = missing_values
    profile['missing_percent'] = {
        col: round((value / max(len(df), 1)) * 100, 1)
        for col, value in missing_values.items()
    }

    duplicated_rows = int(df.duplicated().sum())
    profile['duplicate_rows'] = duplicated_rows
    profile['duplicate_percent'] = round((duplicated_rows / max(len(df), 1)) * 100, 1)

    profile['summary_stats'] = df[numeric_cols].describe().to_dict() if numeric_cols else {}

    profile['category_summary'] = {}
    for col in categorical_cols:
        counts = df[col].value_counts(normalize=True) * 100
        if not counts.empty:
            profile['category_summary'][col] = {
                'top_value': counts.index[0],
                'top_share': round(counts.iloc[0], 1),
                'unique_values': int(df[col].nunique()),
            }
        else:
            profile['category_summary'][col] = {
                'top_value': None,
                'top_share': 0,
                'unique_values': 0,
            }

    return profile
