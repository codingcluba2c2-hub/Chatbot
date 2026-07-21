# backend/pipeline/pipeline_context.py
import uuid
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, PrivateAttr
from services.session_manager import SessionManager
import logging

class PipelineContext(BaseModel):
    original_message: str
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    
    normalized_message: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
    current_intent: Optional[str] = None
    entities: Dict[str, Any] = Field(default_factory=dict)
    aliases: Dict[str, Any] = Field(default_factory=dict)
    is_numeric: bool = False
    
    _logger: logging.Logger = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)
        if not self.conversation_id:
            self.conversation_id = str(uuid.uuid4())
        self.session_id = SessionManager.create_session(self.session_id)
        from core.logger import get_logger
        self._logger = get_logger("pipeline_context")

    @property
    def logger(self):
        return self._logger
