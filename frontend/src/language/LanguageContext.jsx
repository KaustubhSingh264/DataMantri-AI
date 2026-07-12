import React, { createContext, useCallback, useContext, useMemo, useState } from "react";
import {
  LANGUAGE_STORAGE_KEY,
  getLanguageHeaders,
  getLanguageLocale,
  getSpeechLocale,
  normalizeLanguage,
} from "./languageSystem";

const LanguageContext = createContext(null);

export function LanguageProvider({ children }) {
  const [language, setLanguageState] = useState(() => normalizeLanguage(localStorage.getItem(LANGUAGE_STORAGE_KEY)));

  const setLanguage = useCallback((nextLanguage) => {
    const normalized = normalizeLanguage(nextLanguage);
    localStorage.setItem(LANGUAGE_STORAGE_KEY, normalized);
    setLanguageState(normalized);
    return normalized;
  }, []);

  const value = useMemo(() => ({
    language,
    setLanguage,
    locale: getLanguageLocale(language),
    speechLocale: getSpeechLocale(language),
    headers: getLanguageHeaders(language),
  }), [language, setLanguage]);

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error("useLanguage must be used inside LanguageProvider");
  }
  return context;
}
