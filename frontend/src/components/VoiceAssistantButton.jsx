import React, { useState } from "react";
import VoiceAssistantModal from "./VoiceAssistantModal";
import "./VoiceAssistantButton.css";

export default function VoiceAssistantButton({ token, hasData, language, mode, showToast }) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button
        className={`voice-assistant-btn${open ? " open" : ""}`}
        onClick={() => setOpen(!open)}
        aria-label="Open Voice Business Advisor"
        type="button"
      >
        <span className="voice-btn-ring" />
        <span className="mic-icon">🎙</span>
      </button>
      {open && (
        <VoiceAssistantModal
          token={token}
          hasData={hasData}
          language={language}
          mode={mode}
          onClose={() => setOpen(false)}
          showToast={showToast}
        />
      )}
    </>
  );
}
