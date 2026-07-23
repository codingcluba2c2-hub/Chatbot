"""
Purpose: Database connection and CRUD helpers.
Responsibilities: Manage DB session.
Flow: Core infrastructure.
"""

from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy import event
from sqlalchemy import or_, desc, asc
from sqlalchemy.orm import Session
from sqlalchemy.orm import declarative_base, sessionmaker
from typing import List, Optional, Dict, Any
from typing import TypeVar, Generic, Type, List, Optional, Dict, Any
import time
import uuid
from core.config import POSTGRES_URL
from core.config import POSTGRES_URL


engine = create_engine(
    POSTGRES_URL, 
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,
    max_overflow=10,
    connect_args={
        "connect_timeout": 30
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@event.listens_for(engine, "connect")
def on_connect(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
    cursor.close()

Base = declarative_base()

from core.models import *
from core.schemas import *


# backend/repositories/base_repository.py

T = TypeVar("T", bound=BaseModel)
D = TypeVar("D") # DB Model

class BaseRepository(Generic[T, D]):
    def __init__(self, pydantic_model: Type[T], db_model: Type[D] = None):
        self.model = pydantic_model
        self.db_model = db_model
        
    def _to_pydantic(self, db_obj: Any) -> T:
        if not db_obj:
            return None
        # Convert SQLAlchemy object to dictionary, then to Pydantic
        obj_dict = {}
        for prop in self.db_model.__mapper__.column_attrs:
            attr_name = prop.key
            col_name = prop.columns[0].name
            obj_dict[col_name] = getattr(db_obj, attr_name)
        return self.model(**obj_dict)

    def _invalidate_cache(self):
        if hasattr(self, "_cache"):
            self._cache.clear()
            self._cache_times.clear()

    def get_all(self, skip: int = 0, limit: int = 100, sort_by: str = "created_at", descending: bool = True, query: str = None) -> List[T]:
        if not self.db_model:
            return []
            
        cache_key = f"get_all_{skip}_{limit}_{sort_by}_{descending}_{query}"
        
        if not hasattr(self, "_cache"):
            self._cache = {}
            self._cache_times = {}
            
        now = time.time()
        if cache_key in self._cache and (now - self._cache_times.get(cache_key, 0)) < 3600:
            return self._cache[cache_key]
            
        from sqlalchemy.exc import OperationalError
        
        max_retries = 2
        for attempt in range(max_retries):
            try:
                with SessionLocal() as session:
                    stmt = session.query(self.db_model)
                    
                    if query:
                        # Basic search on string columns
                        query_lower = f"%{query.lower()}%"
                        string_columns = [c for c in self.db_model.__table__.columns if c.type.python_type is str]
                        if string_columns:
                            filters = [c.ilike(query_lower) for c in string_columns]
                            if filters:
                                stmt = stmt.filter(or_(*filters))
                                
                    if hasattr(self.db_model, sort_by):
                        sort_col = getattr(self.db_model, sort_by)
                        if descending:
                            stmt = stmt.order_by(desc(sort_col))
                        else:
                            stmt = stmt.order_by(asc(sort_col))
                    else:
                        if hasattr(self.db_model, "created_at"):
                            stmt = stmt.order_by(desc(self.db_model.created_at))
                            
                    stmt = stmt.offset(skip).limit(limit)
                    db_items = stmt.all()
                    
                    results = [self._to_pydantic(item) for item in db_items if item is not None]
                    
                    self._cache[cache_key] = results
                    self._cache_times[cache_key] = now
                    
                    return results
            except OperationalError:
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    raise
        return []
    def get_by_id(self, item_id: str) -> Optional[T]:
        if not self.db_model:
            return None
            
        with SessionLocal() as session:
            db_item = session.query(self.db_model).filter(self.db_model.id == item_id).first()
            return self._to_pydantic(db_item)
        
    def create(self, item: BaseModel) -> T:
        if not self.db_model:
            # Fallback if db_model is missing
            return self.model(**item.model_dump())
            
        db_item = self.model(**item.model_dump())
        item_dict = db_item.model_dump()
        
        db_obj = self.db_model(**item_dict)
        
        with SessionLocal() as session:
            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)
            self._invalidate_cache()
            return self._to_pydantic(db_obj)
        
    def update(self, item_id: str, update_data: BaseModel) -> Optional[T]:
        if not self.db_model:
            return None
            
        with SessionLocal() as session:
            db_obj = session.query(self.db_model).filter(self.db_model.id == item_id).first()
            if not db_obj:
                return None
                
            update_dict = update_data.model_dump(exclude_unset=True)
            for key, value in update_dict.items():
                if hasattr(db_obj, key) and key not in ["id", "created_at"]:
                    setattr(db_obj, key, value)
                    
            if hasattr(db_obj, "updated_at"):
                db_obj.updated_at = time.time()
                
            session.commit()
            session.refresh(db_obj)
            self._invalidate_cache()
            return self._to_pydantic(db_obj)
        
    def delete(self, item_id: str) -> bool:
        if not self.db_model:
            return False
            
        with SessionLocal() as session:
            db_obj = session.query(self.db_model).filter(self.db_model.id == item_id).first()
            if db_obj:
                session.delete(db_obj)
                session.commit()
                self._invalidate_cache()
                return True
            return False

    def count(self) -> int:
        if not self.db_model:
            return 0
            
        with SessionLocal() as session:
            return session.query(self.db_model).count()



class ConversationRepository:
    def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        with SessionLocal() as db:
            item = db.query(ConversationDB).filter(ConversationDB.id == id).first()
            if item:
                return {"id": item.id, "user_id": item.user_id, "created_at": item.created_at, "updated_at": item.updated_at}
            return None
            
    def create(self, id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        with SessionLocal() as db:
            now = time.time()
            item = ConversationDB(id=id, user_id=user_id, created_at=now, updated_at=now)
            db.add(item)
            db.commit()
            return {"id": item.id, "user_id": item.user_id, "created_at": item.created_at, "updated_at": item.updated_at}

class MessageRepository:
    def get_by_conversation(self, conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        with SessionLocal() as db:
            items = db.query(MessageDB).filter(
                MessageDB.conversation_id == conversation_id
            ).order_by(MessageDB.created_at.desc()).limit(limit).all()
            
            return [
                {
                    "id": item.id,
                    "conversation_id": item.conversation_id,
                    "role": item.role,
                    "message": item.message,
                    "intent": item.intent,
                    "created_at": item.created_at
                }
                for item in reversed(items)
            ]
            
    def add_message(self, conversation_id: str, role: str, message: str, intent: Optional[str] = None):
        with SessionLocal() as db:
            item = MessageDB(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                role=role,
                message=message,
                intent=intent,
                created_at=time.time()
            )
            db.add(item)
            db.commit()

class FactRepository:
    def get_by_session(self, session_id: str) -> Dict[str, Any]:
        with SessionLocal() as db:
            now = time.time()
            items = db.query(MemoryFactDB).filter(
                MemoryFactDB.session_id == session_id
            ).all()
            
            valid_facts = {}
            for item in items:
                if item.expires_at is None or item.expires_at > now:
                    valid_facts[item.key] = item.value
                else:
                    db.delete(item)
            db.commit()
            return valid_facts
            
    def set_fact(self, session_id: str, key: str, value: Any, expires_at: Optional[float] = None):
        with SessionLocal() as db:
            existing = db.query(MemoryFactDB).filter(
                MemoryFactDB.session_id == session_id,
                MemoryFactDB.key == key
            ).first()
            
            if existing:
                existing.value = value
                existing.expires_at = expires_at
            else:
                new_fact = MemoryFactDB(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    key=key,
                    value=value,
                    expires_at=expires_at,
                    created_at=time.time()
                )
                db.add(new_fact)
            db.commit()


# backend/repositories/registry.py


class AuditLogRepository(BaseRepository[AuditLog, AuditLogDB]):
    pass

class GreetingRepository(BaseRepository[Greeting, GreetingDB]):
    pass


class FAQRepository(BaseRepository[FAQ, FAQDB]):
    pass




class DocumentRepository(BaseRepository[KnowledgeDocument, KnowledgeDocumentDB]):
    pass

class ChunkRepository(BaseRepository[DocumentChunk, DocumentChunkDB]):
    pass

class KnowledgeSettingsRepository(BaseRepository[KnowledgeSettings, KnowledgeSettingsDB]):
    pass


_instances = {}

def _get_repo(name: str):
    if name not in _instances:
        if name == "audit_repo":
            _instances[name] = AuditLogRepository(AuditLog, AuditLogDB)
        elif name == "greeting_repo":
            _instances[name] = GreetingRepository(Greeting, GreetingDB)
        elif name == "faq_repo":
            _instances[name] = FAQRepository(FAQ, FAQDB)

        elif name == "document_repo":
            _instances[name] = DocumentRepository(KnowledgeDocument, KnowledgeDocumentDB)
        elif name == "chunk_repo":
            _instances[name] = ChunkRepository(DocumentChunk, DocumentChunkDB)
        elif name == "settings_repo":
            _instances[name] = KnowledgeSettingsRepository(KnowledgeSettings, KnowledgeSettingsDB)
        elif name == "settings_repo":
            _instances[name] = KnowledgeSettingsRepository(KnowledgeSettings, KnowledgeSettingsDB)
        elif name == "conversation_repo":
            _instances[name] = ConversationRepository()
        elif name == "message_repo":
            _instances[name] = MessageRepository()
        elif name == "fact_repo":
            _instances[name] = FactRepository()

        else:
            raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return _instances[name]

def __getattr__(name):
    if name in ["audit_repo", "greeting_repo", "faq_repo", 
                "document_repo", "chunk_repo", "settings_repo", 
                "conversation_repo", "message_repo", "fact_repo"]:
        return _get_repo(name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

# Function to record audit logs
def log_audit(action: str, entity_type: str, entity_id: str, old_value=None, new_value=None, user: str = "system"):
    _get_repo("audit_repo").create(AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=old_value,
        new_value=new_value,
        user=user
    ))


# backend/repositories/seed.py

def seed_data():
    if greeting_repo.count() == 0:
        for g in GREETING_RESPONSES:
            greeting_repo.create(Greeting(name="Default Greeting", response=g))
            
# Seed data will be called from app.py during startup


