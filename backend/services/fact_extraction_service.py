# backend/services/fact_extraction_service.py
import re
from typing import Dict, Any
from services.conversation_memory_service import ConversationMemoryService

class FactExtractionService:
    # Patterns to extract facts. Format: (regex_pattern, fact_key, group_index)
    PATTERNS = [
        (r"(?i)my name is\s+([a-zA-Z\s]+)", "user_name", 1),
        (r"(?i)i live in\s+([a-zA-Z\s]+)", "location", 1),
        (r"(?i)i work (?:in|at)\s+([a-zA-Z\s]+)", "company", 1),
        (r"(?i)i am (?:a|an)\s+([a-zA-Z\s]+(?:developer|engineer|designer|manager|architect|programmer))", "profession", 1),
        (r"(?i)my favorite language is\s+([a-zA-Z\+#]+)", "favorite_language", 1),
        (r"(?i)i like\s+([a-zA-Z\s]+)", "interest", 1),
        (r"(?i)my email is\s+([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", "email", 1),
        (r"(?i)my phone number is\s+([\d\-\+\s]+)", "phone_number", 1)
    ]
    
    @classmethod
    def extract_and_store(cls, session_id: str, text: str) -> Dict[str, str]:
        extracted_facts = {}
        for pattern, key, group_index in cls.PATTERNS:
            match = re.search(pattern, text)
            if match:
                value = match.group(group_index).strip()
                ConversationMemoryService.add_fact(session_id, key, value)
                extracted_facts[key] = value
                
        return extracted_facts
