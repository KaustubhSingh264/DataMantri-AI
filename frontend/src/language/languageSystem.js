export const LANGUAGE_SEQUENCE = ["en", "hi", "hinglish"];

export const LANGUAGE_NAMES = {
  en: "English",
  hi: "Hindi",
  hinglish: "Hinglish",
};

export const LANGUAGE_BUTTON_LABELS = {
  en: "🇬🇧 English",
  hi: "🇮🇳 हिंदी",
  hinglish: "🇮🇳 Hinglish",
};

export const LANGUAGE_LOCALES = {
  en: "en-US",
  hi: "hi-IN",
  hinglish: "en-IN",
};

export const SPEECH_LOCALES = {
  en: "en-US",
  hi: "hi-IN",
  hinglish: "hi-IN",
};

export const LANGUAGE_STORAGE_KEY = "language";

export function normalizeLanguage(language) {
  return LANGUAGE_SEQUENCE.includes(language) ? language : "en";
}

export function getLanguageLocale(language) {
  return LANGUAGE_LOCALES[normalizeLanguage(language)];
}

export function getSpeechLocale(language) {
  return SPEECH_LOCALES[normalizeLanguage(language)];
}

export function getLanguageHeaders(language) {
  const normalized = normalizeLanguage(language);
  return {
    "X-DataMantri-Language": normalized,
    "Accept-Language": getLanguageLocale(normalized),
  };
}

export function formatLanguageDate(value, language, options = {}) {
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const normalized = normalizeLanguage(language);
  const locale = getLanguageLocale(normalized);
  const dateOptions = {
    year: "numeric",
    month: "long",
    day: "numeric",
    ...options,
  };
  return new Intl.DateTimeFormat(locale, dateOptions).format(date);
}
