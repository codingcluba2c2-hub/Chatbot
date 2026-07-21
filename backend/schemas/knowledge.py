from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid
import time

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

class KnowledgeNode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: Optional[str] = None
    title: str
    slug: Optional[str] = None
    description: Optional[str] = None
    response_markdown: Optional[str] = None
    node_type: str = "standard"
    icon: Optional[str] = None
    image: Optional[str] = None
    priority: int = 1
    sort_order: int = 1
    status: str = "active"
    aliases: List[str] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    created_by: str = "system"
    updated_by: str = "system"
