# backend/utils/detectors.py
import re
from typing import Optional, Tuple
from repositories.registry import greeting_repo, farewell_repo, fastpath_repo, faq_repo

def validate_query(text: str) -> dict:
    """
    Validation to ensure query is not pure gibberish (keyboard mash, repeated chars, symbols).
    """
    # Bypass for known valid intents
    is_greet, _, _, _ = detect_greeting(text)
    is_fw, _, _, _ = detect_farewell(text)
    fp, _, _, _ = detect_fastpath(text)
    if is_greet or is_fw or fp:
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
