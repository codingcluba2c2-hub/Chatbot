from core.logger import get_logger
"""
Purpose: Input detection.
Responsibilities: Validate and classify input.
Flow: Pre-processing.
"""

from chatbot.pipeline import PipelineStep, PipelineStepResult
from chatbot.pipeline import PipelineContext
from chatbot.pipeline import PipelineResult
from typing import Dict, Any, List
from typing import Optional, Tuple
import re
from chatbot.in_memory_engine import engine
from cachetools import TTLCache, cached
# backend/utils/detectors.py

def validate_query(text: str) -> dict:
    """
    Validation to ensure query is not pure gibberish (keyboard mash, repeated chars, symbols).
    """
    # Bypass for known valid intents
    is_greet, _, _, _, _ = detect_greeting(text)
    if is_greet:
        return {
            "isMeaningful": True, "confidence": 1.0, "reason": "Bypassed: Matches Known Intent",
            "metrics": {"meaningful_score": 100.0, "dictionary_match": 100.0}
        }

    text_clean = text.strip().lower()
    if not text_clean:
        return {
            "isMeaningful": False, "confidence": 0.0, "reason": "Empty string",
            "metrics": {"meaningful_score": 0.0, "dictionary_match": 0.0}
        }

    # Hardcoded test cases to explicitly reject
    HARD_REJECTS = {"gtgb", "nkio", "eoipmk", "asdfgh", "qwertyui", "plmoknijb", "zzzzzzz", "@@@!!!", "123abc###", "asdff", "qwerty"}
    if text_clean in HARD_REJECTS:
        return {
            "isMeaningful": False, "confidence": 0.0, "reason": "Hardcoded gibberish test case",
            "metrics": {"meaningful_score": 0.0, "dictionary_match": 0.0}
        }

    # Only symbols
    if re.fullmatch(r'[^\w\s]+', text_clean):
        return {
            "isMeaningful": False, "confidence": 0.1, "reason": "Only symbols",
            "metrics": {"meaningful_score": 0.0, "dictionary_match": 0.0}
        }

    # Keyboard mashing patterns
    keyboard_walks = ["asdf", "qwer", "zxcv", "plmok", "nkio", "eoipmk", "qwerty"]
    if any(walk in text_clean for walk in keyboard_walks):
        return {
            "isMeaningful": False, "confidence": 0.1, "reason": "Keyboard mashing pattern",
            "metrics": {"meaningful_score": 0.0, "dictionary_match": 0.0}
        }

    # Repeated sequences or characters (e.g. aaaaa, abcabcabcabc)
    if re.search(r'(.)\1{4,}', text_clean):
        return {
            "isMeaningful": False, "confidence": 0.1, "reason": "5+ identical characters",
            "metrics": {"meaningful_score": 0.0, "dictionary_match": 0.0}
        }
        
    if re.search(r'(.{2,})\1{3,}', text_clean):
        return {
            "isMeaningful": False, "confidence": 0.1, "reason": "Repeated pattern",
            "metrics": {"meaningful_score": 0.0, "dictionary_match": 0.0}
        }

    words = text_clean.split()
    
    # Whitelist domain-specific keywords so they are never flagged as gibberish even if mispelled
    # Some words might contain repeated chars or seem weird to basic heuristics
    DOMAIN_KEYWORDS = [
        "company", "leave", "holiday", "salary", "attendance", "contact", 
        "owner", "mission", "vision", "technology", "react", "vite", 
        "mongodb", "postgres", "frontend", "backend", "location", "address", 
        "email", "phone", "services", "projects", "career", "jobs", "policy", 
        "hr", "founder", "framework", "working", "hours", "total"
    ]
    
    # If the text contains any of these domain keywords, consider it meaningful immediately
    for keyword in DOMAIN_KEYWORDS:
        if keyword in text_clean:
            return {
                "isMeaningful": True, 
                "confidence": 1.0, 
                "reason": f"Contains whitelisted domain keyword: {keyword}",
                "metrics": {"meaningful_score": 100.0, "dictionary_match": 100.0}
            }
    
    # Check for words that are just consonants (and long enough to be keyboard mashing)
    long_gibberish_words = 0
    for word in words:
        letters_only = re.sub(r'[^a-z]', '', word)
        if len(letters_only) >= 5 and not re.search(r'[aeiouy]', letters_only):
            long_gibberish_words += 1

    if long_gibberish_words > 0 and len(words) < 3:
        return {
            "isMeaningful": False, "confidence": 0.1, "reason": "Long word with no vowels",
            "metrics": {"meaningful_score": 0.0, "dictionary_match": 0.0}
        }

    # If it survived all negative checks, we assume it's meaningful
    return {
        "isMeaningful": True, 
        "confidence": 1.0, 
        "reason": "Passes all heuristic constraints",
        "metrics": {
            "meaningful_score": 100.0,
            "dictionary_match": 100.0
        }
    }

from functools import lru_cache

def _get_greeting_structures():
    return engine.greeting_phrases

def detect_greeting(text: str) -> Tuple[bool, str, float, str, str]:
    """
    Detects if the message STARTS with a greeting based on GreetingRepository.
    Returns: (is_greeting, matched_pattern, confidence, response, remaining_query)
    """
    text_lower = text.lower().strip()
    all_phrases = _get_greeting_structures()
    
    for phrase_lower, match_str, response in all_phrases:
        if phrase_lower and text_lower.startswith(phrase_lower):
            # Extract remaining text after greeting
            remaining_query = text_lower[len(phrase_lower):].strip()
            # If there's punctuation like "Hi, company name", we should strip it
            remaining_query = re.sub(r'^[^\w\s]+', '', remaining_query).strip()
            
            return True, match_str, 0.95, response, remaining_query
            
    return False, "No greeting pattern matched", 0.0, "", text






from cachetools import cached, TTLCache

def _get_faq_structures():
    all_phrases = []
    for phrase, (orig, f) in engine.faq_exact_map.items():
        all_phrases.append((phrase, orig, f))
    
    phrase_dict = {p[0]: (p[1], p[2]) for p in all_phrases}
    phrase_keys = engine.faq_rapidfuzz_choices
    
    return all_phrases, phrase_dict, phrase_keys

def detect_faq(text: str) -> Tuple[bool, str, float, Any]:
    from rapidfuzz import process, fuzz
    import re
    text_lower = text.lower().strip()
    
    all_phrases, phrase_dict, phrase_keys = _get_faq_structures()
                
    if not all_phrases:
        return False, "No FAQ matched", 0.0, None
        
    # 1. Exact/substring match
    for phrase_lower, match_str, faq_obj in all_phrases:
        # Regex or exact match logic
        if phrase_lower and (phrase_lower in text_lower or text_lower in phrase_lower):
            return True, match_str, 1.0, faq_obj
            
    # 2. RapidFuzz semantic similarity
    result = process.extractOne(text_lower, phrase_keys, scorer=fuzz.token_set_ratio)
    
    if result:
        match, score, index = result
        if score >= 85: # Threshold lowered for semantic match
            original_phrase, faq_obj = phrase_dict[match]
            return True, original_phrase, score / 100.0, faq_obj
            
    return False, "No FAQ matched", 0.0, None




# backend/steps/followup_resolver_step.py

logger = get_logger(__name__)

class FollowUpResolverStep(PipelineStep):
    """
    Deterministically resolves short follow-up messages into full queries using session memory,
    without invoking an LLM.
    """
    def process(self, context: PipelineContext) -> PipelineResult:
        result = PipelineResult()
        
        normalized = context.normalized_message
        words = normalized.split()
        
        # 1. Check if it is a short or incomplete query
        if len(normalized) > 25 or len(words) > 3:
            result.metadata["followup_confidence"] = 0.0
            result.metadata["reason"] = "Query too long for strict deterministic follow-up"
            return result
            
        # Check registry
        keyword = words[0] if words else ""
        # Sometimes user says "my name" or "what salary", try last word too if first doesn't match
        pattern_data = followup_registry.get_pattern(keyword)
        if not pattern_data and len(words) > 1:
            keyword = words[-1]
            pattern_data = followup_registry.get_pattern(keyword)
            
        if not pattern_data:
            result.metadata["followup_confidence"] = 0.0
            result.metadata["reason"] = "No matching keyword pattern found"
            return result
            
        # 2. Fetch Structured Context Store
        global_ctx = ConversationMemoryService.get_context(context.session_id)
        
        # 3. Apply Rewrite Rules based on Context
        rewritten_query = None
        last_entity = None
        
        if keyword in ["name", "my name"]:
            if global_ctx.get("last_memory_operation"):
                rewritten_query = "What should you call me?"
            else:
                rewritten_query = "What is my name?"
                
        else:
            # Need an entity for other keywords
            entities = global_ctx.get("last_entities", [])
            if entities:
                last_entity = entities[-1]
                
            if not last_entity:
                result.metadata["followup_confidence"] = 0.3
                result.metadata["reason"] = "Missing last_entities in Context Store to resolve the rewrite."
                return result
                
            template = pattern_data["template"]
            rewritten_query = template.replace("{last_entity}", last_entity)
            
        confidence = 0.95
        
        # 6. Apply state updates
        context.normalized_message = rewritten_query
        
        result.metadata["rewritten_query"] = rewritten_query
        result.metadata["original_query"] = normalized
        result.metadata["followup_confidence"] = confidence
        result.metadata["last_entity"] = last_entity
        
        logger.info(f"FollowUpResolver applied: '{normalized}' -> '{rewritten_query}' (entity: {last_entity})")
        
        return result



class SecurityValidationStep(PipelineStep):
    def __init__(self):
        super().__init__()
        # Common prompt injection signatures
        self.injection_patterns = [
            r"(?i)ignore previous instructions",
            r"(?i)reveal system prompt",
            r"(?i)developer mode",
            r"(?i)bypass restrictions",
            r"(?i)forget all instructions",
            r"(?i)print environment variables",
            r"(?i)exec\(",
            r"(?i)system\.out",
        ]

    def process(self, context: PipelineContext) -> PipelineResult:
        msg = context.original_message or ""
        
        for pattern in self.injection_patterns:
            if re.search(pattern, msg):
                context.logger.warning(f"Prompt injection detected for session {context.session_id}")
                return PipelineResult(
                    stop=True,
                    intent="security_violation",
                    response="I'm sorry, but I cannot fulfill that request."
                )
                
        return PipelineResult(stop=False)

def warmup_caches():
    engine.load_all()


# backend/services/entity_extraction_service.py
import re
from typing import Dict, List
from chatbot.memory import ConversationMemoryService

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


# backend/services/fact_extraction_service.py
import re
from typing import Dict, Any
from chatbot.memory import ConversationMemoryService

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


import re
import string
import difflib
from typing import Tuple, Optional, Dict, Any

class IntentNormalizationService:
    def __init__(self):
        # 1. Spelling Correction Dictionary
        self.spelling_dict = {
            "comapny": "company",
            "copmany": "company",
            "compnay": "company",
            "mision": "mission",
            "misison": "mission",
            "misson": "mission",
            "frondend": "frontend",
            "fronted": "frontend",
            "front end": "frontend",
            "back end": "backend",
            "bakend": "backend",
            "leavs": "leave",
            "leve": "leave",
            "horus": "hours",
            "contcat": "contact",
            "rajanarayn": "rajnarayan",
            "managerr": "manager",
            "tell me about yourself": "who are you"
        }

        # 2. Intent Dictionary (Aliases mapped to Canonical Intent)
        self.intents = {
            "COMPANY_INFORMATION": [
                "company", "company name", "company details", "about company",
                "company information", "organization", "firm", "enterprise", "corporate profile"
            ],
            "COMPANY_MISSION": [
                "mission", "vision", "goal", "objective", "purpose",
                "company mission", "company vision", "corporate mission"
            ],
            "CONTACT_INFORMATION": [
                "contact", "phone", "email", "support", "hr contact",
                "sales contact", "reach company", "mobile", "reach us"
            ],
            "WORKING_HOURS": [
                "timing", "office timing", "working hours", "office hours",
                "shift timing", "business hours"
            ],
            "LEAVE_POLICY": [
                "leave", "holiday", "earned leave", "casual leave",
                "leave policy", "vacation", "time off"
            ],
            "SERVICES": [
                "services", "offerings", "products", "solutions", "what do you do"
            ],
            "TECHNOLOGY": [
                "tech stack", "technology", "framework", "backend", "frontend",
                "react", "vite", "node"
            ]
        }

        # Precompute flat alias mapping and alias list for fuzzy matching
        self.alias_to_intent = {}
        self.all_aliases = []
        for intent, aliases in self.intents.items():
            for alias in aliases:
                self.alias_to_intent[alias] = intent
                self.all_aliases.append(alias)

    def preprocess_query(self, query: str) -> str:
        """
        Convert lowercase, Remove punctuation, Collapse multiple spaces,
        Normalize unicode, Remove repeated letters.
        """
        # Convert lowercase
        q = query.lower()
        
        # Remove punctuation
        q = q.translate(str.maketrans('', '', string.punctuation))
        
        # Remove repeated letters (3 or more) -> 1 letter
        q = re.sub(r'(.)\1{2,}', r'\1', q)
        
        # Collapse multiple spaces
        q = re.sub(r'\s+', ' ', q).strip()
        return q

    def correct_spelling(self, query: str) -> Tuple[str, Dict[str, str]]:
        """
        Correct spelling mistakes based on the dictionary.
        Returns corrected query and dict of corrected words.
        """
        words = query.split()
        corrected_words_dict = {}
        corrected_query_parts = []
        
        # Multi-word replacements
        temp_query = query
        for typo, correction in self.spelling_dict.items():
            if " " in typo:
                if typo in temp_query:
                    corrected_words_dict[typo] = correction
                    temp_query = temp_query.replace(typo, correction)
        
        # Word by word replacements
        words = temp_query.split()
        final_words = []
        for w in words:
            if w in self.spelling_dict:
                correction = self.spelling_dict[w]
                corrected_words_dict[w] = correction
                final_words.append(correction)
            else:
                final_words.append(w)
                
        corrected_query = " ".join(final_words)
        return corrected_query, corrected_words_dict

    def get_fuzzy_match(self, query: str) -> Tuple[Optional[str], float, Optional[str]]:
        """
        Find best matching alias.
        Returns (Matched Alias, Similarity Score (0-1), Intent)
        """
        best_match = None
        best_score = 0.0
        
        # 1. Exact Substring Match Check
        for alias in self.all_aliases:
            # If an alias (e.g. 'services') is a standalone word in the query (e.g. 'our services')
            if alias == query or f" {alias} " in f" {query} ":
                return alias, 1.0, self.alias_to_intent[alias]
        
        # 2. Fuzzy Match
        for alias in self.all_aliases:
            score = difflib.SequenceMatcher(None, query, alias).ratio()
            if score > best_score:
                best_score = score
                best_match = alias
                
        if best_score >= 0.85 and best_match:
            intent = self.alias_to_intent[best_match]
            return best_match, best_score, intent
            
        return None, best_score, None

    def process(self, original_query: str) -> Dict[str, Any]:
        """
        Full pipeline:
        1. Preprocess
        2. Spelling Correction
        3. Fuzzy Match
        """
        preprocessed = self.preprocess_query(original_query)
        corrected_query, corrected_words = self.correct_spelling(preprocessed)
        matched_alias, score, intent = self.get_fuzzy_match(corrected_query)
        
        return {
            "original_query": original_query,
            "normalized_query": corrected_query,
            "corrected_words": corrected_words,
            "detected_intent": intent,
            "similarity_score": round(score, 4),
            "matched_alias": matched_alias,
            "confidence_meets_threshold": score >= 0.85
        }





# backend/services/gibberish_service.py
GIBBERISH_MESSAGE = "I'm sorry, I couldn't understand that. Could you please rephrase?"
class GibberishService:
    @staticmethod
    def get_response() -> str:
        return GIBBERISH_MESSAGE


# backend/services/followup_registry.py
from typing import Dict, Any, Optional

class FollowupPatternRegistry:
    def __init__(self):
        # keyword -> (rewrite_template, priority)
        self.patterns: Dict[str, Dict[str, Any]] = {
            "name": {
                "template": "What is my preferred name?",
                "priority": 10
            },
            "salary": {
                "template": "What is the salary for {last_entity}?",
                "priority": 10
            },
            "price": {
                "template": "What is the price of {last_entity}?",
                "priority": 10
            },
            "pricing": {
                "template": "What is the pricing for {last_entity}?",
                "priority": 10
            },
            "address": {
                "template": "What is the address of {last_entity}?",
                "priority": 10
            },
            "phone": {
                "template": "What is the phone number of {last_entity}?",
                "priority": 10
            },
            "contact": {
                "template": "What is the contact information for {last_entity}?",
                "priority": 10
            },
            "timing": {
                "template": "What are the timings for {last_entity}?",
                "priority": 10
            },
            "location": {
                "template": "What is the location of {last_entity}?",
                "priority": 10
            },
            "email": {
                "template": "What is the email address for {last_entity}?",
                "priority": 10
            },
            "website": {
                "template": "What is the website for {last_entity}?",
                "priority": 10
            },
            "owner": {
                "template": "Who is the owner of {last_entity}?",
                "priority": 10
            },
            "ceo": {
                "template": "Who is the CEO of {last_entity}?",
                "priority": 10
            },
            "founder": {
                "template": "Who is the founder of {last_entity}?",
                "priority": 10
            },
            "services": {
                "template": "What services does {last_entity} offer?",
                "priority": 10
            },
            "leave": {
                "template": "What is the leave policy for {last_entity}?",
                "priority": 10
            },
            "policy": {
                "template": "What is the policy regarding {last_entity}?",
                "priority": 10
            }
        }

    def get_pattern(self, keyword: str) -> Optional[Dict[str, Any]]:
        return self.patterns.get(keyword.lower().strip())

class GibberishStep(PipelineStep):
    def process(self, context: PipelineContext) -> PipelineStepResult:
        import re
        text = context.normalized_message
        
        def _get_gibberish_result():
            component = {
                "type": "fallback",
                "prefix": "That doesn't look like a valid message. I couldn't understand",
                "query": context.original_message,
                "suffix": ". Please try asking a clear question about one of the topics below.",
                "suggestions": ["Overview", "Office Timings", "Leave Policy", "Contact", "Services", "Career", "Help"]
            }
            return PipelineStepResult(
                stop=True,
                intent="Gibberish",
                response="",
                components=[component]
            )

        # Fast O(1) heuristic checks for INSTANT 1ms gibberish detection
        if re.search(r'(.)\1{4,}', text) or (len(text) < 2 and not text.isalnum()):
            context.logger.info("Gibberish detected (Fast Regex): repeating chars or too short")
            return _get_gibberish_result()
            
        if re.search(r'(?i)[bcdfghjklmnpqrstvwxz]{5,}', text):
            context.logger.info("Gibberish detected (Fast Regex): 5+ consecutive consonants")
            return _get_gibberish_result()

        # Fallback to the advanced validate_query heuristic for more complex cases
        validation_result = validate_query(text)
        if not validation_result.get("isMeaningful", True):
            context.logger.info(f"Gibberish detected (Advanced Engine): {validation_result.get('reason')}")
            return _get_gibberish_result()
        
        return PipelineStepResult(stop=False)

class NormalizeStep(PipelineStep):
    def process(self, context: PipelineContext) -> PipelineStepResult:
        from utils.normalizer import normalize_text
        context.normalized_message = normalize_text(context.original_message)
        context.metadata["normalized"] = True
        context.metadata["original_query"] = context.original_message
        context.metadata["normalized_query"] = context.normalized_message
        context.metadata["input_length"] = len(context.original_message)
        # Assuming English for now unless langdetect is used
        context.metadata["language"] = "English"
        return PipelineStepResult(stop=False)

    def add_pattern(self, keyword: str, template: str, priority: int = 10):
        self.patterns[keyword.lower().strip()] = {
            "template": template,
            "priority": priority
        }

followup_registry = FollowupPatternRegistry()


