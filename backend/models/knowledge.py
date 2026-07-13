from sqlalchemy import Column, String, Float, Integer, JSON
from core.database import Base

class KnowledgeDocumentDB(Base):
    __tablename__ = "knowledge_documents"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    category = Column(String, default="general")
    language = Column(String, default="en")
    status = Column(String, default="processing")
    version = Column(Integer, default=1)
    tags = Column(JSON, default=list)
    uploaded_by = Column(String, default="admin")
    created_at = Column(Float)
    updated_at = Column(Float)
    file_path = Column(String, nullable=True)
    file_type = Column(String, nullable=True)
    file_size = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    error_message = Column(String, nullable=True)
    processing_stats = Column(JSON, default=dict)
    file_hash = Column(String, nullable=True, index=True)

class DocumentChunkDB(Base):
    __tablename__ = "document_chunks"
    
    id = Column(String, primary_key=True, index=True)
    document_id = Column(String, index=True)
    content = Column(String)
    metadata_col = Column("metadata", JSON, default=dict)
    created_at = Column(Float)

class KnowledgeSettingsDB(Base):
    __tablename__ = "knowledge_settings"
    
    id = Column(String, primary_key=True, index=True, default="default")
    chunk_strategy = Column(String, default="character")
    chunk_size = Column(Integer, default=800)
    chunk_overlap = Column(Integer, default=150)
    similarity_threshold = Column(Float, default=0.75)
    top_k = Column(Integer, default=5)
    updated_at = Column(Float)
