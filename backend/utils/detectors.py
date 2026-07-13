# backend/utils/detectors.py
import re
from typing import Optional, Tuple
from repositories.registry import greeting_repo, farewell_repo, fastpath_repo, faq_repo

def is_gibberish(text: str) -> Tuple[bool, str, float]:
    """
    Detects simple gibberish like random characters, keyboard spam, etc.
    Returns: (is_gibberish, matched_rule, confidence)
    """
    # Bypass gibberish detection if the text matches a known valid intent
    is_greet, _, _, _ = detect_greeting(text)
    if is_greet:
        return False, "Bypassed: Matches Greeting", 0.0
        
    is_fw, _, _, _ = detect_farewell(text)
    if is_fw:
        return False, "Bypassed: Matches Farewell", 0.0
        
    fp, _, _ = detect_fastpath(text)
    if fp:
        return False, "Bypassed: Matches FastPath", 0.0

    if "asdf" in text or "qwer" in text or "zxcv" in text:
        return True, "Keyboard mashing pattern", 1.0
        
    if re.search(r'(.)\1{2,}', text):
        return True, "3+ identical characters", 0.9
        
    if re.search(r'(.{2,})\1{2,}', text):
        return True, "Repeating multi-char sequence", 0.9
        
    if re.match(r'^[^aeiouy0-9]{1,2}$', text) and text not in ["gm", "gd", "gn"]:
        return True, "1-2 consonants only", 0.8
        
    for word in text.split():
        if len(word) >= 3 and not re.search(r'[aeiouy]', word):
            return True, f"Word without vowels: {word}", 0.85
            
        if len(word) > 5 and re.search(r'[a-z]+[0-9]+', word):
            return True, f"Alphanumeric mix: {word}", 0.75
            
    if re.search(r'[^aeiouy0-9\W\s]{4,}', text):
        return True, "4+ consonants in a row", 0.8
        
    if len(text.split()) == 1 and len(text) > 7:
        consonants = len(re.findall(r'[^aeiouy0-9\W\s]', text))
        if consonants / len(text) > 0.7:
            return True, "High consonant ratio (>70%)", 0.9
            
    return False, "No gibberish pattern matched", 0.0

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

def detect_fastpath(text: str) -> Tuple[Optional[str], str, float]:
    """
    Detects if the text matches any known FastPath.
    Returns: (fastpath_trigger, matched_phrase, confidence)
    """
    fastpaths = fastpath_repo.get_all(limit=1000)
    text_lower = text.lower()
    
    all_phrases = []
    for fp in fastpaths:
        if not fp.enabled:
            continue
        all_phrases.append((fp.trigger.lower(), fp.trigger))
        for alias in fp.aliases:
            all_phrases.append((alias.lower(), fp.trigger))
            
    all_phrases.sort(key=lambda x: len(x[0]), reverse=True)
    
    for phrase_lower, trigger in all_phrases:
        if phrase_lower in text_lower:
            confidence = len(phrase_lower) / max(len(text_lower), 1)
            confidence = min(1.0, confidence + 0.5) if len(phrase_lower) > 3 else 0.8
            return trigger, phrase_lower, round(confidence, 2)
            
    return None, "No fastpath matched", 0.0

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
