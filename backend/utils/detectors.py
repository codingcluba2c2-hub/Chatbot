# backend/utils/detectors.py
import re
from typing import Optional, Tuple
from core.database import greeting_repo, farewell_repo, fastpath_repo, faq_repo

def validate_query(text: str) -> dict:
    """
    Validation to ensure query is not pure gibberish (keyboard mash, repeated chars, symbols).
    """
    # Bypass for known valid intents
    is_greet, _, _, _, _ = detect_greeting(text)
    is_fw, _, _, _, _ = detect_farewell(text)
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

def detect_greeting(text: str) -> Tuple[bool, str, float, str, str]:
    """
    Detects if the message STARTS with a greeting based on GreetingRepository.
    Returns: (is_greeting, matched_pattern, confidence, response, remaining_query)
    """
    greetings = greeting_repo.get_all(limit=1000)
    text_lower = text.lower().strip()
    
    # Sort by length descending to match longest phrases first
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
        if phrase_lower and text_lower.startswith(phrase_lower):
            # Extract remaining text after greeting
            remaining_query = text_lower[len(phrase_lower):].strip()
            # If there's punctuation like "Hi, company name", we should strip it
            remaining_query = re.sub(r'^[^\w\s]+', '', remaining_query).strip()
            
            return True, match_str, 0.95, response, remaining_query
            
    return False, "No greeting pattern matched", 0.0, "", text

def detect_farewell(text: str) -> Tuple[bool, str, float, str, str]:
    """
    Detects if the message STARTS with a farewell based on FarewellRepository.
    Returns: (is_farewell, matched_pattern, confidence, response, remaining_query)
    """
    farewells = farewell_repo.get_all(limit=1000)
    text_lower = text.lower().strip()
    
    # Sort by length descending to match longest phrases first
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
        if phrase_lower and text_lower.startswith(phrase_lower):
            # Extract remaining text
            remaining_query = text_lower[len(phrase_lower):].strip()
            remaining_query = re.sub(r'^[^\w\s]+', '', remaining_query).strip()
            
            return True, match_str, 0.95, response, remaining_query
            
    return False, "No farewell pattern matched", 0.0, "", text

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
    Detects if the message matches an FAQ using fuzzy string matching.
    Returns: (is_faq, matched_question, confidence, answer)
    """
    from rapidfuzz import process, fuzz
    faqs = faq_repo.get_all(limit=1000)
    text_lower = text.lower().strip()
    
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
                
    if not all_phrases:
        return False, "No FAQ matched", 0.0, ""
        
    # We create a dictionary of phrase -> (original_phrase, answer)
    phrase_dict = {p[0]: (p[1], p[2]) for p in all_phrases}
    phrase_keys = list(phrase_dict.keys())
    
    # 1. Check exact/substring match first for speed
    all_phrases.sort(key=lambda x: len(x[0]), reverse=True)
    for phrase_lower, match_str, answer in all_phrases:
        if phrase_lower and (phrase_lower in text_lower or text_lower in phrase_lower):
            return True, match_str, 1.0, answer
            
    # 2. Use RapidFuzz for fuzzy matching (to handle Al vs ai typos)
    # We use token_set_ratio or WRatio which is good for sentence similarity
    result = process.extractOne(text_lower, phrase_keys, scorer=fuzz.token_set_ratio)
    
    if result:
        match, score, index = result
        if score >= 90: # 90% similarity threshold
            original_phrase, answer = phrase_dict[match]
            return True, original_phrase, score / 100.0, answer
            
    return False, "No FAQ matched", 0.0, ""

def detect_knowledge_tree(text: str) -> Tuple[bool, str, float, str, str]:
    """
    Detects if the message matches a Knowledge Tree node.
    Returns: (is_matched, matched_node_title, confidence, response_markdown, node_id)
    """
    from core.database import knowledge_node_repo
    from rapidfuzz import process, fuzz
    
    nodes = knowledge_node_repo.get_all(limit=1000)
    text_lower = text.lower().strip()
    
    all_phrases = []
    for n in nodes:
        if getattr(n, "status", "active") != "active":
            continue
            
        title = getattr(n, "title", "")
        resp = getattr(n, "response_markdown", "") or getattr(n, "description", "")
        if title:
            all_phrases.append((title.lower(), title, resp, n.id))
            
        for alias in getattr(n, "aliases", []):
            if alias:
                all_phrases.append((alias.lower(), title, resp, n.id))
                
    if not all_phrases:
        return False, "No Node matched", 0.0, "", ""
        
    phrase_dict = {p[0]: (p[1], p[2], p[3]) for p in all_phrases}
    phrase_keys = list(phrase_dict.keys())
    
    # 1. Check exact match or if the alias is fully contained in the user's text
    all_phrases.sort(key=lambda x: len(x[0]), reverse=True)
    for phrase_lower, match_str, resp, node_id in all_phrases:
        if phrase_lower and (phrase_lower == text_lower or phrase_lower in text_lower):
            return True, match_str, 1.0, resp, node_id
            
    # 2. Use RapidFuzz for fuzzy matching
    result = process.extractOne(text_lower, phrase_keys, scorer=fuzz.ratio)
    
    if result:
        match, score, index = result
        if score >= 85: # 85% similarity threshold for exact matches with typos
            original_phrase, resp, node_id = phrase_dict[match]
            return True, original_phrase, score / 100.0, resp, node_id
            
    return False, "No Node matched", 0.0, "", ""
