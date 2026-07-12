import re
import pandas as pd
import plotly.express as px


def humanize_label(value: str):
    return str(value or "").replace("_", " ").strip().title()


def get_language_style(language: str) -> str:
    if language == "hi":
        return "hindi"
    if language == "hinglish":
        return "hinglish"
    return "english"


def localize_answer(answer: str, style: str):
    if not answer:
        return answer
    if style == "english":
        return answer
    if answer == NO_INFO:
        return "इस डेटासेट में ऐसी जानकारी उपलब्ध नहीं है।" if style == "hindi" else "Is dataset me aisi information available nahi hai."

    replacements = {
        "revenue": "रेवेन्यू" if style == "hindi" else "revenue",
        "sales": "बिक्री" if style == "hindi" else "sales",
        "profit": "लाभ" if style == "hindi" else "profit",
        "dataset": "डेटासेट" if style == "hindi" else "dataset",
        "rows": "पंक्तियाँ" if style == "hindi" else "rows",
        "columns": "कॉलम" if style == "hindi" else "columns",
        "missing values": "मिसिंग वैल्यू" if style == "hindi" else "missing values",
        "duplicate rows": "डुप्लिकेट पंक्तियाँ" if style == "hindi" else "duplicate rows",
        "highest": "सबसे ऊँचा" if style == "hindi" else "highest",
        "top": "शीर्ष" if style == "hindi" else "top",
        "total": "कुल" if style == "hindi" else "total",
        "average": "औसत" if style == "hindi" else "average",
        "median": "मीडियन" if style == "hindi" else "median",
        "outlier": "आउटलायर" if style == "hindi" else "outlier",
        "forecast": "पूर्वानुमान" if style == "hindi" else "forecast",
        "trend": "ट्रेंड" if style == "hindi" else "trend",
        "confidence": "कॉन्फिडेंस" if style == "hindi" else "confidence",
        "reason": "कारण" if style == "hindi" else "reason",
        "change": "बदलाव" if style == "hindi" else "change",
    }

    localized = answer
    for source, target in replacements.items():
        localized = re.sub(rf"\b{re.escape(source)}\b", target, localized, flags=re.IGNORECASE)

    if style == "hindi":
        localized = re.sub(r"\bNo information\b", "कोई जानकारी नहीं", localized, flags=re.IGNORECASE)
        localized = re.sub(r"\bYour dataset\b", "आपका डेटासेट", localized, flags=re.IGNORECASE)
        localized = re.sub(r"\bYour data\b", "आपका डेटा", localized, flags=re.IGNORECASE)
        localized = re.sub(r"\bPlease\b", "कृपया", localized, flags=re.IGNORECASE)
        localized = re.sub(r"\bIf\b", "अगर", localized, flags=re.IGNORECASE)
    elif style == "hinglish":
        localized = re.sub(r"\bYour dataset\b", "Aapke dataset", localized, flags=re.IGNORECASE)
        localized = re.sub(r"\bPlease\b", "Please", localized, flags=re.IGNORECASE)
    return localized


def answer_data_question(df: pd.DataFrame, profile: dict, question: str, language: str = "en"):
    """Semantic dataset question-answering with robust category and numeric matching."""
    question_lower = question.lower().strip()
    multilingual_terms = {
        "kitne": "how many",
        "kitna": "how much",
        "kul": "total",
        "hamare": "our",
        "hamara": "our",
        "products": "product",
        "grahak": "customer",
        "shahar": "city",
        "shehar": "city",
        "kaunsa": "which",
        "kaun sa": "which",
        "sabse zyada": "top",
        "sabse jyada": "top",
        "sabse kam": "lowest",
        "bikri": "sales",
        "aamdani": "revenue",
        "munafa": "profit",
        "kyun": "why",
        "kyu": "why",
        "कितने": "how many",
        "कितना": "how much",
        "कुल": "total",
        "प्रोडक्ट": "product",
        "उत्पाद": "product",
        "ग्राहक": "customer",
        "शहर": "city",
        "सबसे ज्यादा": "top",
        "बिक्री": "sales",
        "रेवेन्यू": "revenue",
        "मुनाफा": "profit",
        "क्यों": "why",
    }
    for source, target in multilingual_terms.items():
        question_lower = question_lower.replace(source, target)
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category", "string"]).columns.tolist()
    wants_advice = any(term in question_lower for term in ["advice", "advise", "suggest", "recommend", "what should", "action", "improve", "next step"])
    no_info = "There is no such information available in the dataset"
    semantic_roles = {
        "product": ["product", "item", "sku", "article", "sub category", "sub_category", "name"],
        "category": ["category", "type", "segment", "department"],
        "city": ["city", "region", "state", "location", "market", "area", "zone"],
        "customer": ["customer", "client", "buyer", "user"],
        "order": ["order", "invoice", "transaction", "bill"],
        "date": ["date", "time", "month", "year", "day"],
        "revenue": ["revenue", "sales", "sale", "amount", "total", "gmv", "value", "price", "net"],
        "profit": ["profit", "margin", "earning", "income"],
        "quantity": ["quantity", "qty", "units", "stock", "inventory"],
        "discount": ["discount", "coupon", "offer"],
        "status": ["status", "delivery", "state"],
    }
    known_field_terms = list(semantic_roles.keys())

    def first_match(columns, keywords):
        for keyword in keywords:
            for col in columns:
                lower_col = col.lower().replace("_", " ")
                if keyword in lower_col:
                    return col
        return columns[0] if columns else None

    def role_requested(role):
        terms = semantic_roles.get(role, [role])
        return any(term in question_lower for term in [role, *terms])

    def role_available(role):
        terms = semantic_roles.get(role, [role])
        all_columns = [str(col).lower().replace("_", " ") for col in df.columns]
        return any(any(term in column for term in terms) for column in all_columns)

    def column_for_role(role, columns):
        return first_match(columns, semantic_roles.get(role, [role]))

    def requested_metric_role():
        if role_requested("profit"):
            return "profit" if role_available("profit") else "revenue"
        if role_requested("revenue"):
            return "revenue"
        if role_requested("quantity"):
            return "quantity"
        if role_requested("discount"):
            return "discount"
        return None

    def mentioned_column(columns):
        normalized_question = question_lower.replace("_", " ")
        for col in columns:
            normalized_col = col.lower().replace("_", " ")
            if normalized_col in normalized_question:
                return col
        for col in columns:
            parts = [part for part in col.lower().replace("_", " ").split() if len(part) > 2]
            if parts and any(part in normalized_question for part in parts):
                return col
        return None

    def requested_missing_known_field():
        for term in known_field_terms:
            if term == "profit" and role_requested("profit") and role_available("revenue"):
                continue
            if role_requested(term) and not role_available(term):
                return True
        return False

    def build_category_chart(col):
        counts = df[col].value_counts().head(6).reset_index()
        counts.columns = [col, "count"]
        fig = px.bar(
            counts,
            x=col,
            y="count",
            title=f"Top values for {humanize_label(col)}",
            color="count",
            color_continuous_scale="greens",
        )
        return fig.to_json()

    def build_numeric_chart(col):
        fig = px.histogram(df, x=col, nbins=24, title=f"Distribution of {humanize_label(col)}")
        return fig.to_json()

    def describe_column(col):
        if col in numeric_cols:
            summary = df[col].describe()
            return f"{col} has {int(summary['count'])} values, mean {summary['mean']:.2f}, min {summary['min']:.2f}, max {summary['max']:.2f}."
        if col in categorical_cols:
            values = df[col].value_counts().head(3)
            examples = ", ".join([f"'{idx}'" for idx in values.index.tolist()])
            return f"{col} has {int(df[col].nunique())} unique values, top examples are {examples}."
        return f"{col} is included in the dataset."

    def find_category_column():
        if role_requested("product"):
            preferred = column_for_role("product", categorical_cols)
        elif role_requested("city"):
            preferred = column_for_role("city", categorical_cols)
        elif role_requested("customer"):
            preferred = column_for_role("customer", categorical_cols)
        elif role_requested("category"):
            preferred = column_for_role("category", categorical_cols)
        else:
            preferred = None
        preferred = preferred or mentioned_column(categorical_cols) or first_match(categorical_cols, ["product", "category", "item", "name", "type", "region", "segment"])
        return preferred if preferred else (categorical_cols[0] if categorical_cols else None)

    def find_numeric_column():
        metric_role = requested_metric_role()
        preferred = column_for_role(metric_role, numeric_cols) if metric_role else None
        preferred = preferred or mentioned_column(numeric_cols) or first_match(numeric_cols, ["sales", "revenue", "profit", "amount", "total", "value", "price", "quantity", "count", "rating", "score"])
        return preferred if preferred else (numeric_cols[0] if numeric_cols else None)

    def performance_by_category(category_col, value_col, ascending=False):
        grouped = (
            df[[category_col, value_col]]
            .dropna()
            .groupby(category_col)[value_col]
            .sum()
            .sort_values(ascending=ascending)
        )
        if grouped.empty:
            return None
        label = grouped.index[0]
        value = grouped.iloc[0]
        share = (value / grouped.sum() * 100) if grouped.sum() else 0
        return label, value, share

    def top_n_performance(category_col, value_col, n=10, ascending=False):
        grouped = (
            df[[category_col, value_col]]
            .dropna()
            .groupby(category_col)[value_col]
            .sum()
            .sort_values(ascending=ascending)
            .head(n)
        )
        return grouped

    def advice_for(category_col, value_col, top_label=None):
        metric = humanize_label(value_col)
        segment = humanize_label(category_col)
        if top_label is None:
            return (
                f"Next step: compare {segment} by {metric}, quantity, and profit if available. "
                "Double down on high-value segments, investigate weak segments for stock, pricing, or demand issues, "
                "and avoid making decisions from row count alone."
            )
        return (
            f"Advice: treat '{top_label}' as a strong segment, but validate it with margin, repeat demand, and availability. "
            f"If {metric} is revenue-like, protect this segment with inventory and targeted campaigns. "
            "If it is cost-like, check whether high value is actually good or a risk."
        )

    def requested_top_n(default=1):
        import re
        match = re.search(r"top\s+(\d+)", question_lower)
        if match:
            return max(1, min(25, int(match.group(1))))
        return default

    def answer_unique_count(role, label):
        col = column_for_role(role, df.columns)
        if col is None:
            return None
        unique_count = int(df[col].nunique(dropna=True))
        return {
            "answer": f"Your dataset has {unique_count:,} unique {label} based on {humanize_label(col)}.",
            "chart": build_category_chart(col) if col in categorical_cols else None,
        }

    def answer_why_change():
        value_col = find_numeric_column()
        time_candidates = [col for col in df.columns if "date" in col.lower() or "time" in col.lower() or pd.api.types.is_datetime64_any_dtype(df[col])]
        if not value_col or not time_candidates:
            return None
        time_col = time_candidates[0]
        work = df.copy()
        work[time_col] = pd.to_datetime(work[time_col], errors="coerce")
        work[value_col] = pd.to_numeric(work[value_col], errors="coerce")
        work = work.dropna(subset=[time_col, value_col]).sort_values(time_col)
        if len(work) < 4:
            return None
        midpoint = work[time_col].median()
        previous = float(work[work[time_col] <= midpoint][value_col].sum())
        recent = float(work[work[time_col] > midpoint][value_col].sum())
        if previous == 0:
            return None
        change = round((recent - previous) / abs(previous) * 100, 1)
        category_col = find_category_column()
        driver_text = ""
        if category_col and category_col in work.columns:
            before = work[work[time_col] <= midpoint].groupby(category_col)[value_col].sum()
            after = work[work[time_col] > midpoint].groupby(category_col)[value_col].sum()
            delta = (after - before).sort_values()
            if not delta.empty:
                driver = delta.index[0] if change < 0 else delta.index[-1]
                driver_text = f" The biggest segment driver was '{driver}' in {humanize_label(category_col)}."
        direction = "dropped" if change < 0 else "increased"
        action = "Check orders, pricing, discounts, inventory, and weak segments before deciding next action."
        return {
            "answer": f"{humanize_label(value_col)} {direction} by {abs(change)}% between the earlier and later periods.{driver_text} {action}",
            "chart": None,
        }

    category_column = find_category_column()
    numeric_column = find_numeric_column()
    mentioned_category = mentioned_column(categorical_cols)
    mentioned_numeric = mentioned_column(numeric_cols)
    metric_role = requested_metric_role()

    if requested_missing_known_field():
        return {"answer": no_info, "chart": None}

    if any(term in question_lower for term in ["how many", "count", "number of", "total"]) and role_requested("product"):
        result = answer_unique_count("product", "products")
        if result:
            return result
    if any(term in question_lower for term in ["how many", "count", "number of", "total"]) and role_requested("customer"):
        result = answer_unique_count("customer", "customers")
        if result:
            return result
    if any(term in question_lower for term in ["how many", "count", "number of", "total"]) and "order" in question_lower:
        result = answer_unique_count("order", "orders")
        if result:
            return result

    if "why" in question_lower and any(role_requested(role) for role in ["profit", "revenue"]):
        result = answer_why_change()
        if result:
            return result

    underperform_terms = ["underperform", "under performing", "least performing", "lowest performing", "worst performing", "weakest", "bottom performing", "low performing", "poor performing"]
    if any(term in question_lower for term in underperform_terms) or ("least" in question_lower and "perform" in question_lower):
        col = find_category_column()
        value_col = find_numeric_column()
        if col and value_col:
            result = performance_by_category(col, value_col, ascending=True)
            if result:
                label, value, share = result
                return {
                    "answer": (
                        f"The weakest {col.replace('_', ' ')} by total {value_col.replace('_', ' ')} is '{label}'. "
                        f"It contributes {value:.2f}, only {share:.1f}% of the measured total. "
                        "This segment deserves a quality, pricing, availability, or demand review before scaling efforts."
                    ),
                    "chart": build_category_chart(col),
                }
        if col:
            counts = df[col].value_counts()
            worst_category = counts.idxmin()
            worst_count = counts.min()
            exact_column_name = col.replace("_", " ")
            return {
                "answer": f"The least performing {exact_column_name} is '{worst_category}' with only {worst_count} records ({(worst_count / len(df) * 100):.1f}% of the dataset).",
                "chart": build_category_chart(col),
            }
        return {"answer": "No categorical field available to determine the least performing segment.", "chart": None}

    top_terms = ["top", "best", "highest", "strongest", "most successful", "popular", "leading"]
    if any(term in question_lower for term in top_terms) or ("maximum" in question_lower) or ("max" in question_lower):
        if mentioned_category or any(role_requested(role) for role in ["category", "product", "city", "customer", "date"]):
            col = mentioned_category or find_category_column()
            value_col = find_numeric_column()
            top_n = requested_top_n()
            if col and value_col and top_n > 1:
                grouped = top_n_performance(col, value_col, top_n)
                if not grouped.empty:
                    total = grouped.sum()
                    lines = [
                        f"{idx + 1}. {label}: {value:.2f} ({(value / total * 100) if total else 0:.1f}% of the top {len(grouped)} total)"
                        for idx, (label, value) in enumerate(grouped.items())
                    ]
                    best_label = grouped.index[0]
                    answer = (
                        f"Top {len(grouped)} {humanize_label(col)} values by total {humanize_label(value_col)}:\n"
                        + "\n".join(lines)
                    )
                    if wants_advice:
                        answer += f"\n\n{advice_for(col, value_col, best_label)}"
                    return {"answer": answer, "chart": build_category_chart(col)}
            if col and not mentioned_numeric and not metric_role:
                counts = df[col].value_counts().head(top_n if top_n > 1 else 1)
                if counts.empty:
                    return {"answer": no_info, "chart": None}
                if top_n > 1:
                    lines = [
                        f"{idx + 1}. {label}: {count} rows ({(count / len(df) * 100):.1f}%)"
                        for idx, (label, count) in enumerate(counts.items())
                    ]
                    return {
                        "answer": f"Top {len(counts)} {humanize_label(col)} values by row count:\n" + "\n".join(lines),
                        "chart": build_category_chart(col),
                    }
                top_value = counts.index[0]
                top_count = counts.iloc[0]
                return {
                    "answer": f"The top {humanize_label(col)} is '{top_value}' with {top_count} rows ({(top_count / len(df) * 100):.1f}% of the dataset).",
                    "chart": build_category_chart(col),
                }
            if col and value_col:
                result = performance_by_category(col, value_col)
                if result:
                    label, value, share = result
                    metric_label = "revenue" if metric_role == "revenue" else humanize_label(value_col)
                    advice = f" {advice_for(col, value_col, label)}" if wants_advice else ""
                    return {
                        "answer": (
                            f"The leading {humanize_label(col)} by total {metric_label} is '{label}'. "
                            f"It contributes {value:.2f}, representing {share:.1f}% of the measured total. "
                            "This is a strong segment and a candidate for deeper retention, inventory, or campaign analysis."
                            f"{advice}"
                        ),
                        "chart": build_category_chart(col),
                    }
            if col:
                counts = df[col].value_counts()
                best_category = counts.idxmax()
                best_count = counts.max()
                exact_column_name = col.replace("_", " ")
                advice = f" {advice_for(col, numeric_column)}" if wants_advice and numeric_column else ""
                return {
                    "answer": f"The top {humanize_label(exact_column_name)} is '{best_category}' with {best_count} entries ({(best_count / len(df) * 100):.1f}% of the dataset).{advice}",
                    "chart": build_category_chart(col),
                }
        if numeric_column:
            if not mentioned_numeric and any(word in question_lower for word in ["city", "product", "customer", "category", "date"]):
                return {"answer": no_info, "chart": None}
            max_val = df[numeric_column].max()
            return {"answer": f"The highest value is {max_val:.2f} in {humanize_label(numeric_column)}.", "chart": None}
        return {"answer": "I couldn't identify a top segment or numeric leader in this dataset.", "chart": None}

    if any(term in question_lower for term in ["average", "mean", "avg", "median"]):
        col = numeric_column
        if col:
            avg = df[col].mean()
            median = df[col].median()
            return {
                "answer": (
                    f"The average value for {humanize_label(col)} is {avg:.2f}, while the median is {median:.2f}. "
                    f"The gap between them helps indicate whether a few unusually high or low values are influencing the overall picture."
                ),
                "chart": build_numeric_chart(col),
            }
        return {"answer": "No numeric field available to calculate averages.", "chart": None}

    if any(term in question_lower for term in ["most common", "popular", "frequent", "top", "mode"]):
        col = find_category_column()
        if col:
            top_value = df[col].mode().iloc[0]
            top_count = (df[col] == top_value).sum()
            exact_column_name = col.replace("_", " ")
            return {
                "answer": f"The most common {humanize_label(exact_column_name)} is '{top_value}' with {top_count} occurrences ({(top_count / len(df) * 100):.1f}% of all rows).",
                "chart": build_category_chart(col),
            }
        return {"answer": "No categorical field available for frequency analysis.", "chart": None}

    if any(term in question_lower for term in ["outlier", "extreme", "anomaly", "anomalies"]):
        col = numeric_column
        if col:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers = df[(df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR)]
            if len(outliers) > 0:
                return {"answer": f"Found {len(outliers)} outliers in {humanize_label(col)} ({(len(outliers) / len(df) * 100):.1f}% of rows).", "chart": None}
            return {"answer": f"No significant outliers detected in {humanize_label(col)}.", "chart": None}
        return {"answer": "No numeric field available to detect outliers.", "chart": None}

    if any(term in question_lower for term in ["how many", "total", "rows", "count"]):
        return {
            "answer": (
                f"Your dataset contains {len(df)} rows and {len(df.columns)} columns. "
                f"It includes {len(numeric_cols)} numeric fields, {len(categorical_cols)} categorical fields, "
                f"and {len(df.select_dtypes(include=['datetime64[ns]', 'datetime64[ns, UTC]']).columns)} date/time fields."
            ),
            "chart": None,
        }

    if any(term in question_lower for term in ["column", "feature", "fields"]):
        return {"answer": f"Your dataset has {len(df.columns)} columns, including {len(numeric_cols)} numeric and {len(categorical_cols)} categorical fields.", "chart": None}

    if any(term in question_lower for term in ["quality", "missing", "null", "duplicate", "duplicates"]):
        missing_pct = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
        duplicates = df.duplicated().sum()
        quality_label = "healthy" if missing_pct < 5 and duplicates == 0 else "needs attention"
        return {
            "answer": (
                f"Data quality looks {quality_label}: {missing_pct:.1f}% of cells are missing and there are {duplicates} duplicate rows "
                f"({(duplicates / len(df) * 100):.1f}% duplication). "
                "For reliable insights, handle duplicates first, then fill or review high-missing columns."
            ),
            "chart": None,
        }

    if wants_advice:
        col = find_category_column()
        value_col = find_numeric_column()
        if col and value_col:
            result = performance_by_category(col, value_col)
            if result:
                label, value, share = result
                return {
                    "answer": (
                        f"Suggestion: focus first on '{label}' in {humanize_label(col)} because it contributes "
                        f"{value:.2f}, about {share:.1f}% of the measured {humanize_label(value_col)}. "
                        f"{advice_for(col, value_col, label)}"
                    ),
                    "chart": build_category_chart(col),
                }
        if col:
            counts = df[col].value_counts()
            if not counts.empty:
                label = counts.index[0]
                return {
                    "answer": (
                        f"Suggestion: start by reviewing '{label}' in {humanize_label(col)} because it appears most often. "
                        "Then compare it with revenue, quantity, profit, and stock availability before making a business decision."
                    ),
                    "chart": build_category_chart(col),
                }
        return {"answer": no_info, "chart": None}

    # Fallback summary with context to keep the assistant helpful.
    top_summary = []
    if category_column:
        popular = df[category_column].value_counts().head(1)
        if not popular.empty:
            top_summary.append(f"Top {humanize_label(category_column)} is '{popular.index[0]}'")
    if numeric_column:
        top_summary.append(f"leading numeric field is {humanize_label(numeric_column)}")

    fallback_message = (
        no_info
    )
    return {"answer": fallback_message, "chart": None}
