"""
Purpose: Consolidate all Pydantic schemas.
Responsibilities: Input/output validation.
Flow: Used by api and pipeline.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from typing import Optional, Dict, Any
from typing import Optional, List, Any, Dict
from typing import Optional, List, Dict, Any
import time
import uuid

# backend/schemas/admin.py

class BaseEntity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    created_by: Optional[str] = "system"
    updated_by: Optional[str] = "system"
    status: Optional[str] = "active"

class GreetingBase(BaseModel):
    name: str
    intent: str = "Greeting"
    priority: int = 1
    alias: List[str] = Field(default_factory=list)
    regex: Optional[str] = None
    response: str = ""
    enabled: bool = True

class Greeting(BaseEntity, GreetingBase):
    pass


class FAQBase(BaseModel):
    title: str
    answer: Optional[str] = ""
    aliases: List[str] = []
    regex_pattern: Optional[str] = None
    parent_id: Optional[str] = None
    display_type: str = "Standard"
    show_children_buttons: bool = False
    icon: Optional[str] = None
    status: Optional[str] = "active"

class FAQ(BaseEntity, FAQBase):
    pass


class AuditLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = Field(default_factory=time.time)
    action: str
    entity_type: str
    entity_id: str
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    user: str = "system"



class KnowledgeDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    category: str = "general"
    language: str = "en"
    status: str = "processing" # draft, processing, published, archived, failed
    version: int = 1
    tags: List[str] = Field(default_factory=list)
    uploaded_by: str = "admin"
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    file_path: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = 0
    chunk_count: int = 0
    error_message: Optional[str] = None
    processing_stats: Dict[str, Any] = Field(default_factory=dict)
    file_hash: Optional[str] = None
    raw_text: Optional[str] = None

class DocumentChunk(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)

class KnowledgeSettings(BaseModel):
    id: str = "default"
    chunk_strategy: str = "character"
    chunk_size: int = 800
    chunk_overlap: int = 150
    similarity_threshold: float = 0.75
    top_k: int = 5
    updated_at: float = Field(default_factory=time.time)


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)



# backend/schemas/response.py

class ChatResponse(BaseModel):
    intent: str
    response: str
    components: List[Dict[str, Any]] = Field(default_factory=list)
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    session_id: Optional[str] = None
    trace: Optional[Dict[str, Any]] = None


