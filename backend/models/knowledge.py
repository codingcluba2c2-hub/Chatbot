from sqlalchemy import Column, String, Float, Integer, JSON, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from core.database import Base

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

class KnowledgeNodeDB(Base):
    __tablename__ = "knowledge_nodes"
    
    id = Column(String, primary_key=True, index=True)
    parent_id = Column(String, ForeignKey("knowledge_nodes.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String, nullable=False)
    slug = Column(String, nullable=True)
    description = Column(String, nullable=True)
    response_markdown = Column(String, nullable=True)
    node_type = Column(String, default="standard")
    icon = Column(String, nullable=True)
    image = Column(String, nullable=True)
    priority = Column(Integer, default=1)
    sort_order = Column(Integer, default=1)
    status = Column(String, default="active")
    aliases = Column(JSON().with_variant(JSONB, "postgresql"), default=list)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, default="system")
    updated_by = Column(String, default="system")
