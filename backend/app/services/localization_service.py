from __future__ import annotations

import copy
import re
from typing import Any

VALID_LANGUAGES = {"en", "hi", "hinglish"}
TECHNICAL_WORDS = {"CSV", "PDF", "API", "AI", "SQL", "Excel", "Power BI", "KPI", "KPIs", "ROI"}
DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")
VISIBLE_WORD_RE = re.compile(r"[\w\u0900-\u097F]+", re.UNICODE)
ALLOWED_HINDI_ENGLISH_WORDS = {word.lower() for word in TECHNICAL_WORDS} | {
    "csv",
    "xlsx",
    "json",
    "pdf",
    "api",
    "ai",
    "sql",
    "excel",
    "power",
    "bi",
    "kpi",
    "kpis",
    "roi",
}

PHRASES: dict[str, list[tuple[str, str]]] = {
    "hi": [
        ("Business problem", "व्यावसायिक समस्या"),
        ("AI reasoning", "एआई का तर्क"),
        ("Evidence", "प्रमाण"),
        ("Expected revenue", "अनुमानित राजस्व"),
        ("Expected cost", "अनुमानित लागत"),
        ("Implementation checklist", "कार्यान्वयन जाँच सूची"),
        ("Potential risks", "संभावित जोखिम"),
        ("Success metrics", "सफलता मापदंड"),
        ("Dependencies", "निर्भरताएँ"),
        ("Owner", "जिम्मेदार व्यक्ति"),
        ("Notes", "नोट्स"),
        ("Business lead", "व्यावसायिक प्रमुख"),
        ("Business Lead", "व्यावसायिक प्रमुख"),
        ("Recommended action", "सुझाई गई कार्रवाई"),
        ("Recommendation", "सुझाव"),
        ("Recommendations", "सुझाव"),
        ("Leadership Priority", "नेतृत्व प्राथमिकता"),
        ("Quick Win", "त्वरित लाभ"),
        ("Long-Term Strategy", "दीर्घकालिक रणनीति"),
        ("Growth Opportunity", "विकास अवसर"),
        ("Cost Saving", "लागत बचत"),
        ("Risk Reduction", "जोखिम में कमी"),
        ("Highest ROI", "सबसे अधिक ROI"),
        ("High", "उच्च"),
        ("Medium", "मध्यम"),
        ("Low", "कम"),
        ("Dataset signals, KPI movement, confidence level, and business impact were used.", "डेटासेट संकेत, KPI बदलाव, विश्वास स्तर और व्यावसायिक प्रभाव का उपयोग किया गया।"),
        ("A material business signal needs focused ownership.", "एक महत्वपूर्ण व्यावसायिक संकेत पर स्पष्ट जिम्मेदारी चाहिए।"),
        ("This recommendation is based on the strongest decision signal available in the uploaded analysis.", "यह सुझाव अपलोड किए गए विश्लेषण में उपलब्ध सबसे मजबूत निर्णय संकेत पर आधारित है।"),
        ("Revenue uplift estimate available after validation.", "सत्यापन के बाद राजस्व वृद्धि का अनुमान उपलब्ध होगा।"),
        ("Cost estimate depends on execution scope.", "लागत का अनुमान कार्यान्वयन के दायरे पर निर्भर करता है।"),
        ("Operational adoption may be slower than expected", "परिचालन अपनाने की गति अपेक्षा से धीमी हो सकती है"),
        ("External demand may change during rollout", "रोलआउट के दौरान बाहरी मांग बदल सकती है"),
        ("ROI lift", "ROI सुधार"),
        ("Revenue movement", "राजस्व बदलाव"),
        ("Execution completion", "कार्यान्वयन पूर्णता"),
        ("Risk reduction", "जोखिम में कमी"),
        ("Assign an owner", "जिम्मेदार व्यक्ति तय करें"),
        ("Assign an owner and weekly decision cadence.", "जिम्मेदार व्यक्ति और साप्ताहिक निर्णय प्रक्रिया तय करें।"),
        ("Launch a controlled pilot before scaling spend or process changes.", "खर्च या प्रक्रिया बदलाव बढ़ाने से पहले नियंत्रित पायलट शुरू करें।"),
        ("Measure ROI, adoption, and risk reduction after the first cycle.", "पहले चक्र के बाद ROI, अपनाने की दर और जोखिम में कमी मापें।"),
        ("Confirm the affected segment and baseline KPI.", "प्रभावित सेगमेंट और बेसलाइन KPI की पुष्टि करें।"),
        ("Define the first business intervention and expected outcome.", "पहला व्यावसायिक हस्तक्षेप और अपेक्षित परिणाम तय करें।"),
        ("Upload completed", "अपलोड पूरा हुआ"),
        ("Unsupported file type", "असमर्थित फाइल प्रकार"),
        ("Upload CSV, XLSX, or JSON.", "CSV, XLSX या JSON अपलोड करें।"),
        ("Uploaded file is empty", "अपलोड की गई फाइल खाली है"),
        ("Choose a non-empty CSV, XLSX, or JSON dataset.", "खाली न होने वाला CSV, XLSX या JSON डेटासेट चुनें।"),
        ("Upload processing failed", "अपलोड प्रोसेसिंग असफल रही"),
        ("Error processing question", "सवाल प्रोसेस करने में त्रुटि"),
        ("Error generating business advisor report", "बिजनेस एडवाइजर रिपोर्ट बनाने में त्रुटि"),
        ("No previous dataset found. Please upload a CSV.", "पिछला डेटासेट नहीं मिला। कृपया CSV अपलोड करें।"),
        ("Cleaned data: removed", "क्लीन डेटा: हटाए गए"),
        ("duplicates, filled", "डुप्लिकेट, भरी गईं"),
        ("missing values", "मिसिंग वैल्यू"),
    ],
    "hinglish": [
        ("Business problem", "Business problem"),
        ("AI reasoning", "AI ka reasoning"),
        ("Expected revenue", "Expected revenue"),
        ("Expected cost", "Expected cost"),
        ("Implementation checklist", "Implementation checklist"),
        ("Potential risks", "Potential risks"),
        ("Success metrics", "Success metrics"),
        ("Business lead", "Business lead"),
        ("Recommended action", "Recommended action"),
        ("Leadership Priority", "Leadership priority"),
        ("Quick Win", "Quick win"),
        ("Long-Term Strategy", "Long-term strategy"),
        ("A material business signal needs focused ownership.", "Ek important business signal ko clear owner chahiye."),
        ("This recommendation is based on the strongest decision signal available in the uploaded analysis.", "Ye recommendation uploaded analysis ke sabse strong decision signal par based hai."),
        ("Assign an owner and weekly decision cadence.", "Owner assign karo aur weekly decision cadence set karo."),
        ("Revenue uplift estimate available after validation.", "Validation ke baad revenue uplift estimate clear hoga."),
        ("Cost estimate depends on execution scope.", "Cost estimate execution scope par depend karta hai."),
        ("Upload completed", "Upload complete ho gaya"),
        ("Unsupported file type", "File type supported nahi hai"),
        ("Upload CSV, XLSX, or JSON.", "CSV, XLSX ya JSON upload karo."),
        ("Uploaded file is empty", "Uploaded file empty hai"),
        ("Choose a non-empty CSV, XLSX, or JSON dataset.", "Non-empty CSV, XLSX ya JSON dataset choose karo."),
        ("Upload processing failed", "Upload processing fail ho gayi"),
        ("Error processing question", "Question process karne me error"),
        ("Error generating business advisor report", "Business Advisor report generate karne me error"),
        ("No previous dataset found. Please upload a CSV.", "Previous dataset nahi mila. Please CSV upload karo."),
        ("Cleaned data: removed", "Clean data: remove hue"),
        ("duplicates, filled", "duplicates, fill hui"),
        ("missing values", "missing values"),
        ("Operational adoption may be slower than expected", "Operational adoption expected se slow ho sakti hai"),
        ("External demand may change during rollout", "Rollout ke dauran external demand change ho sakti hai"),
        ("ROI lift", "ROI lift"),
        ("Revenue movement", "Revenue movement"),
        ("Execution completion", "Execution completion"),
        ("Risk reduction", "Risk reduction"),
    ],
}

REGEXES: dict[str, list[tuple[re.Pattern[str], str]]] = {
    "en": [
        (re.compile(r"व्यावसायिक"), "business"),
        (re.compile(r"पूर्वानुमान"), "forecast"),
        (re.compile(r"जोखिम"), "risk"),
        (re.compile(r"असामान्यता"), "anomaly"),
        (re.compile(r"राजस्व"), "revenue"),
        (re.compile(r"लाभ"), "profit"),
        (re.compile(r"लागत"), "cost"),
        (re.compile(r"ग्राहक"), "customer"),
        (re.compile(r"विकास"), "growth"),
        (re.compile(r"रुझान"), "trend"),
        (re.compile(r"मापदंड"), "metric"),
        (re.compile(r"प्रभाव"), "impact"),
        (re.compile(r"कार्रवाई"), "action"),
        (re.compile(r"विश्वास"), "confidence"),
        (re.compile(r"सुझाव"), "recommendation"),
        (re.compile(r"डेटासेट"), "dataset"),
        (re.compile(r"मात्रा"), "quantity"),
        (re.compile(r"[\u0900-\u097F]+"), "business metric"),
    ],
    "hi": [
        (re.compile(r"\b(\d[\d,.]*) rows\b", re.I), r"\1 पंक्तियाँ"),
        (re.compile(r"\b(\d[\d,.]*) columns\b", re.I), r"\1 कॉलम"),
        (re.compile(r"\bmissing cells\b", re.I), "मिसिंग सेल"),
        (re.compile(r"\bduplicate rows\b", re.I), "डुप्लिकेट पंक्तियाँ"),
        (re.compile(r"\brevenue\b", re.I), "राजस्व"),
        (re.compile(r"\bprofit\b", re.I), "लाभ"),
        (re.compile(r"\bcost\b", re.I), "लागत"),
        (re.compile(r"\bcustomer(s)?\b", re.I), "ग्राहक"),
        (re.compile(r"\bsegment(s)?\b", re.I), "सेगमेंट"),
        (re.compile(r"\bdataset\b", re.I), "डेटासेट"),
        (re.compile(r"\bbusiness\b", re.I), "व्यावसायिक"),
        (re.compile(r"\bconfidence\b", re.I), "विश्वास"),
        (re.compile(r"\brisk(s)?\b", re.I), "जोखिम"),
        (re.compile(r"\bgrowth\b", re.I), "विकास"),
        (re.compile(r"\bforecast(s|ing)?\b", re.I), "पूर्वानुमान"),
        (re.compile(r"\btrend(s)?\b", re.I), "रुझान"),
        (re.compile(r"\banomal(y|ies)\b", re.I), "असामान्यता"),
        (re.compile(r"\bimpact\b", re.I), "प्रभाव"),
        (re.compile(r"\baction(s)?\b", re.I), "कार्रवाई"),
        (re.compile(r"\bmetric(s)?\b", re.I), "मापदंड"),
    ],
    "hinglish": [
        (re.compile(r"\bThis signal can affect\b", re.I), "Ye signal affect kar sakta hai"),
        (re.compile(r"\bReview the supporting evidence before acting\.?", re.I), "Act karne se pehle supporting evidence review karo."),
        (re.compile(r"\bFocus on\b", re.I), "Focus karo"),
        (re.compile(r"\bbefore using\b", re.I), "use karne se pehle"),
    ],
}


def normalize_language(language: str | None) -> str:
    return language if language in VALID_LANGUAGES else "en"


def language_from_request(request: Any | None, fallback: str | None = None) -> str:
    """Read the app-wide language contract from a FastAPI request."""
    if request is not None:
        query_language = getattr(request, "query_params", {}).get("language")
        header_language = getattr(request, "headers", {}).get("X-DataMantri-Language")
        accept_language = getattr(request, "headers", {}).get("Accept-Language")
        for candidate in (query_language, header_language):
            normalized = normalize_language(candidate)
            if candidate and normalized == candidate:
                return normalized
        if accept_language:
            for raw_part in accept_language.split(","):
                part = raw_part.split(";")[0].strip().lower()
                if part == "hinglish":
                    return "hinglish"
                primary = part.split("-")[0]
                if primary in VALID_LANGUAGES:
                    return primary
    return normalize_language(fallback)


def language_prompt_context(language: str | None, mode: str = "business", tone: str = "executive") -> dict[str, str]:
    language = normalize_language(language)
    names = {"en": "English", "hi": "Hindi", "hinglish": "Hinglish"}
    rules = {
        "en": (
            "Generate the response entirely in English. Never use Hindi words, Devanagari, "
            "transliteration, or mixed-language phrasing."
        ),
        "hi": (
            "Generate the response entirely in natural Hindi. Do not use English except universally "
            "accepted technical words: CSV, SQL, Python, API, Power BI, Excel, JSON, PDF, AI, KPI, ROI."
        ),
        "hinglish": (
            "Generate the response entirely in natural spoken Hinglish using Roman characters only. "
            "Do not use Devanagari. Do not create literal word-by-word translations."
        ),
    }
    return {"language": language, "language_name": names[language], "mode": mode, "tone": tone, "instruction": rules[language]}


def contains_devanagari(value: str | None) -> bool:
    return bool(value and DEVANAGARI_RE.search(str(value)))


def _visible_words(value: str) -> list[str]:
    return VISIBLE_WORD_RE.findall(str(value or ""))


def _english_word_ratio(value: str) -> float:
    words = _visible_words(value)
    if not words:
        return 0.0
    english_words = [
        word for word in words
        if re.search(r"[A-Za-z]", word) and word.lower() not in ALLOWED_HINDI_ENGLISH_WORDS
    ]
    return len(english_words) / len(words)


def validate_language_text(value: str | None, language: str | None) -> tuple[bool, str | None]:
    """Validate the product-wide language purity contract for generated display text."""
    language = normalize_language(language)
    text = str(value or "")
    if not text.strip():
        return True, None
    if language == "en" and contains_devanagari(text):
        return False, "English output contains Hindi Unicode characters."
    if language == "hi" and _english_word_ratio(text) > 0.05:
        return False, "Hindi output contains too much English text."
    if language == "hinglish" and contains_devanagari(text):
        return False, "Hinglish output contains Devanagari characters."
    return True, None


def _walk_text(value: Any, path: str = "") -> list[tuple[str, str]]:
    if isinstance(value, str):
        return [(path, value)]
    if isinstance(value, list):
        return [item for index, child in enumerate(value) for item in _walk_text(child, f"{path}[{index}]")]
    if isinstance(value, tuple):
        return [item for index, child in enumerate(value) for item in _walk_text(child, f"{path}[{index}]")]
    if isinstance(value, dict):
        return [
            item
            for key, child in value.items()
            for item in _walk_text(child, f"{path}.{key}" if path else str(key))
        ]
    return []


def validate_language_payload(value: Any, language: str | None) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    for path, text in _walk_text(value):
        valid, reason = validate_language_text(text, language)
        if not valid:
            violations.append({"path": path, "reason": reason or "Invalid language output"})
    return violations


def localize_text(value: str, language: str | None) -> str:
    language = normalize_language(language)
    text = str(value).replace("_", " ")
    for source, target in PHRASES.get(language, []):
        text = text.replace(source, target)
    for pattern, replacement in REGEXES.get(language, []):
        text = pattern.sub(replacement, text)
    return text


def _localize_key(key: str, language: str) -> str:
    return localize_text(key, language)


def localize_payload(value: Any, language: str | None) -> Any:
    language = normalize_language(language)
    if isinstance(value, str):
        return localize_text(value, language)
    if isinstance(value, list):
        return [localize_payload(item, language) for item in value]
    if isinstance(value, tuple):
        return tuple(localize_payload(item, language) for item in value)
    if isinstance(value, dict):
        return {key: localize_payload(item, language) for key, item in value.items()}
    return value


def localize_analysis_payload(analysis: dict[str, Any], language: str | None) -> dict[str, Any]:
    language = normalize_language(language)
    payload = copy.deepcopy(analysis)
    payload["language"] = language
    payload["localization"] = language_prompt_context(language)

    localized_sections = [
        "insights",
        "recommendations",
        "executive_summary",
        "executive_dashboard",
        "risks",
        "opportunities",
        "business_advice",
        "business_kpis",
        "forecasts",
        "anomaly_engine",
        "root_cause_engine",
        "ai_modes",
        "trend_engine",
        "explanation_engine",
    ]
    for section in localized_sections:
        if section in payload:
            payload[section] = localize_payload(payload[section], language)
    payload["language_qa"] = {
        "language": language,
        "violations": validate_language_payload(
            {section: payload.get(section) for section in localized_sections if section in payload},
            language,
        ),
    }
    return payload
