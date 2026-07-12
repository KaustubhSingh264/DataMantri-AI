from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple
import re

import pandas as pd


def _quality_score(df: pd.DataFrame) -> float:
    if df is None or df.empty or len(df.columns) == 0:
        return 0.0
    total_cells = max(1, int(len(df) * len(df.columns)))
    missing_rate = float(df.isna().sum().sum()) / total_cells
    duplicate_rate = float(df.duplicated().sum()) / max(1, len(df))
    empty_column_rate = float(sum(df[col].isna().all() for col in df.columns)) / max(1, len(df.columns))
    penalty = missing_rate * 45 + duplicate_rate * 35 + empty_column_rate * 20
    return round(max(0.0, min(100.0, 100 - penalty)), 2)


@dataclass
class DataCleaner:
    df: pd.DataFrame
    report: Dict[str, Any] = field(default_factory=dict)
    errors: List[Dict[str, str]] = field(default_factory=list)

    def __post_init__(self):
        self.cleaned = self.df.copy()
        self.report = {
            "rows_before": int(len(self.cleaned)),
            "columns_before": int(len(self.cleaned.columns)),
            "rows_after": int(len(self.cleaned)),
            "columns_after": int(len(self.cleaned.columns)),
            "rows_removed": 0,
            "duplicates_removed": 0,
            "missing_filled": 0,
            "numeric_converted": 0,
            "dates_converted": 0,
            "text_trimmed": 0,
            "outliers_detected": 0,
            "outliers_capped": 0,
            "quality_before": _quality_score(self.cleaned),
            "quality_after": _quality_score(self.cleaned),
            "steps": [],
            "errors": self.errors,
        }

    def _run_step(self, name: str, fn):
        try:
            fn()
            self.report["steps"].append({"name": name, "status": "ok"})
        except Exception as exc:
            self.errors.append({"step": name, "error": str(exc)})
            self.report["steps"].append({"name": name, "status": "failed", "error": str(exc)})

    def normalize_columns(self):
        seen = {}
        rename_map = {}
        for column in self.cleaned.columns:
            base = re.sub(r"[^0-9a-zA-Z]+", "_", str(column).strip().lower()).strip("_") or "column"
            count = seen.get(base, 0)
            seen[base] = count + 1
            rename_map[column] = base if count == 0 else f"{base}_{count + 1}"
        self.cleaned = self.cleaned.rename(columns=rename_map)
        self.report["columns_renamed"] = sum(1 for old, new in rename_map.items() if old != new)

    def clean_text(self):
        text_cols = self.cleaned.select_dtypes(include=["object", "string", "category"]).columns
        for column in text_cols:
            self.cleaned[column] = self.cleaned[column].map(lambda value: value.strip() if isinstance(value, str) else value)
        self.report["text_trimmed"] = int(len(text_cols))

    def clean_numeric(self):
        converted = 0
        for column in list(self.cleaned.columns):
            series = self.cleaned[column]
            if pd.api.types.is_numeric_dtype(series):
                continue
            non_null = series.dropna()
            if non_null.empty:
                continue
            cleaned_text = (
                non_null.astype(str)
                .str.replace(",", "", regex=False)
                .str.replace("₹", "", regex=False)
                .str.replace("$", "", regex=False)
                .str.replace("%", "", regex=False)
                .str.strip()
            )
            numeric_candidate = pd.to_numeric(cleaned_text, errors="coerce")
            if numeric_candidate.notna().mean() >= 0.8:
                self.cleaned[column] = pd.to_numeric(
                    self.cleaned[column].astype(str)
                    .str.replace(",", "", regex=False)
                    .str.replace("₹", "", regex=False)
                    .str.replace("$", "", regex=False)
                    .str.replace("%", "", regex=False)
                    .str.strip(),
                    errors="coerce",
                )
                converted += 1
        self.report["numeric_converted"] = converted

    def clean_dates(self):
        converted = 0
        for column in list(self.cleaned.columns):
            if pd.api.types.is_datetime64_any_dtype(self.cleaned[column]):
                continue
            lower = str(column).lower()
            if not any(token in lower for token in ["date", "time", "created", "updated", "month", "year"]):
                continue
            try:
                parsed = pd.to_datetime(self.cleaned[column], errors="coerce", format="mixed")
            except TypeError:
                parsed = pd.to_datetime(self.cleaned[column], errors="coerce")
            if parsed.notna().mean() >= 0.6:
                self.cleaned[column] = parsed
                converted += 1
        self.report["dates_converted"] = converted

    def remove_duplicates(self):
        before = len(self.cleaned)
        self.cleaned = self.cleaned.drop_duplicates()
        removed = before - len(self.cleaned)
        self.report["duplicates_removed"] = int(removed)
        self.report["rows_removed"] += int(removed)

    def fill_missing(self):
        before_missing = int(self.cleaned.isna().sum().sum())
        for column in self.cleaned.columns:
            if not self.cleaned[column].isna().any():
                continue
            if pd.api.types.is_numeric_dtype(self.cleaned[column]):
                fill_value = self.cleaned[column].median()
                self.cleaned[column] = self.cleaned[column].fillna(0 if pd.isna(fill_value) else fill_value)
            elif pd.api.types.is_datetime64_any_dtype(self.cleaned[column]):
                mode = self.cleaned[column].mode(dropna=True)
                self.cleaned[column] = self.cleaned[column].fillna(mode.iloc[0] if not mode.empty else pd.Timestamp("1970-01-01"))
            else:
                mode = self.cleaned[column].mode(dropna=True)
                self.cleaned[column] = self.cleaned[column].fillna(mode.iloc[0] if not mode.empty else "Unknown")
        after_missing = int(self.cleaned.isna().sum().sum())
        self.report["missing_filled"] = max(0, before_missing - after_missing)

    def detect_outliers(self):
        detected = 0
        capped = 0
        for column in self.cleaned.select_dtypes(include=["number"]).columns:
            if "id" in str(column).lower():
                continue
            series = pd.to_numeric(self.cleaned[column], errors="coerce")
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            if pd.isna(iqr) or iqr == 0:
                continue
            lower = q1 - 3 * iqr
            upper = q3 + 3 * iqr
            mask = (series < lower) | (series > upper)
            count = int(mask.sum())
            detected += count
            if 0 < count <= max(10, int(len(series) * 0.02)):
                self.cleaned.loc[mask & (series < lower), column] = lower
                self.cleaned.loc[mask & (series > upper), column] = upper
                capped += count
        self.report["outliers_detected"] = detected
        self.report["outliers_capped"] = capped

    def calculate_quality_score(self):
        self.report["rows_after"] = int(len(self.cleaned))
        self.report["columns_after"] = int(len(self.cleaned.columns))
        self.report["quality_after"] = _quality_score(self.cleaned)

    def clean(self) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        for name, fn in [
            ("normalize_columns", self.normalize_columns),
            ("clean_text", self.clean_text),
            ("clean_numeric", self.clean_numeric),
            ("clean_dates", self.clean_dates),
            ("remove_duplicates", self.remove_duplicates),
            ("fill_missing", self.fill_missing),
            ("detect_outliers", self.detect_outliers),
            ("calculate_quality_score", self.calculate_quality_score),
        ]:
            self._run_step(name, fn)
        self.cleaned = self.cleaned.convert_dtypes()
        self.calculate_quality_score()
        return self.cleaned, self.report


def clean_dataset(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    return DataCleaner(df).clean()
