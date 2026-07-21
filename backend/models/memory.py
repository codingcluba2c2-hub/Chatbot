from sqlalchemy import Column, String, Float, Integer, JSON, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from core.database import Base
from sqlalchemy.sql import func
from datetime import datetime

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
