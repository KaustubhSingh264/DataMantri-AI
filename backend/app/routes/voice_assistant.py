from collections import defaultdict, deque
from time import time
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.routes.upload import get_db, load_latest_dataframe
from app.models.user import User
from app.schemas.voice_assistant import VoiceTextRequest
from app.services.subscription_service import FEATURE_VOICE, assert_usage_allowed, record_feature_usage
from app.services.business_logic import build_proactive_suggestions
from app.services.session_memory import get_or_create_session
from app.services.security import verify_user
from app.services.text_to_speech import text_to_speech
from app.services.voice_business_advisor import process_text_query, process_voice_query

router = APIRouter(prefix="/voice-assistant", tags=["voice-assistant"])
RATE_WINDOW_SECONDS = 60
RATE_LIMIT = 20
_voice_rate = defaultdict(deque)


def check_rate_limit(user_id: int):
    now = time()
    events = _voice_rate[user_id]
    while events and now - events[0] > RATE_WINDOW_SECONDS:
        events.popleft()
    if len(events) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Too many voice requests. Please wait a moment and try again.")
    events.append(now)


def enforce_voice_access(user, db: Session):
    assert_usage_allowed(user, db, FEATURE_VOICE)


def increment_voice_usage(user_id: int, db: Session):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db_user.qa_queries_used = (db_user.qa_queries_used or 0) + 1
        db.add(db_user)
        db.commit()
        record_feature_usage(db_user, db, FEATURE_VOICE)


def ensure_text(value, fallback: str = "") -> str:
    if value is None:
        return fallback
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return " ".join(filter(None, (ensure_text(item) for item in value))) or fallback
    if isinstance(value, dict):
        for key in ("answer_text", "answer", "response", "message", "detail", "error", "text", "summary", "advisory_summary"):
            if key in value:
                text = ensure_text(value.get(key))
                if text:
                    return text
        return str(value)
    return fallback


@router.post("/query")
async def voice_assistant_text_query(
    req: VoiceTextRequest,
    user=Depends(verify_user),
    db: Session = Depends(get_db),
):
    check_rate_limit(user.id)
    enforce_voice_access(user, db)

    latest, df = load_latest_dataframe(user, db)
    profile = (latest.result_json or {}).get("profile", {})
    kpis = (latest.result_json or {}).get("kpis", {})
    session = get_or_create_session(user.id, req.session_id)
    result = await process_text_query(req.transcript, session, df, profile, kpis, req.language_hint)
    answer_text = ensure_text(result.get("answer_text"), "I could not generate a voice answer from this request.")
    answer_audio_url = None

    try:
        _, answer_audio_url = await text_to_speech(answer_text, result.get("language") or req.language_hint)
    except Exception as exc:
        print(f"Voice TTS skipped: {exc}")

    increment_voice_usage(user.id, db)

    return {
        "transcript": ensure_text(result.get("transcript"), req.transcript),
        "answer_text": answer_text,
        "answer_audio_url": answer_audio_url,
        "language": result.get("language") or req.language_hint or "en-US",
        "session_id": session.id,
        "suggestions": build_proactive_suggestions(df, profile, req.language_hint),
    }


@router.post("/ask")
async def voice_assistant_ask(
    audio: UploadFile = File(...),
    session_id: Optional[str] = None,
    language_hint: Optional[str] = None,
    user=Depends(verify_user),
    db: Session = Depends(get_db),
):
    check_rate_limit(user.id)
    enforce_voice_access(user, db)

    latest, df = load_latest_dataframe(user, db)
    profile = (latest.result_json or {}).get("profile", {})
    kpis = (latest.result_json or {}).get("kpis", {})
    session = get_or_create_session(user.id, session_id)
    try:
        result = await process_voice_query(audio, session, df, profile, kpis, language_hint)
    except RuntimeError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc

    increment_voice_usage(user.id, db)

    return {
        "transcript": ensure_text(result.get("transcript"), ""),
        "answer_text": ensure_text(result.get("answer_text"), "I could not generate a voice answer from this request."),
        "answer_audio_url": result.get("answer_audio_url"),
        "language": result.get("language") or language_hint or "en-US",
        "session_id": session.id,
        "suggestions": build_proactive_suggestions(df, profile, language_hint),
    }
