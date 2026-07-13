# backend/services/session_manager.py
import uuid
import time
from typing import Dict, Any, Optional

class SessionManager:
    # In-memory storage: session_id -> session_data
    _sessions: Dict[str, Dict[str, Any]] = {}
    SESSION_TTL = 3600 * 24 # 24 hours

    @classmethod
    def generate_session_id(cls) -> str:
        return str(uuid.uuid4())

    @classmethod
    def create_session(cls, session_id: Optional[str] = None) -> str:
        """Returns existing session_id or creates a new one."""
        if session_id and session_id in cls._sessions:
            cls._sessions[session_id]["updated_at"] = time.time()
            return session_id
            
        new_session_id = session_id or cls.generate_session_id()
        cls._sessions[new_session_id] = {
            "session_id": new_session_id,
            "created_at": time.time(),
            "updated_at": time.time(),
        }
        return new_session_id

    @classmethod
    def get_session(cls, session_id: str) -> Optional[Dict[str, Any]]:
        cls.expire_sessions()
        session = cls._sessions.get(session_id)
        if session:
            session["updated_at"] = time.time()
        return session

    @classmethod
    def update_session(cls, session_id: str, data: Dict[str, Any]):
        if session_id in cls._sessions:
            cls._sessions[session_id].update(data)
            cls._sessions[session_id]["updated_at"] = time.time()

    @classmethod
    def delete_session(cls, session_id: str):
        if session_id in cls._sessions:
            del cls._sessions[session_id]

    @classmethod
    def expire_sessions(cls):
        current_time = time.time()
        expired = [sid for sid, data in cls._sessions.items() if current_time - data["updated_at"] > cls.SESSION_TTL]
        for sid in expired:
            del cls._sessions[sid]
            
    @classmethod
    def clear_session_data(cls, session_id: str):
        if session_id in cls._sessions:
            cls._sessions[session_id] = {
                "session_id": session_id,
                "created_at": time.time(),
                "updated_at": time.time(),
            }
