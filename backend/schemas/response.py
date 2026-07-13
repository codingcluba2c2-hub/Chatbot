# backend/schemas/response.py
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

class ChatResponse(BaseModel):
    intent: str
    response: str
    components: List[Dict[str, Any]] = Field(default_factory=list)
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    session_id: Optional[str] = None
    trace: Optional[Dict[str, Any]] = None
