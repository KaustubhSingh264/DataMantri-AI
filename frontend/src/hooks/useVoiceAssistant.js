import { useCallback, useEffect, useRef, useState } from "react";
import { API_BASE_CANDIDATES } from "../config/api";
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

function extractText(value, fallback = "") {
  if (value == null) return fallback;
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  if (Array.isArray(value)) {
    const text = value.map((item) => extractText(item)).filter(Boolean).join(" ");
    return text || fallback;
  }
  if (typeof value === "object") {
    const priorityKeys = [
      "answer_text",
      "answer",
      "response",
      "message",
      "detail",
      "error",
      "text",
      "summary",
      "advisory_summary",
      "msg",
    ];
    for (const key of priorityKeys) {
      if (Object.prototype.hasOwnProperty.call(value, key)) {
        const text = extractText(value[key]);
        if (text) return text;
      }
    }
    try {
      return JSON.stringify(value);
    } catch {
      return fallback;
    }
  }
  return fallback;
}

function normalizeSpeechLanguage(languageCode) {
  const raw = String(languageCode || "").toLowerCase();
  if (raw.includes("hi") || raw.includes("hindi") || raw.includes("hinglish")) return "hi-IN";
  return "en-US";
}

function resolveAudioUrl(apiBase, audioUrl) {
  if (!audioUrl) return "";
  if (/^https?:\/\//i.test(audioUrl)) return audioUrl;
  return `${apiBase}${audioUrl.startsWith("/") ? "" : "/"}${audioUrl}`;
}

function pickVoice(language) {
  const voices = window.speechSynthesis?.getVoices?.() || [];
  const preferredLang = normalizeSpeechLanguage(language).startsWith("hi") ? "hi" : "en";
  return voices.find((voice) => voice.lang?.toLowerCase().startsWith(preferredLang)) || voices[0] || null;
}

export default function useVoiceAssistant({ token, language = "en-US", languageHint = language, mode = "business", onError } = {}) {
  const [state, setState] = useState("idle");
  const [transcript, setTranscript] = useState("");
  const [answer, setAnswer] = useState(null);
  const [sessionId, setSessionId] = useState(localStorage.getItem("voiceSessionId") || "");
  const [suggestions, setSuggestions] = useState([]);
  const [isSupported, setIsSupported] = useState(Boolean(SpeechRecognition));
  const waveformRef = useRef();
  const recognitionRef = useRef(null);
  const finalTranscriptRef = useRef("");
  const audioRef = useRef(null);

  const postVoiceQuery = useCallback(async (payload) => {
    let lastError = null;
    for (const apiBase of API_BASE_CANDIDATES) {
      try {
        const res = await fetch(`${apiBase}/voice-assistant/query`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ ...payload, mode }),
        });
        let data = {};
        try {
          data = await res.json();
        } catch {
          data = {};
        }
        if (!res.ok) {
          const httpError = new Error(extractText(data.detail || data, `Voice advisor request failed (${res.status}).`));
          httpError.isHttpError = true;
          throw httpError;
        }
        return { data, apiBase };
      } catch (error) {
        if (error.isHttpError) throw error;
        lastError = error;
      }
    }
    throw new Error(lastError?.message || "Could not connect to the Data Mantri backend. Please make sure FastAPI is running on port 8000.");
  }, [token]);

  useEffect(() => {
    setIsSupported(Boolean(SpeechRecognition));
    return () => {
      recognitionRef.current?.abort?.();
      window.speechSynthesis?.cancel?.();
    };
  }, []);

  const speak = useCallback((text, responseLanguage) => {
    const safeText = extractText(text).trim();
    if (!safeText || !window.speechSynthesis) {
      setState("idle");
      return;
    }

    window.speechSynthesis.cancel();
    window.speechSynthesis.resume?.();
    const utterance = new SpeechSynthesisUtterance(safeText);
    const speechLanguage = normalizeSpeechLanguage(responseLanguage || language);
    utterance.lang = speechLanguage;
    utterance.rate = speechLanguage.startsWith("hi") ? 0.92 : 0.96;
    utterance.pitch = 1;
    const voice = pickVoice(speechLanguage);
    if (voice) utterance.voice = voice;
    utterance.onstart = () => setState("speaking");
    utterance.onend = () => setState("idle");
    utterance.onerror = () => setState("idle");
    window.speechSynthesis.speak(utterance);
  }, [language]);

  const playAudio = useCallback((url, fallbackText, fallbackLanguage) => {
    if (!url) {
      speak(fallbackText || answer?.text, fallbackLanguage || answer?.language);
      return;
    }
    audioRef.current?.pause?.();
    const audio = new Audio(url);
    audioRef.current = audio;
    setState("speaking");
    audio.onended = () => setState("idle");
    audio.onerror = () => speak(fallbackText || answer?.text, fallbackLanguage || answer?.language);
    audio.play().catch(() => speak(fallbackText || answer?.text, fallbackLanguage || answer?.language));
  }, [answer, speak]);

  const askTranscript = useCallback(async (spokenText) => {
    const cleaned = spokenText.trim();
    if (!cleaned) {
      setState("idle");
      return;
    }

    setState("analyzing");
    setTranscript(cleaned);
    setAnswer(null);

    try {
      const { data, apiBase } = await postVoiceQuery({
          transcript: cleaned,
          session_id: sessionId || null,
          language_hint: languageHint,
      });

      if (data.session_id) {
        setSessionId(data.session_id);
        localStorage.setItem("voiceSessionId", data.session_id);
      }
      const answerText = extractText(
        data.answer_text || data.answer || data.response || data.message,
        "I could not generate a voice answer from this request."
      );
      const responseLanguage = data.language || languageHint || language;

      setSuggestions(Array.isArray(data.suggestions) ? data.suggestions : []);
      setAnswer({ text: answerText, audioUrl: data.answer_audio_url || null, language: responseLanguage });

      if (data.answer_audio_url) {
        playAudio(resolveAudioUrl(apiBase, data.answer_audio_url), answerText, responseLanguage);
      } else {
        speak(answerText, responseLanguage);
      }
    } catch (error) {
      const message = extractText(error?.message || error, "Voice advisor request failed.");
      setState("idle");
      setAnswer({ text: message, error: true });
      onError?.(message);
    }
  }, [language, languageHint, onError, playAudio, postVoiceQuery, sessionId, speak]);

  const startListening = async () => {
    if (!SpeechRecognition) {
      onError?.("Voice input is not supported in this browser. Please use Chrome or Edge.");
      return;
    }
    if (!token) {
      onError?.("Please log in to use the voice advisor.");
      return;
    }

    window.speechSynthesis?.cancel?.();
    recognitionRef.current?.abort?.();
    finalTranscriptRef.current = "";
    setState("listening");
    setTranscript("");
    setAnswer(null);

    const recognition = new SpeechRecognition();
    recognition.lang = language;
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;
    recognition.onresult = (event) => {
      let interim = "";
      let finalText = "";
      for (let index = event.resultIndex; index < event.results.length; index += 1) {
        const piece = event.results[index][0].transcript;
        if (event.results[index].isFinal) finalText += piece;
        else interim += piece;
      }
      if (finalText) finalTranscriptRef.current = `${finalTranscriptRef.current} ${finalText}`.trim();
      setTranscript(`${finalTranscriptRef.current} ${interim}`.trim());
    };
    recognition.onerror = (event) => {
      setState("idle");
      onError?.(event.error === "not-allowed" ? "Microphone permission was blocked." : "Voice recognition failed. Please try again.");
    };
    recognition.onend = () => {
      const spokenText = finalTranscriptRef.current.trim();
      if (state === "listening" || spokenText) {
        askTranscript(spokenText || transcript);
      }
    };
    recognitionRef.current = recognition;
    recognition.start();
  };

  const stopListening = () => {
    recognitionRef.current?.stop?.();
    setState("analyzing");
  };

  const stopSpeaking = () => {
    audioRef.current?.pause?.();
    window.speechSynthesis?.cancel?.();
    setState("idle");
  };

  return {
    state,
    transcript,
    answer,
    suggestions,
    isSupported,
    startListening,
    stopListening,
    stopSpeaking,
    playAudio,
    askTranscript,
    waveformRef,
  };
}
