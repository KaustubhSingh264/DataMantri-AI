import re
from typing import Any

import pandas as pd

from app.services.qa_engine import answer_data_question, humanize_label, localize_answer
from app.services.session_memory import get_recent_context


NO_INFO = "There is no such information available in the dataset"

HINGLISH_TERMS = {
    "sabse profitable": "top profit",
    "sabse zyada": "top",
    "zyada": "highest",
    "kam": "low",
    "kaunsa": "which",
    "kaun sa": "which",
    "kaun hai": "which",
    "batao": "tell",
    "samjhao": "explain",
    "mujhe": "me",
    "mera": "my",
    "meri": "my",
    "kpi batao": "explain kpi",
    "kpis batao": "explain kpi",
    "business summary": "business summary",
    "sales prediction": "forecast sales",
    "profit kyu": "why profit",
    "kyu": "why",
    "shehar": "city",
    "grahak": "customer",
    "utpaad": "product",
    "bikri": "sales",
    "munafa": "profit",
    "aamdani": "revenue",
}

DEVANAGARI_TERMS = {
    "सबसे profitable": "top profit",
    "सबसे ज्यादा": "top",
    "कौनसा": "which",
    "कौन सा": "which",
    "बताओ": "tell",
    "समझाओ": "explain",
    "मेरा": "my",
    "मेरी": "my",
    "किस city": "city",
    "शहर": "city",
    "ग्राहक": "customer",
    "प्रोडक्ट": "product",
    "उत्पाद": "product",
    "बिक्री": "sales",
    "मुनाफा": "profit",
    "रेवेन्यू": "revenue",
    "आमदनी": "revenue",
    "क्यों": "why",
}


def normalize_multilingual_query(query: str) -> str:
    normalized = f" {query.lower().strip()} "
    for source, target in {**HINGLISH_TERMS, **DEVANAGARI_TERMS}.items():
        normalized = normalized.replace(source.lower(), target)
    return re.sub(r"\s+", " ", normalized).strip()


def detect_language(query: str, language_hint: str | None = None) -> str:
    query_lower = query.lower()
    if language_hint in {"en", "hi", "hinglish"}:
        return {"en": "en-US", "hi": "hi-IN", "hinglish": "hi-IN"}[language_hint]
    if "english" in query_lower or "angrezi" in query_lower:
        return "en-US"
    if "hindi" in query_lower or "हिंदी" in query_lower:
        return "hi-IN"
    if "hinglish" in query_lower:
        return "hi-IN"
    if re.search(r"[\u0900-\u097F]", query):
        return "hi-IN"
    hinglish_markers = ["mera", "meri", "kaunsa", "kaun", "batao", "kyu", "zyada", "kam", "mujhe"]
    if any(marker in query.lower() for marker in hinglish_markers):
        return "hi-IN"
    if language_hint:
        return language_hint
    return "en-US"


def response_style(query: str, detected_language: str, language_hint: str | None = None):
    query_lower = query.lower()
    if language_hint == "en":
        return "english"
    if language_hint == "hi":
        return "hindi"
    if language_hint == "hinglish":
        return "hinglish"
    if "hinglish" in query_lower:
        return "hinglish"
    if "hindi" in query_lower or "हिंदी" in query_lower or re.search(r"[\u0900-\u097F]", query):
        return "hindi"
    if detected_language.startswith("hi"):
        return "hinglish"
    return "english"


def get_numeric_columns(df: pd.DataFrame):
    return df.select_dtypes(include=["number"]).columns.tolist()


def get_category_columns(df: pd.DataFrame):
    return df.select_dtypes(include=["object", "category", "string"]).columns.tolist()


def choose_column(columns: list[str], keywords: list[str]):
    for keyword in keywords:
        for column in columns:
            if keyword in column.lower().replace("_", " "):
                return column
    return columns[0] if columns else None


def format_value(value: Any) -> str:
    if isinstance(value, (int, float)) and not pd.isna(value):
        if abs(value) >= 100000:
            return f"{value / 100000:.2f} lakh"
        return f"{value:,.2f}"
    return str(value)


def localized_label(value: str, style: str) -> str:
    label = humanize_label(value)
    if style == "hindi":
        replacements = {
            "Total Amount": "कुल राशि",
            "Amount": "राशि",
            "Product": "उत्पाद",
            "Product Name": "उत्पाद नाम",
            "City": "शहर",
            "Category": "श्रेणी",
            "Customer": "ग्राहक",
            "Customer ID": "ग्राहक ID",
            "Date": "तारीख",
            "Order Date": "ऑर्डर तारीख",
            "Revenue": "रेवेन्यू",
            "Sales": "बिक्री",
            "Profit": "लाभ",
            "Quantity": "मात्रा",
            "Price": "कीमत",
            "Count": "गिनती",
        }
        for source, target in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
            label = label.replace(source, target)
        return label
    if style == "hinglish":
        return label.lower()
    return label


async def polish_answer_with_llm(user_query: str, grounded_answer: str, style: str, df: pd.DataFrame):
    return grounded_answer


def explain_kpis(df: pd.DataFrame, profile: dict, kpis: dict, style: str = "english") -> str:
    rows = profile.get("shape", {}).get("rows", len(df))
    columns = profile.get("shape", {}).get("columns", len(df.columns))
    numeric_cols = get_numeric_columns(df)
    category_cols = get_category_columns(df)
    revenue_col = choose_column(numeric_cols, ["revenue", "sales", "amount", "total", "price", "profit"])
    city_col = choose_column(category_cols, ["city", "region", "state"])
    product_col = choose_column(category_cols, ["product", "item", "name", "category"])

    if style == "hindi":
        lines = [f"आपके डेटासेट में {rows:,} रिकॉर्ड और {columns} कॉलम हैं।"]
    elif style == "hinglish":
        lines = [f"Aapke dataset mein {rows:,} records aur {columns} columns hain."]
    else:
        lines = [f"Your dataset has {rows:,} records across {columns} columns."]
    if revenue_col:
        total_value = pd.to_numeric(df[revenue_col], errors="coerce").sum()
        metric = localized_label(revenue_col, style)
        if style == "hindi":
            lines.append(f"{metric} लगभग {format_value(total_value)} है।")
        elif style == "hinglish":
            lines.append(f"{metric} lagbhag {format_value(total_value)} hai.")
        else:
            prefix = "" if metric.lower().startswith("total") else "Total "
            lines.append(f"{prefix}{metric} is about {format_value(total_value)}.")
    if city_col and revenue_col:
        grouped = df.groupby(city_col)[revenue_col].sum().sort_values(ascending=False)
        if not grouped.empty:
            top_city = grouped.index[0]
            share = grouped.iloc[0] / grouped.sum() * 100 if grouped.sum() else 0
            city_label = localized_label(city_col, style)
            if style == "hindi":
                lines.append(f"{city_label} में {top_city} सबसे मजबूत है और कुल मापे गए मूल्य का करीब {share:.1f}% योगदान देता है।")
            elif style == "hinglish":
                lines.append(f"{city_label} mein {top_city} sabse strong hai aur measured value ka lagbhag {share:.1f}% contribute karta hai.")
            else:
                lines.append(f"{top_city} is your strongest {humanize_label(city_col)}, contributing nearly {share:.1f}% of measured value.")
    if product_col and revenue_col:
        grouped = df.groupby(product_col)[revenue_col].sum().sort_values(ascending=False)
        if not grouped.empty:
            product_label = localized_label(product_col, style)
            if style == "hindi":
                lines.append(f"आपका प्रमुख {product_label} {grouped.index[0]} है।")
            elif style == "hinglish":
                lines.append(f"Aapka leading {product_label} {grouped.index[0]} hai.")
            else:
                lines.append(f"Your leading {humanize_label(product_col)} is {grouped.index[0]}.")

    missing_total = sum(profile.get("missing_values", {}).values()) if profile else int(df.isna().sum().sum())
    duplicate_rows = profile.get("duplicate_rows", int(df.duplicated().sum())) if profile else int(df.duplicated().sum())
    if missing_total or duplicate_rows:
        if style == "hindi":
            lines.append(f"डेटा क्वालिटी पर ध्यान चाहिए: {missing_total} मिसिंग वैल्यू और {duplicate_rows} डुप्लिकेट पंक्तियाँ निर्णयों को प्रभावित कर सकती हैं।")
        elif style == "hinglish":
            lines.append(f"Data quality par attention chahiye: {missing_total} missing values aur {duplicate_rows} duplicate rows decisions ko affect kar sakti hain.")
        else:
            lines.append(f"Data quality needs attention: {missing_total} missing values and {duplicate_rows} duplicate rows can affect decisions.")
    else:
        if style == "hindi":
            lines.append("डेटा क्वालिटी मजबूत दिख रही है; कोई बड़ी मिसिंग वैल्यू या डुप्लिकेट पंक्ति समस्या नहीं दिखती।")
        elif style == "hinglish":
            lines.append("Data quality strong lag rahi hai; koi obvious missing-value ya duplicate-row blocker nahi dikh raha.")
        else:
            lines.append("Data quality looks strong, with no obvious missing-value or duplicate-row blocker.")
    return " ".join(lines)


def explain_profit_change(df: pd.DataFrame) -> str:
    numeric_cols = get_numeric_columns(df)
    date_cols = [column for column in df.columns if "date" in column.lower() or pd.api.types.is_datetime64_any_dtype(df[column])]
    profit_col = choose_column(numeric_cols, ["profit", "margin", "revenue", "sales", "amount", "total"])
    if not profit_col or not date_cols:
        return NO_INFO

    date_col = date_cols[0]
    work = df[[date_col, profit_col] + get_category_columns(df)[:2]].copy()
    work[date_col] = pd.to_datetime(work[date_col], errors="coerce")
    work[profit_col] = pd.to_numeric(work[profit_col], errors="coerce")
    work = work.dropna(subset=[date_col, profit_col]).sort_values(date_col)
    if len(work) < 6:
        return "There is not enough historical data to explain the profit trend confidently."

    midpoint = work[date_col].median()
    previous = work[work[date_col] <= midpoint][profit_col].sum()
    recent = work[work[date_col] > midpoint][profit_col].sum()
    if previous == 0:
        return NO_INFO

    change = (recent - previous) / abs(previous) * 100
    direction = "increased" if change >= 0 else "decreased"
    reason = ""
    category_col = choose_column(get_category_columns(work), ["city", "region", "category", "product", "segment"])
    if category_col:
        previous_group = work[work[date_col] <= midpoint].groupby(category_col)[profit_col].sum()
        recent_group = work[work[date_col] > midpoint].groupby(category_col)[profit_col].sum()
        deltas = (recent_group - previous_group).sort_values()
        if not deltas.empty:
            weakest = deltas.index[0] if change < 0 else deltas.index[-1]
            reason = f" The biggest segment movement came from {weakest}."

    if change < 0:
        return f"{humanize_label(profit_col)} decreased by about {abs(change):.1f}% in the latest period.{reason} Review pricing, discounts, demand, and inventory for the weakest segment first."
    return f"{humanize_label(profit_col)} increased by about {change:.1f}% in the latest period.{reason} Keep protecting the segment that is driving this growth."


async def handle_business_query(transcript, session, df, profile, kpis, language_hint=None):
    clean_transcript = (transcript or "").strip()
    normalized_query = normalize_multilingual_query(clean_transcript)
    detected_language = detect_language(clean_transcript, language_hint)
    style = response_style(clean_transcript, detected_language, language_hint)
    recent_context = get_recent_context(session)

    if not clean_transcript:
        answer_text = "Please ask a business question after uploading your data."
        return localize_answer(answer_text, style), {"language": detected_language, "style": style}

    if any(term in normalized_query for term in ["explain kpi", "kpi", "business summary", "summary", "health", "important metric"]):
        answer_text = explain_kpis(df, profile, kpis, style)
        answer_text = await polish_answer_with_llm(clean_transcript, answer_text, style, df)
        return answer_text, {"intent": "kpi_summary", "language": detected_language, "style": style}

    if "why profit" in normalized_query or ("why" in normalized_query and any(term in normalized_query for term in ["profit", "sales", "revenue"])):
        answer_text = explain_profit_change(df)
        answer_text = localize_answer(answer_text, style)
        answer_text = await polish_answer_with_llm(clean_transcript, answer_text, style, df)
        return answer_text, {"intent": "trend_reason", "language": detected_language, "style": style}

    question_for_engine = normalized_query
    if len(question_for_engine.split()) <= 3 and recent_context:
        last_subject = recent_context[-1].get("context", {}).get("normalized_query", "")
        if last_subject:
            question_for_engine = f"{last_subject} {question_for_engine}"

    result = answer_data_question(df, profile, question_for_engine)
    answer_text = result.get("answer") if isinstance(result, dict) else str(result)
    if not answer_text:
        answer_text = NO_INFO

    answer_text = localize_answer(answer_text, style)
    answer_text = await polish_answer_with_llm(clean_transcript, answer_text, style, df)
    return answer_text, {
        "intent": "dataset_question",
        "language": detected_language,
        "style": style,
        "normalized_query": question_for_engine,
        "chart": result.get("chart") if isinstance(result, dict) else None,
    }


def build_proactive_suggestions(df: pd.DataFrame, profile: dict, language_hint: str | None = None):
    style = "hindi" if language_hint == "hi" else "hinglish" if language_hint == "hinglish" else "english"
    category_cols = get_category_columns(df)
    numeric_cols = get_numeric_columns(df)
    product_col = choose_column(category_cols, ["product", "item", "name", "category"])
    city_col = choose_column(category_cols, ["city", "region", "state", "market"])
    money_col = choose_column(numeric_cols, ["revenue", "sales", "amount", "total", "price", "profit"])
    if style == "hindi":
        suggestions = ["पूछें: मेरे KPIs समझाइए"]
    elif style == "hinglish":
        suggestions = ["Ask: Mere KPIs samjhao"]
    else:
        suggestions = ["Ask: Explain my KPIs"]
    if product_col and money_col:
        if style == "hindi":
            suggestions.append(f"पूछें: कौन सा {localized_label(product_col, style)} सबसे ज्यादा {localized_label(money_col, style)} देता है?")
        elif style == "hinglish":
            suggestions.append(f"Ask: Kaunsa {localized_label(product_col, style)} maximum {localized_label(money_col, style)} generate karta hai?")
        else:
            suggestions.append(f"Ask: Which {humanize_label(product_col)} generates maximum revenue?")
    if city_col and money_col:
        if style == "hindi":
            suggestions.append(f"पूछें: कौन सा {localized_label(city_col, style)} सबसे अच्छा perform कर रहा है?")
        elif style == "hinglish":
            suggestions.append(f"Ask: Kaunsa {localized_label(city_col, style)} best perform kar raha hai?")
        else:
            suggestions.append(f"Ask: Which {humanize_label(city_col)} is performing best?")
    if any("date" in column.lower() for column in df.columns):
        if style == "hindi":
            suggestions.append("पूछें: profit कम क्यों हो रहा है?")
        elif style == "hinglish":
            suggestions.append("Ask: Profit kam kyu ho raha hai?")
        else:
            suggestions.append("Ask: Why are profits decreasing?")
    missing_total = sum(profile.get("missing_values", {}).values()) if profile else 0
    if missing_total:
        if style == "hindi":
            suggestions.append("पूछें: पहले क्या clean करना चाहिए?")
        elif style == "hinglish":
            suggestions.append("Ask: Pehle kya clean karna chahiye?")
        else:
            suggestions.append("Ask: What should I clean first?")
    return suggestions[:4]
