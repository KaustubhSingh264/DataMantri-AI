from app.services.speech_to_text import speech_to_text
from app.services.text_to_speech import text_to_speech
from app.services.session_memory import update_session_context
from app.services.business_logic import handle_business_query


async def process_text_query(transcript, session, df, profile, kpis, language_hint=None):
    answer_text, context = await handle_business_query(transcript, session, df, profile, kpis, language_hint)
    update_session_context(session, transcript, answer_text, context)
    return {
        "transcript": transcript,
        "answer_text": answer_text,
        "language": context.get("language") or language_hint or "en-US",
        "context": context,
    }


async def process_voice_query(audio, session, df, profile, kpis, language_hint=None):
    transcript, detected_lang = await speech_to_text(audio, language_hint)
    answer_text, context = await handle_business_query(transcript, session, df, profile, kpis, detected_lang or language_hint)
    update_session_context(session, transcript, answer_text, context)
    audio_path, audio_url = await text_to_speech(answer_text, detected_lang or language_hint)
    return {
        "transcript": transcript,
        "answer_text": answer_text,
        "answer_audio_url": audio_url,
        "answer_audio_path": audio_path,
        "language": detected_lang or language_hint or "en-US",
        "context": context,
    }
