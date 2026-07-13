from sqlalchemy import Column, String, Float, Integer, JSON
from core.database import Base

class ConversationDB(Base):
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=True, index=True)
    created_at = Column(Float)
    updated_at = Column(Float)

class MessageDB(Base):
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, index=True)
    conversation_id = Column(String, index=True)
    role = Column(String) # 'user' or 'assistant'
    message = Column(String)
    intent = Column(String, nullable=True)
    created_at = Column(Float)

class MemoryFactDB(Base):
    __tablename__ = "memory_facts"
    
    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, index=True) # Usually mapped to conversation_id
    key = Column(String, index=True)
    value = Column(JSON)
    expires_at = Column(Float, nullable=True)
    created_at = Column(Float)
