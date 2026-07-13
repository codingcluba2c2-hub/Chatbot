# backend/services/entity_extraction_service.py
import re
from typing import Dict, List
from services.conversation_memory_service import ConversationMemoryService

class EntityExtractionService:
    # Deterministic entity extractors using capture groups or full match
    ENTITY_PATTERNS = {
        "Email": r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7})",
        "Phone": r"(\+?[0-9\-\s\(\)]{10,15})",
        "Date": r"(\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4})\b)",
        "Time": r"(\b(?:[01]?\d|2[0-3]):[0-5]\d(?::[0-5]\d)?\s*(?:[aApP]\.?[mM]\.?)\b)",
        "Person": r"(?i)\b(?:name is|i am|this is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b",
        "Organization": r"(?i)\b(?:from|represent|for)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?(?:Inc\.|LLC|Corp\.|Ltd\.)?)\b",
        "Company": r"(?i)\b(?:work at|company is|work in)\s+([A-Z][a-zA-Z0-9&]+(?:\s+[A-Z][a-zA-Z0-9&]+)*)\b",
        "City": r"(?i)\b(?:live in|from|city of)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b",
        "State": r"(?i)\b(?:state of|in state)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b",
        "Country": r"(?i)\b(?:country of|in country)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b",
        "Department": r"(?i)\b(?:in the|department is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\s+Department)\b",
        "Designation": r"(?i)\b(?:role is|as a|as an|am a)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?(?:Manager|Engineer|Developer|Director|Lead|Specialist))\b"
    }

    @classmethod
    def extract_and_store(cls, session_id: str, text: str) -> Dict[str, List[str]]:
        extracted_entities = {}
        for entity_type, pattern in cls.ENTITY_PATTERNS.items():
            for match in re.finditer(pattern, text):
                # Use the first capture group if it exists, otherwise the full match
                clean_match = match.group(1).strip() if match.lastindex else match.group(0).strip()
                if clean_match:
                    if entity_type not in extracted_entities:
                        extracted_entities[entity_type] = []
                    
                    ConversationMemoryService.add_entity(session_id, entity_type, clean_match)
                    extracted_entities[entity_type].append(clean_match)
                    
        return extracted_entities
