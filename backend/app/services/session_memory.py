from uuid import uuid4
from datetime import datetime

_sessions = {}

class Session:
    def __init__(self, user_id, session_id=None):
        self.id = session_id or str(uuid4())
        self.user_id = user_id
        self.history = []

def get_or_create_session(user_id, session_id=None):
    if session_id and session_id in _sessions and _sessions[session_id].user_id == user_id:
        return _sessions[session_id]
    session = Session(user_id, session_id)
    _sessions[session.id] = session
    return session

def update_session_context(session, user_query, ai_response, context):
    session.history.append({
        "user": user_query,
        "ai": ai_response,
        "context": context,
        "created_at": datetime.utcnow().isoformat(),
    })
    if len(session.history) > 8:
        session.history = session.history[-8:]


def get_recent_context(session):
    return session.history[-4:] if session and session.history else []
