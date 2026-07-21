from typing import Dict, Any, List, Optional
import time
from repositories.registry import conversation_repo, message_repo, fact_repo

class ConversationMemoryService:
    @classmethod
    def _initialize_memory(cls, session_id: str, conversation_id: Optional[str] = None):
        # We use session_id as conversation_id in this context for simplicity if not provided
        conv_id = conversation_id or session_id
        existing = conversation_repo.get_by_id(conv_id)
        if not existing:
            conversation_repo.create(id=conv_id)
            
    @classmethod
    def get_memory(cls, session_id: str) -> Dict[str, Any]:
        cls._initialize_memory(session_id)
        messages = message_repo.get_by_conversation(session_id)
        facts = fact_repo.get_by_session(session_id)
        
        # We must format messages to match what the old in-memory dict expected:
        # "role", "content" (which is 'message' in DB), "intent"
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "role": msg["role"],
                "content": msg["message"],
                "intent": msg["intent"],
                "timestamp": msg["created_at"]
            })
            
        # AI Safety: Sliding Window Context Truncation
        # Keep only the last 10 messages to prevent context window overflow
        max_messages = 10
        if len(formatted_messages) > max_messages:
            formatted_messages = formatted_messages[-max_messages:]
            
        return {
            "conversation_id": session_id,
            "session_id": session_id,
            "messages": formatted_messages,
            "facts": facts,
            "entities": facts.get("entities", {}), # Store entities inside facts for now
            "preferences": facts.get("preferences", {}),
            "summary": facts.get("summary", []),
            "metadata": facts.get("metadata", {})
        }
        
    @classmethod
    def clear_memory(cls, session_id: str):
        # Not fully implemented deletion of all messages, but we can clear facts
        fact_repo.set_fact(session_id, "facts", {})
        fact_repo.set_fact(session_id, "entities", {})
            
    @classmethod
    def add_message(cls, session_id: str, role: str, content: str, intent: Optional[str] = None, trace: Optional[Dict] = None, conversation_id: Optional[str] = None):
        conv_id = conversation_id or session_id
        cls._initialize_memory(session_id, conv_id)
        message_repo.add_message(
            conversation_id=conv_id,
            role=role,
            message=content,
            intent=intent
        )

    @classmethod
    def add_fact(cls, session_id: str, key: str, value: Any):
        cls._initialize_memory(session_id)
        # Store individual fact
        fact_repo.set_fact(session_id, key, value)

    @classmethod
    def get_fact(cls, session_id: str, key: str) -> Optional[Any]:
        facts = fact_repo.get_by_session(session_id)
        return facts.get(key)
        
    @classmethod
    def add_entity(cls, session_id: str, entity_type: str, value: str):
        cls._initialize_memory(session_id)
        facts = fact_repo.get_by_session(session_id)
        entities = facts.get("entities", {})
        
        if entity_type not in entities:
            entities[entity_type] = []
        if value not in entities[entity_type]:
            entities[entity_type].append(value)
            
        fact_repo.set_fact(session_id, "entities", entities)

    @classmethod
    def get_context(cls, session_id: str) -> Dict[str, Any]:
        cls._initialize_memory(session_id)
        context = fact_repo.get_by_session(session_id).get("conversation_context", {})
        return {
            "conversation_id": context.get("conversation_id", session_id),
            "current_topic": context.get("current_topic", ""),
            "last_intent": context.get("last_intent", ""),
            "last_entities": context.get("last_entities", []),
            "last_memory_operation": context.get("last_memory_operation", ""),
            "last_knowledge_node": context.get("last_knowledge_node", ""),
            "last_rag_document": context.get("last_rag_document", ""),
            "last_selected_button": context.get("last_selected_button", "")
        }

    @classmethod
    def update_context(cls, session_id: str, new_data: Dict[str, Any]):
        cls._initialize_memory(session_id)
        current_context = cls.get_context(session_id)
        current_context.update(new_data)
        fact_repo.set_fact(session_id, "conversation_context", current_context)
