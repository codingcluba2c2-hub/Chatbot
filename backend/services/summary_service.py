# backend/services/summary_service.py
from typing import List, Dict, Any
from services.conversation_memory_service import ConversationMemoryService
import time

class SummaryService:
    @classmethod
    def generate_summary(cls, session_id: str):
        """
        Generates a deterministic summary of the conversation based on intents.
        Without AI, this maps intents to sentences.
        """
        memory = ConversationMemoryService.get_memory(session_id)
        messages = memory.get("messages", [])
        
        # Keep existing summary items
        summary = memory.get("summary", [])
        
        for msg in messages:
            if msg["role"] == "user" and msg.get("intent"):
                intent = msg["intent"]
                sentence = ""
                if intent == "Greeting":
                    sentence = "User introduced himself."
                elif intent == "FastPath":
                    sentence = "User asked about a specific topic."
                elif intent == "MemoryLookup":
                    sentence = "User asked to recall a stored fact."
                elif intent == "Gibberish":
                    sentence = "User entered unrecognized text."
                elif intent == "FAQ":
                    content = msg.get("content", "").lower()
                    if "policy" in content:
                        if "leave" in content:
                            sentence = "Asked leave policy."
                        elif "company" in content:
                            sentence = "Asked company policy."
                        else:
                            sentence = "Asked about policies."
                    elif "hours" in content or "working" in content:
                        sentence = "Asked working hours."
                    else:
                        sentence = "Asked an FAQ."
                elif intent == "Farewell":
                    sentence = "User said goodbye."
        
                if sentence and sentence not in summary:
                    summary.append(sentence)
                    
        memory["summary"] = summary
        memory["updated_at"] = time.time()
