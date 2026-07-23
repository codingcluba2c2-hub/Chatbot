"""
Purpose: Consolidate all SQLAlchemy models.
Responsibilities: Define database tables.
Flow: Accessed by chatbot and api.
"""

from datetime import datetime
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, String, Float, Boolean, Integer, JSON
from sqlalchemy import Column, String, Float, Integer, JSON
from sqlalchemy import Column, String, Float, Integer, JSON, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from core.database import Base
import time
import uuid


class GreetingDB(Base):
    __tablename__ = "greetings"
    
    id = Column(String, primary_key=True, index=True)
    created_at = Column(Float)
    updated_at = Column(Float)
    created_by = Column(String, default="system")
    updated_by = Column(String, default="system")
    status = Column(String, default="active")
    
    name = Column(String)
    intent = Column(String, default="Greeting")
    priority = Column(Integer, default=1)
    alias = Column(JSON, default=list)
    regex = Column(String, nullable=True)
    response = Column(String, default="")
    enabled = Column(Boolean, default=True)


class FAQDB(Base):
    __tablename__ = "faqs"
    
    id = Column(String, primary_key=True, index=True)
    created_at = Column(Float)
    updated_at = Column(Float)
    created_by = Column(String, default="system")
    updated_by = Column(String, default="system")
    status = Column(String, default="active")
    
    title = Column(String)
    answer = Column(String)
    aliases = Column(JSON, default=list)
    regex_pattern = Column(String, nullable=True)
    
    parent_id = Column(String, nullable=True)
    display_type = Column(String, default="Standard")
    show_children_buttons = Column(Boolean, default=False)
    icon = Column(String, nullable=True)



class AuditLogDB(Base):
    __tablename__ = "audit_logs"
    
    id = Column(String, primary_key=True, index=True)
    timestamp = Column(Float)
    action = Column(String)
    entity_type = Column(String)
    entity_id = Column(String)
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    user = Column(String, default="system")



class ChatCacheDB(Base):
    __tablename__ = "chat_cache"
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    normalized_question = Column(String, index=True)
    question_hash = Column(String, index=True, unique=True)
    embedding = Column(JSON, nullable=True) # Storing list of floats as JSON
    retrieved_chunk_ids = Column(JSON, nullable=True)
    retrieved_scores = Column(JSON, nullable=True)
    answer = Column(String)
    provider_used = Column(String)
    session_id = Column(String, index=True, nullable=True)
    created_at = Column(Float, default=time.time)
    expires_at = Column(Float, nullable=True)
    hit_count = Column(Integer, default=0)
    last_accessed = Column(Float, default=time.time)



class KnowledgeDocumentDB(Base):
    __tablename__ = "knowledge_documents"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String, default="general")
    language = Column(String, default="en")
    status = Column(String, default="processing")
    version = Column(Integer, default=1)
    tags = Column(JSON().with_variant(JSONB, "postgresql"), default=list)
    uploaded_by = Column(String, default="admin")
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    file_path = Column(String, nullable=True)
    file_type = Column(String, nullable=True)
    file_size = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    error_message = Column(String, nullable=True)
    processing_stats = Column(JSON().with_variant(JSONB, "postgresql"), default=dict)
    file_hash = Column(String, nullable=True, index=True)
    raw_text = Column(String, nullable=True)

class DocumentChunkDB(Base):
    __tablename__ = "document_chunks"
    
    id = Column(String, primary_key=True, index=True)
    document_id = Column(String, ForeignKey("knowledge_documents.id", ondelete="CASCADE"), index=True)
    chunk_number = Column(Integer, default=0)
    title = Column(String, nullable=True)
    content = Column(String, nullable=False)
    embedding = Column(Vector(384))
    metadata_col = Column("metadata", JSON().with_variant(JSONB, "postgresql"), default=dict)
    token_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class KnowledgeSettingsDB(Base):
    __tablename__ = "knowledge_settings"
    
    id = Column(String, primary_key=True, index=True, default="default")
    chunk_strategy = Column(String, default="character")
    chunk_size = Column(Integer, default=800)
    chunk_overlap = Column(Integer, default=150)
    similarity_threshold = Column(Float, default=0.75)
    top_k = Column(Integer, default=5)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())




class ConversationDB(Base):
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class MessageDB(Base):
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    role = Column(String, nullable=False) # 'user' or 'assistant'
    message = Column(String, nullable=False)
    intent = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())

class MemoryFactDB(Base):
    __tablename__ = "memory_facts"
    
    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    key = Column(String, index=True, nullable=False)
    value = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())


