import json
import time
from typing import Dict, Any, Optional
from core.database import fact_repo
from core.logger import get_logger

logger = get_logger(__name__)

class ConversationStateManager:
    """
    Enterprise Conversation State Manager.
    Maintains a single source of truth for the active entity and context of a conversation.
    """
    
    @classmethod
    def get_state(cls, session_id: str) -> Dict[str, Any]:
        """
        Retrieves the latest conversational state.
        """
        facts = fact_repo.get_by_session(session_id)
        return facts.get("conversation_state", {})
        
    @classmethod
    def update_state(cls, session_id: str, new_state: Dict[str, Any]):
        """
        Overwrites/updates the current conversation state.
        """
        current = cls.get_state(session_id)
        
        # Merge new state elements over the old state
        for k, v in new_state.items():
            current[k] = v
            
        current["timestamp"] = time.time()
        
        # Save as a single key-value fact
        fact_repo.set_fact(session_id, "conversation_state", current)
