# backend/pipeline/pipeline_context.py
import uuid
from typing import Dict, Any, Optional
from services.session_manager import SessionManager

class PipelineContext:
    def __init__(self, original_message: str, session_id: Optional[str] = None, conversation_id: Optional[str] = None):
        self.original_message = original_message
        self.normalized_message = ""
        self.metadata: Dict[str, Any] = {}
        self.current_intent: Optional[str] = None
        self.entities: Dict[str, Any] = {}
        self.aliases: Dict[str, Any] = {}
        self.conversation_id: str = conversation_id or str(uuid.uuid4())
        self.session_id: str = SessionManager.create_session(session_id)
        self.is_numeric: bool = False
