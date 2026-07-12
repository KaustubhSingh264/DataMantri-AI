from typing import Optional

from pydantic import BaseModel


class VoiceTextRequest(BaseModel):
    transcript: str
    session_id: Optional[str] = None
    language_hint: Optional[str] = None
