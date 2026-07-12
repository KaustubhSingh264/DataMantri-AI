import os
import tempfile


async def text_to_speech(text, language):
    if not os.getenv("OPENAI_API_KEY"):
        return None, None

    from openai import OpenAI

    audio_dir = os.path.join(os.getcwd(), "static", "audio")
    os.makedirs(audio_dir, exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3", dir=audio_dir) as tmp:
        audio_path = tmp.name

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.audio.speech.create(
        model=os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts"),
        voice=os.getenv("OPENAI_TTS_VOICE", "alloy"),
        input=text[:4000],
    )
    response.stream_to_file(audio_path)
    audio_url = f"/static/audio/{os.path.basename(audio_path)}"
    return audio_path, audio_url
