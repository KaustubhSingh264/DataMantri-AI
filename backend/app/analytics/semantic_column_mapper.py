from app.services.dataset_profiler import inspect_dataset


def map_semantic_columns(df):
    profile = inspect_dataset(df)
    return {
        semantic_type: [column for column, meta in profile["columns"].items() if meta.get("semantic_type") == semantic_type]
        for semantic_type in {meta.get("semantic_type") for meta in profile["columns"].values()}
    }


__all__ = ["map_semantic_columns"]
