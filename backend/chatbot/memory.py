from chatbot.pipeline import PipelineStep, PipelineStepResult, PipelineContext
"""
Purpose: Memory management.
Responsibilities: Store and retrieve history.
Flow: Start and end of pipeline.
"""

from chatbot.pipeline import PipelineContext
from chatbot.pipeline import PipelineResult
from typing import Dict, Any, List, Optional
from typing import Optional, Tuple
import re
import time


class MemoryDetectorStep(PipelineStep):
    def __init__(self):
        super().__init__()
        # Patterns for UPDATE
        self.update_patterns = [
            (r"(?i)^(?:my name is|i'm|i am|call me|you can call me|remember my name is|remember me as|save my name as|my name's|my new name is) (.+)", "user_name"),
            (r"(?i)^(?:change my name to|update my name to|update my name) (.+)", "user_name"),
            (r"(?i)^(?:i call you|i can call you|call yourself|your name is|your nickname is|i want to call you|from now on i'll call you) (.+)", "assistant_name")
        ]
        
        # Patterns for DELETE
        self.delete_patterns = [
            (r"(?i)^(?:forget my name|clear my name|delete my name)", "user_name")
        ]
        
        # Patterns for LOOKUP
        self.lookup_patterns = [
            (r"(?i)\b(?:what's my name|what is my name|who am i|do you know my name|what do you call me|what should you call me|my name)\b", "user_name"),
            (r"(?i)\b(?:what's your name|what is your name|who are you|what do i call you|your name)\b", "assistant_name")
        ]

    def _extract_name(self, text: str) -> str:
        # Simple cleanup (e.g., remove trailing punctuation)
        return re.sub(r'[^\w\s]', '', text).strip().title()

    def process(self, context: PipelineContext) -> PipelineResult:
        t0 = time.perf_counter()
        text = context.normalized_message.strip()
        memory = context.metadata.get("memory", {})
        
        # Check DELETE first
        for pattern, field in self.delete_patterns:
            if re.search(pattern, text):
                t1 = time.perf_counter()
                context.metadata["memory_intent"] = "DELETE"
                context.metadata["detected_field"] = field
                context.metadata["previous_value"] = memory.get(field)
                context.metadata["updated_value"] = None
                context.metadata["storage"] = "localStorage"
                context.metadata["execution_time_ms"] = int((t1 - t0) * 1000)
                
                context.current_intent = "Memory (Delete)"
                return PipelineResult(
                    continue_pipeline=False,
                    stop=True,
                    intent="Memory (Delete)",
                    response="Okay. I've forgotten your saved name.",
                    actions=[{"type": "UPDATE_MEMORY", "payload": {field: None}}]
                )
        
        # Check UPDATE
        for pattern, field in self.update_patterns:
            match = re.match(pattern, text)
            if match:
                value = self._extract_name(match.group(1))
                t1 = time.perf_counter()
                
                context.metadata["memory_intent"] = "UPDATE"
                context.metadata["detected_field"] = field
                context.metadata["previous_value"] = memory.get(field)
                context.metadata["updated_value"] = value
                context.metadata["storage"] = "localStorage"
                context.metadata["execution_time_ms"] = int((t1 - t0) * 1000)
                
                context.current_intent = "Memory (Update)"
                
                # Dynamic response
                response_text = ""
                if field == "user_name":
                    if "change" in text.lower() or "update" in text.lower():
                        response_text = f"Done! I'll remember your name as **{value}**."
                    elif "call me" in text.lower():
                        response_text = f"Sure! I'll call you **{value}** from now on."
                    else:
                        response_text = f"Nice to meet you, **{value}**! I'll remember your name."
                elif field == "assistant_name":
                    response_text = f"Sounds good! You can call me **{value}**."
                    
                return PipelineResult(
                    continue_pipeline=False,
                    stop=True,
                    intent="Memory (Update)",
                    response=response_text,
                    actions=[{"type": "UPDATE_MEMORY", "payload": {field: value, "preferred_name": value if field == "user_name" else memory.get("preferred_name")}}]
                )
                
        # Check LOOKUP
        lookup_responses = []
        matched_fields = []
        
        for pattern, field in self.lookup_patterns:
            if re.search(pattern, text):
                if field in matched_fields:
                    continue
                matched_fields.append(field)
                val = memory.get(field)
                
                if field == "user_name":
                    if val:
                        resp = f"Your name is **{val}**." if "what" in text.lower() else f"You're **{val}**."
                        if "what do you call me" in text.lower():
                            resp = f"I call you **{val}**."
                        lookup_responses.append(resp)
                    else:
                        lookup_responses.append("I don't know your name yet. What should I call you?")
                elif field == "assistant_name":
                    if val:
                        lookup_responses.append(f"You can call me **{val}**.")
                    else:
                        lookup_responses.append("I am Mobiloitte AI Assistant.")
                        
        if lookup_responses:
            t1 = time.perf_counter()
            context.metadata["memory_intent"] = "LOOKUP"
            context.metadata["detected_fields"] = matched_fields
            context.metadata["storage"] = "localStorage"
            context.metadata["execution_time_ms"] = int((t1 - t0) * 1000)
            
            context.current_intent = "Memory (Lookup)"
            
            final_resp = " ".join(lookup_responses)
            greeting_prefix = context.metadata.get("greeting_prefix", "")
            if greeting_prefix:
                final_resp = f"{greeting_prefix}\n\n{final_resp}"
                
            return PipelineResult(
                continue_pipeline=False,
                stop=True,
                intent="Memory (Lookup)",
                response=final_resp
            )
                
        return PipelineResult(continue_pipeline=True)



from typing import Dict, Any, List, Optional
import time
from core.database import conversation_repo, message_repo, fact_repo

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

    @classmethod
    def add_structured_turn(cls, session_id: str, turn_data: Dict[str, Any]):
        cls._initialize_memory(session_id)
        turns = cls.get_fact(session_id, "structured_turns") or []
        turns.append(turn_data)
        
        # Keep last 10 turns to avoid blowing up memory size
        if len(turns) > 10:
            turns = turns[-10:]
            
        cls.add_fact(session_id, "structured_turns", turns)


# backend/services/session_manager.py
import uuid
import time
from typing import Dict, Any, Optional

class SessionManager:
    # In-memory storage: session_id -> session_data
    _sessions: Dict[str, Dict[str, Any]] = {}
    SESSION_TTL = 3600 * 24 # 24 hours

    @classmethod
    def generate_session_id(cls) -> str:
        return str(uuid.uuid4())

    @classmethod
    def create_session(cls, session_id: Optional[str] = None) -> str:
        """Returns existing session_id or creates a new one."""
        if session_id and session_id in cls._sessions:
            cls._sessions[session_id]["updated_at"] = time.time()
            return session_id
            
        new_session_id = session_id or cls.generate_session_id()
        cls._sessions[new_session_id] = {
            "session_id": new_session_id,
            "created_at": time.time(),
            "updated_at": time.time(),
        }
        return new_session_id

    @classmethod
    def get_session(cls, session_id: str) -> Optional[Dict[str, Any]]:
        cls.expire_sessions()
        session = cls._sessions.get(session_id)
        if session:
            session["updated_at"] = time.time()
        return session

    @classmethod
    def update_session(cls, session_id: str, data: Dict[str, Any]):
        if session_id in cls._sessions:
            cls._sessions[session_id].update(data)
            cls._sessions[session_id]["updated_at"] = time.time()

    @classmethod
    def delete_session(cls, session_id: str):
        if session_id in cls._sessions:
            del cls._sessions[session_id]

    @classmethod
    def expire_sessions(cls):
        current_time = time.time()
        expired = [sid for sid, data in cls._sessions.items() if current_time - data["updated_at"] > cls.SESSION_TTL]
        for sid in expired:
            del cls._sessions[sid]
            
    @classmethod
    def clear_session_data(cls, session_id: str):
        if session_id in cls._sessions:
            cls._sessions[session_id] = {
                "session_id": session_id,
                "created_at": time.time(),
                "updated_at": time.time(),
            }


# backend/services/memory_lookup_service.py
import re
from typing import Optional, Tuple
from chatbot.memory import ConversationMemoryService

class MemoryLookupService:
    # Mapping of question patterns to fact keys
    LOOKUP_PATTERNS = [
        (r"(?i)who am i\??", "user_name"),
        (r"(?i)what is my name\??", "user_name"),
        (r"(?i)where do i live\??", "location"),
        (r"(?i)what is my location\??", "location"),
        (r"(?i)where do i work\??", "company"),
        (r"(?i)what is my company\??", "company"),
        (r"(?i)what is my email\??", "email"),
        (r"(?i)what is my phone number\??", "phone_number"),
        (r"(?i)what is my profession\??", "profession"),
        (r"(?i)what is my favorite language\??", "favorite_language"),
        (r"(?i)what do i like\??", "interest")
    ]
    
    # Mapping of fact keys to response templates
    RESPONSE_TEMPLATES = {
        "user_name": "Your name is {value}.",
        "location": "Your location is {value}.",
        "company": "You work at {value}.",
        "email": "Your email is {value}.",
        "phone_number": "Your phone number is {value}.",
        "profession": "Your profession is {value}.",
        "favorite_language": "Your favorite language is {value}.",
        "interest": "You like {value}."
    }

    @classmethod
    def check_memory(cls, session_id: str, text: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Returns: (is_found, matched_key, response_message)
        """
        for pattern, fact_key in cls.LOOKUP_PATTERNS:
            if re.search(pattern, text):
                fact_value = ConversationMemoryService.get_fact(session_id, fact_key)
                if fact_value:
                    template = cls.RESPONSE_TEMPLATES.get(fact_key, "I remember that your " + fact_key + " is {value}.")
                    response = template.format(value=fact_value)
                    return True, fact_key, response
                else:
                    return False, fact_key, f"I don't know your {fact_key.replace('_', ' ')} yet. You haven't told me."
                    
        return False, None, None


# backend/services/response_service.py
import datetime
import re

class ResponseService:
    @staticmethod
    def get_fallback() -> str:
        return FALLBACK_MESSAGE

    @staticmethod
    def adjust_for_time_of_day(response: str) -> str:
        hour = datetime.datetime.now().hour
        if hour < 12:
            correct_greeting = "Good morning"
        elif 12 <= hour < 17:
            correct_greeting = "Good afternoon"
        else:
            correct_greeting = "Good evening"
            
        pattern = re.compile(r'(good\s+(morning|afternoon|evening))', re.IGNORECASE)
        
        def replacer(match):
            orig = match.group(1)
            if orig[0].isupper():
                return correct_greeting
            return correct_greeting.lower()
            
        return pattern.sub(replacer, response)

    def format_response(self, text: str, context: dict = None) -> str:
        from chatbot.detector import FALLBACK_MESSAGE
        if not text:
            return FALLBACK_MESSAGE

    @staticmethod
    def get_sequential_response(session_id: str, intent_key: str, raw_response: str) -> str:
        if not raw_response:
            return ""
            
        responses = [r.strip() for r in raw_response.split('||') if r.strip()]
        if not responses:
            return raw_response
            
        session = SessionManager.get_session(session_id)
        if not session:
            SessionManager.create_session(session_id)
            session = SessionManager.get_session(session_id) or {}
            
        counters = session.get("response_counters", {})
        count = counters.get(intent_key, 0)
        
        selected_response = responses[count % len(responses)]
        
        counters[intent_key] = count + 1
        session["response_counters"] = counters
        SessionManager.update_session(session_id, session)
        
        return ResponseService.adjust_for_time_of_day(selected_response)


