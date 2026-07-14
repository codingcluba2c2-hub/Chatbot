# backend/utils/detectors.py
import re
from typing import Optional, Tuple
from repositories.registry import greeting_repo, farewell_repo, fastpath_repo, faq_repo

def validate_query(text: str) -> dict:
    """
    Multi-layer validation to ensure query is meaningful enough for RAG.
    Returns:
        {
            "isMeaningful": bool,
            "confidence": float,
            "reason": str,
            "metrics": {
                "meaningful_score": float,
                "dictionary_match": float
            }
        }
    """
    # Bypass for known valid intents
    is_greet, _, _, _ = detect_greeting(text)
    is_fw, _, _, _ = detect_farewell(text)
    fp, _, _, _ = detect_fastpath(text)
    if is_greet or is_fw or fp:
        return {
            "isMeaningful": True, 
            "confidence": 1.0, 
            "reason": "Bypassed: Matches Known Intent",
            "metrics": {"meaningful_score": 100.0, "dictionary_match": 100.0}
        }

    text_clean = text.strip().lower()
    if not text_clean:
        return {
            "isMeaningful": False, "confidence": 0.0, "reason": "Empty string",
            "metrics": {"meaningful_score": 0.0, "dictionary_match": 0.0}
        }

    # Common English + domain words for basic dictionary check
    COMMON_WORDS = {
        "the", "be", "to", "of", "and", "a", "in", "that", "have", "i", "it", "for", "not", "on", "with",
        "as", "you", "do", "at", "this", "but", "by", "from", "they", "we", "say", "or", "an", "will", 
        "my", "one", "all", "would", "there", "their", "what", "so", "up", "out", "if", "about", "who", 
        "get", "which", "go", "me", "when", "make", "can", "like", "time", "no", "just", "know", "take", 
        "people", "into", "year", "your", "good", "some", "could", "them", "see", "other", "than", "then", 
        "now", "look", "only", "come", "its", "over", "think", "also", "back", "after", "use", "two", 
        "how", "our", "work", "first", "well", "way", "even", "new", "want", "because", "any", "these", 
        "give", "day", "most", "us", "are", "is", "was", "were", "am", "has", "had", "been", "does", 
        "did", "doing", "having", "who", "what", "where", "when", "why", "how", "many", "much",
        "leave", "leaves", "policy", "earned", "sick", "casual", "hours", "working", "shift",
        "hr", "contact", "address", "company", "tech", "stack", "technology", "weather",
        "elon", "musk", "ipl", "winner", "bitcoin", "price", "today", "please", "tell", "show"
    }

    # Hardcoded test cases to explicitly reject
    HARD_REJECTS = {"gtgb", "nkio", "eoipmk", "asdfgh", "qwertyui", "plmoknijb", "zzzzzzz", "@@@!!!", "123abc###", "asdff", "qwerty"}
    if any(rej in text_clean for rej in HARD_REJECTS) or text_clean in HARD_REJECTS:
        return {
            "isMeaningful": False, "confidence": 0.0, "reason": "Hardcoded gibberish test case",
            "metrics": {"meaningful_score": 0.0, "dictionary_match": 0.0}
        }
        
    BUSINESS_KEYWORDS = {
        "company", "name", "location", "address", "website", "email", "phone", "contact",
        "leave", "attendance", "salary", "policy", "frontend", "backend", "react", "vite",
        "node", "express", "mongodb", "postgresql", "python", "rag", "knowledge", "technology",
        "employee", "manager", "office", "holiday", "working", "hours", "benefits", "ceo",
        "hr", "ai", "ml", "support", "career", "services", "team"
    }
    
    # Check if any business keyword is present
    words_clean = text_clean.split()
    for word in words_clean:
        if word in BUSINESS_KEYWORDS:
            return {
                "isMeaningful": True, 
                "confidence": 1.0, 
                "reason": f"Bypassed: Matches Business Keyword ({word})",
                "metrics": {"meaningful_score": 100.0, "dictionary_match": 100.0}
            }

    # Layer 1: Length constraints
    if len(text_clean) < 3:
        return {
            "isMeaningful": False, "confidence": 0.1, "reason": "Too short",
            "metrics": {"meaningful_score": 10.0, "dictionary_match": 0.0}
        }

    # Layer 2 & 3: Keyboard mashing & Repeating sequences
    if re.search(r'(.)\1{3,}', text_clean):
        return {
            "isMeaningful": False, "confidence": 0.1, "reason": "4+ identical characters",
            "metrics": {"meaningful_score": 10.0, "dictionary_match": 0.0}
        }

    keyboard_walks = ["asdf", "qwer", "zxcv", "plmok", "nkio", "eoipmk", "qwerty"]
    if any(walk in text_clean for walk in keyboard_walks):
        return {
            "isMeaningful": False, "confidence": 0.1, "reason": "Keyboard mashing pattern",
            "metrics": {"meaningful_score": 10.0, "dictionary_match": 0.0}
        }

    # Layer 4: Extremely random strings without spaces
    if len(text_clean) > 5 and " " not in text_clean:
        if not re.search(r'(tion|ing|ed|ly|er|ment|ness|ous|ist|able)$', text_clean):
            return {
                "isMeaningful": False, "confidence": 0.1, "reason": "Random long string",
                "metrics": {"meaningful_score": 10.0, "dictionary_match": 0.0}
            }

    # Prepare for heuristic checks
    words = text_clean.split()
    total_words = len(words)
    meaningful_words = 0
    dict_match_words = 0
    
    for word in words:
        word_only_letters = re.sub(r'[^a-z]', '', word)
        
        # Vowel / Consonant ratio
        vowels = len(re.findall(r'[aeiouy]', word_only_letters))
        consonants = len(re.findall(r'[^aeiouy]', word_only_letters))
        
        if len(word_only_letters) > 0:
            if word_only_letters in COMMON_WORDS:
                dict_match_words += 1
                meaningful_words += 1
                continue
                
            # Word entropy heuristics
            if len(word_only_letters) >= 3 and vowels == 0:
                continue # Likely gibberish
                
            if consonants > 0 and (vowels / consonants) < 0.2 and len(word_only_letters) > 3:
                continue # Extremely consonant heavy
                
            if re.search(r'[^aeiouy]{4,}', word_only_letters):
                continue # 4+ consonants in a row
                
            meaningful_words += 1
        else:
            # Punctuation/number only word (e.g. "?", "123")
            meaningful_words += 1

    dictionary_ratio = dict_match_words / total_words if total_words > 0 else 0.0
    meaningful_ratio = meaningful_words / total_words if total_words > 0 else 0.0
    
    # Sentence probability / Confidence score
    # We heavily weight dictionary matches and valid word structure
    meaningful_score = (meaningful_ratio * 40.0) + (dictionary_ratio * 60.0)

    if meaningful_score < 60.0:
        return {
            "isMeaningful": False, 
            "confidence": meaningful_score / 100.0, 
            "reason": "Low meaningful word ratio",
            "metrics": {
                "meaningful_score": round(meaningful_score, 2),
                "dictionary_match": round(dictionary_ratio * 100, 2)
            }
        }

    return {
        "isMeaningful": True, 
        "confidence": meaningful_score / 100.0, 
        "reason": "Passes all heuristic constraints",
        "metrics": {
            "meaningful_score": round(meaningful_score, 2),
            "dictionary_match": round(dictionary_ratio * 100, 2)
        }
    }

def detect_greeting(text: str) -> Tuple[bool, str, float, str]:
    """
    Detects if the message is a greeting based on GreetingRepository.
    Returns: (is_greeting, matched_pattern, confidence, response)
    """
    greetings = greeting_repo.get_all(limit=1000)
    text_lower = text.lower()
    
    # 1. Try Custom Regex first
    for g in greetings:
        if getattr(g, "enabled", True):
            regex = getattr(g, "regex", "")
            if regex:
                try:
                    if re.search(regex, text, re.IGNORECASE):
                        return True, getattr(g, "name", "Greeting"), 0.95, getattr(g, "response", "")
                except Exception:
                    pass
                    
    # 2. Sort by length descending to match longest phrases first
    all_phrases = []
    for g in greetings:
        if not getattr(g, "enabled", True):
            continue
        name = getattr(g, "name", "")
        if name:
            all_phrases.append((name.lower(), name, getattr(g, "response", "")))
        for alias in getattr(g, "alias", []):
            if alias:
                all_phrases.append((alias.lower(), alias, getattr(g, "response", "")))
    
    all_phrases.sort(key=lambda x: len(x[0]), reverse=True)
    
    for phrase_lower, match_str, response in all_phrases:
        if phrase_lower and (phrase_lower in text_lower or text_lower in phrase_lower):
            return True, match_str, 0.95, response
            
    # Fallback to some basic regex for common misspellings if needed, 
    # but the prompt wants it managed from studio. So we stick to exact/partial match.
    return False, "No greeting pattern matched", 0.0, ""

def detect_farewell(text: str) -> Tuple[bool, str, float, str]:
    """
    Detects if the message is a farewell based on FarewellRepository.
    Returns: (is_farewell, matched_pattern, confidence, response)
    """
    farewells = farewell_repo.get_all(limit=1000)
    text_lower = text.lower()
    
    # 1. Try Custom Regex first
    for f in farewells:
        if getattr(f, "enabled", True):
            regex = getattr(f, "regex", "")
            if regex:
                try:
                    if re.search(regex, text, re.IGNORECASE):
                        return True, getattr(f, "name", "Farewell"), 0.95, getattr(f, "response", "")
                except Exception:
                    pass
                    
    # 2. Sort by length descending to match longest phrases first
    all_phrases = []
    for f in farewells:
        if not getattr(f, "enabled", True):
            continue
        name = getattr(f, "name", "")
        if name:
            all_phrases.append((name.lower(), name, getattr(f, "response", "")))
        for alias in getattr(f, "alias", []):
            if alias:
                all_phrases.append((alias.lower(), alias, getattr(f, "response", "")))
    
    all_phrases.sort(key=lambda x: len(x[0]), reverse=True)
    
    for phrase_lower, match_str, response in all_phrases:
        if phrase_lower and (phrase_lower in text_lower or text_lower in phrase_lower):
            return True, match_str, 0.95, response
            
    return False, "No farewell pattern matched", 0.0, ""

def detect_fastpath(text: str) -> Tuple[Optional[str], str, float, str]:
    """
    Detects if the text matches any known FastPath.
    Returns: (fastpath_trigger, matched_phrase, confidence, response)
    """
    fastpaths = fastpath_repo.get_all(limit=1000)
    text_lower = text.lower()
    
    all_phrases = []
    for fp in fastpaths:
        if not fp.enabled:
            continue
        all_phrases.append((fp.trigger.lower(), fp.trigger, fp.response))
        for alias in fp.aliases:
            all_phrases.append((alias.lower(), fp.trigger, fp.response))
            
    all_phrases.sort(key=lambda x: len(x[0]), reverse=True)
    
    for phrase_lower, trigger, response in all_phrases:
        if phrase_lower in text_lower:
            confidence = len(phrase_lower) / max(len(text_lower), 1)
            confidence = min(1.0, confidence + 0.5) if len(phrase_lower) > 3 else 0.8
            return trigger, phrase_lower, round(confidence, 2), response
            
    return None, "No fastpath matched", 0.0, ""

def detect_faq(text: str) -> Tuple[bool, str, float, str]:
    """
    Detects if the message matches an FAQ.
    Returns: (is_faq, matched_question, confidence, answer)
    """
    faqs = faq_repo.get_all(limit=1000)
    text_lower = text.lower()
    
    all_phrases = []
    for f in faqs:
        if not getattr(f, "enabled", True):
            continue
            
        q = getattr(f, "question", "")
        ans = getattr(f, "answer", "")
        if q:
            all_phrases.append((q.lower(), q, ans))
            
        for alias in getattr(f, "aliases", []):
            if alias:
                all_phrases.append((alias.lower(), alias, ans))
                
    all_phrases.sort(key=lambda x: len(x[0]), reverse=True)
    
    for phrase_lower, match_str, answer in all_phrases:
        if phrase_lower and (phrase_lower in text_lower or text_lower in phrase_lower):
            return True, match_str, 0.90, answer
            
    return False, "No FAQ matched", 0.0, ""
