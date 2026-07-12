import useVoiceAssistant from "../hooks/useVoiceAssistant";
import { getTranslations } from "../locales";
import "./VoiceAssistantModal.css";

function toDisplayText(value, fallback = "") {
  if (value == null) return fallback;
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  if (Array.isArray(value)) {
    const text = value.map((item) => toDisplayText(item)).filter(Boolean).join(" ");
    return text || fallback;
  }
  if (typeof value === "object") {
    const keys = ["answer_text", "answer", "response", "message", "detail", "error", "text", "summary", "advisory_summary", "msg"];
    for (const key of keys) {
      if (Object.prototype.hasOwnProperty.call(value, key)) {
        const text = toDisplayText(value[key]);
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

export default function VoiceAssistantModal({ token, hasData, language, mode, onClose, showToast }) {
  const copy = getTranslations(language);
  const voiceLanguage = language === "en" ? "en-US" : "hi-IN";
  const {
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
  } = useVoiceAssistant({
    token,
    language: voiceLanguage,
    languageHint: language,
    mode,
    onError: showToast,
  });

  const examples = [copy.voiceExampleRevenue, copy.voiceExampleKpis, copy.voiceExampleProfit];

  const localizeSuggestion = (value) => {
    const clean = toDisplayText(value).replace(/^Ask:\s*/i, "").replace(/^पूछें:\s*/i, "");
    return clean;
  };

  const localizeVoiceAnswer = (value) => {
    return toDisplayText(value);
  };

  const disabled = !hasData || !isSupported;

  return (
    <div className="voice-modal-bg" onClick={onClose}>
      <div className="voice-modal" onClick={(event) => event.stopPropagation()}>
        <button className="voice-close-btn" onClick={onClose} aria-label={copy.voiceCloseLabel} type="button">×</button>
        <div className="voice-modal-header">
          <span className="voice-kicker">{copy.voiceKicker}</span>
          <h2>{copy.voiceTitle}</h2>
          <p>{copy.voiceSubtitle}</p>
          <span className="voice-mode-chip">{mode === "data" ? copy.voiceDataMode : mode === "eli5" ? copy.voiceEli5Mode : copy.voiceBusinessMode}</span>
        </div>

        <div className={`voice-orb ${state}`} ref={waveformRef}>
          <div className="voice-bars" aria-hidden="true">
            <span /><span /><span /><span /><span />
          </div>
          <button
            className={`mic-anim ${state}`}
            onClick={state === "listening" ? stopListening : state === "speaking" ? stopSpeaking : startListening}
            disabled={disabled || state === "analyzing"}
            type="button"
          >
            {state === "listening" ? "■" : state === "speaking" ? "Ⅱ" : "🎙"}
          </button>
        </div>

        <div className={`voice-state ${state}`}>{copy[`voice${state.charAt(0).toUpperCase()}${state.slice(1)}`] || copy.voiceIdle}</div>

        {!hasData && <div className="voice-warning">{copy.voiceNoData}</div>}
        {!isSupported && <div className="voice-warning">{copy.voiceNoSupport}</div>}

        {transcript && (
          <div className="voice-message user">
            <span>{copy.voiceYouAsked}</span>
            <p>{transcript}</p>
          </div>
        )}
        {answer && (
          <div className={`voice-message ai ${answer.error ? "error" : ""}`}>
            <div className="voice-message-top">
              <span>{copy.voiceResponse}</span>
              {!answer.error && <button onClick={() => playAudio()} type="button">{copy.voiceSpeakAgain}</button>}
            </div>
            <p>{localizeVoiceAnswer(answer.text)}</p>
          </div>
        )}

        <div className="voice-examples">
          {(suggestions.length ? suggestions : examples).slice(0, 3).map((item) => {
            const prompt = localizeSuggestion(item);
            return (
              <button key={prompt} onClick={() => askTranscript(prompt)} disabled={!hasData || state === "analyzing"} type="button">
                {prompt}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
