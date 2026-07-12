import os
import tempfile


async def speech_to_text(audio, language_hint=None):
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("Server speech-to-text needs OPENAI_API_KEY. Browser voice mode can still send recognized text securely to the backend.")

    suffix = os.path.splitext(audio.filename or "")[1] or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await audio.read())
        tmp_path = tmp.name

    try:
        from openai import OpenAI

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        with open(tmp_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model=os.getenv("OPENAI_STT_MODEL", "whisper-1"),
                file=audio_file,
                language=(language_hint.split("-")[0] if language_hint else None),
                response_format="verbose_json",
            )
        transcript = getattr(transcription, "text", "") or transcription.get("text", "")
        detected_lang = getattr(transcription, "language", None) or language_hint or "en"
        return transcript, detected_lang
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
