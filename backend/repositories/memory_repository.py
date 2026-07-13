from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from models.memory import ConversationDB, MessageDB, MemoryFactDB
from core.database import SessionLocal
import time
import uuid

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
