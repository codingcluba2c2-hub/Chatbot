from sqlalchemy import Column, String, Float, Integer, JSON
from core.database import Base
import time
import uuid

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
