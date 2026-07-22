import json
import os
import re
from typing import Dict, Tuple, Any
from chatbot.pipeline import PipelineStep, PipelineContext, PipelineResult
from chatbot.memory import ConversationMemoryService
from core.logger import get_logger
import time

logger = get_logger(__name__)

# Leetspeak map for normalization
LEET_MAP = {
    '0': 'o',
    '1': 'i',
    '3': 'e',
    '4': 'a',
    '5': 's',
    '7': 't',
    '@': 'a',
    '$': 's'
}

def normalize_for_abuse(text: str) -> str:
    """
    Normalizes input text to defeat basic abuse obfuscation tactics.
    - lowercase
    - replace leetspeak
    - remove punctuation
    - deduplicate repeated characters
    - remove spaces to catch "f u c k"
    """
    if not text:
        return ""
    
    # Lowercase
    t = text.lower()
    
    # Replace leetspeak
    for k, v in LEET_MAP.items():
        t = t.replace(k, v)
        
    # Remove punctuation & whitespace (to catch spaced out words or symbols)
    # Keeping only letters and numbers
    t = re.sub(r'[^a-z0-9]', '', t)
    
    # Deduplicate repeating characters (e.g., fuuuuck -> fuck)
    # We keep only 1 of each consecutive character. 
    # E.g. 'hello' -> 'helo', 'asshole' -> 'ashole'.
    # Because this destroys some valid double letters, we do the same 
    # to the dictionary words later for fuzzy matching if exact fails.
    if t:
        deduped = t[0]
        for char in t[1:]:
            if char != deduped[-1]:
                deduped += char
        t = deduped
        
    return t

def get_abuse_dictionary() -> Dict[str, str]:
    dict_path = os.path.join(os.path.dirname(__file__), "abuse_dict.json")
    try:
        with open(dict_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load abuse dictionary: {e}")
        return {}

class AbuseDetectionStep(PipelineStep):
    def __init__(self):
        # Dictionary is loaded dynamically in process() to support real-time updates
        pass

    def process(self, context: PipelineContext) -> PipelineResult:
        t0 = time.perf_counter()
        original_text = context.normalized_message
        
        abuse_dict = get_abuse_dictionary()
        if not original_text or not abuse_dict:
            return PipelineResult(continue_pipeline=True)
            
        deduped_dict = {
            normalize_for_abuse(k): (k, v) for k, v in abuse_dict.items()
        }
            
        # 1. Normalize
        normalized_str = normalize_for_abuse(original_text)
        
        detected_keyword = None
        severity = None
        method = None
        
        # 2. Check exact matches on original tokenized words first
        # This catches normal usage without over-triggering on substrings
        for word in original_text.lower().split():
            clean_word = re.sub(r'[^a-z0-9]', '', word)
            if clean_word in abuse_dict:
                detected_keyword = clean_word
                severity = abuse_dict[clean_word]
                method = "Exact Word Match"
                break
                
        # 3. If no exact match, check fuzzy/regex match on the heavily normalized string
        # We use word boundaries to prevent substring matches (e.g. 'salary' matching 'sala')
        if not detected_keyword:
            for deduped_word, (original_word, sev) in deduped_dict.items():
                if re.search(rf'\b{re.escape(deduped_word)}\b', normalized_str):
                    detected_keyword = original_word
                    severity = sev
                    method = "Regex Boundary Match"
                    break
                    
        # No abuse found
        if not detected_keyword:
            return PipelineResult(continue_pipeline=True)
            
        # Abuse found, track in memory
        session_id = context.session_id
        memory = ConversationMemoryService.get_memory(session_id)
        facts = memory.get("facts", {})
        abuse_count = facts.get("abuse_count", 0) + 1
        
        # Update memory fact
        from core.database import fact_repo
        fact_repo.set_fact(session_id, "abuse_count", abuse_count)
        
        # Determine enterprise response
        response_text = ""
        
        if abuse_count >= 3:
            response_text = "I can no longer assist you due to repeated abusive language. This conversation has been temporarily paused. Please return when you are ready to communicate respectfully."
        elif abuse_count == 2:
            response_text = "This is a final warning. I will not tolerate abusive or offensive language. Please ask your question respectfully, or I will end the conversation."
        else:
            # 1st offense depends on severity
            if severity == "LOW":
                response_text = "I'm here to help. Let's keep our conversation respectful."
            elif severity == "MEDIUM":
                response_text = "I'd be happy to help, but please avoid offensive language."
            else: # HIGH
                response_text = "I can't assist with abusive language. If you'd like help with a question, please ask respectfully."
                
        # Record Developer Metadata
        t1 = time.perf_counter()
        context.metadata["Abuse detected"] = True
        context.metadata["Matched keyword"] = detected_keyword
        context.metadata["Severity"] = severity
        context.metadata["Normalization result"] = normalized_str
        context.metadata["Detection method"] = method
        context.metadata["Abuse count"] = abuse_count
        context.metadata["Pipeline stopped"] = True
        context.metadata["execution_time_ms"] = int((t1 - t0) * 1000)
        
        logger.warning(f"Abuse detected (Severity: {severity}, Word: {detected_keyword}, Offense: {abuse_count})")
        
        return PipelineResult(
            continue_pipeline=False,
            stop=True,
            intent="Abuse",
            response=response_text
        )
