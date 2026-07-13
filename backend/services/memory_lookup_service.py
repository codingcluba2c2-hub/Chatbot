# backend/services/memory_lookup_service.py
import re
from typing import Optional, Tuple
from services.conversation_memory_service import ConversationMemoryService

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
