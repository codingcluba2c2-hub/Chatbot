# backend/schemas/admin.py
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
import uuid
import time

class BaseEntity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    created_by: str = "system"
    updated_by: str = "system"
    status: str = "active"

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

class FarewellBase(BaseModel):
    name: str
    intent: str = "Farewell"
    priority: int = 1
    alias: List[str] = Field(default_factory=list)
    regex: Optional[str] = None
    response: str = ""
    enabled: bool = True

class Farewell(BaseEntity, FarewellBase):
    pass

class FAQBase(BaseModel):
    question: str
    aliases: List[str] = []
    answer: str
    category: str = "general"
    keywords: List[str] = []
    priority: int = 1
    language: str = "en"
    enabled: bool = True

class FAQ(BaseEntity, FAQBase):
    pass

class FastPathBase(BaseModel):
    trigger: str
    aliases: List[str] = []
    intent: str = "FastPath"
    response: str
    quick_actions: List[str] = []
    priority: int = 1
    enabled: bool = True

class FastPath(BaseEntity, FastPathBase):
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
