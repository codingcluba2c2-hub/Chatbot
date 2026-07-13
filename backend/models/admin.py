from sqlalchemy import Column, String, Float, Boolean, Integer, JSON
from core.database import Base

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

class FarewellDB(Base):
    __tablename__ = "farewells"
    
    id = Column(String, primary_key=True, index=True)
    created_at = Column(Float)
    updated_at = Column(Float)
    created_by = Column(String, default="system")
    updated_by = Column(String, default="system")
    status = Column(String, default="active")
    
    name = Column(String)
    intent = Column(String, default="Farewell")
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
    
    question = Column(String)
    aliases = Column(JSON, default=list)
    answer = Column(String)
    category = Column(String, default="general")
    keywords = Column(JSON, default=list)
    priority = Column(Integer, default=1)
    language = Column(String, default="en")
    enabled = Column(Boolean, default=True)

class FastPathDB(Base):
    __tablename__ = "fastpaths"
    
    id = Column(String, primary_key=True, index=True)
    created_at = Column(Float)
    updated_at = Column(Float)
    created_by = Column(String, default="system")
    updated_by = Column(String, default="system")
    status = Column(String, default="active")
    
    trigger = Column(String)
    aliases = Column(JSON, default=list)
    intent = Column(String, default="FastPath")
    response = Column(String)
    quick_actions = Column(JSON, default=list)
    priority = Column(Integer, default=1)
    enabled = Column(Boolean, default=True)

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
