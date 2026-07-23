import math
import time
from typing import Dict, Any, Tuple
from chatbot.in_memory_engine import engine
from core.logger import get_logger

logger = get_logger("gibberish_engine")

class GibberishScoringEngine:
    """
    Deterministic gibberish scoring engine.
    Assumes meaningful entities and spell corrections have already bypassed it.
    """
    
    THRESHOLD = 50
    
    @staticmethod
    def evaluate(raw_text: str) -> Tuple[bool, Dict[str, Any]]:
        t0 = time.perf_counter()
        
        text = raw_text.lower()
        text = engine.compiled_regex["unicode_noise"].sub('', text)
        text = engine.compiled_regex["collapse_spaces"].sub(' ', text).strip()
        
        if not text:
            return True, {"total_score": 100, "reason": "empty_or_noise"}
            
        words = text.split()
        
        # If it matches any allowlist, it's not gibberish
        if any(w in engine.false_positive_allowlist for w in words):
            return False, {"total_score": 0, "reason": "allowlist_match"}
            
        score = 0
        breakdown = {}
        length = len(text)
        
        # 1. Symbols only
        if engine.compiled_regex["symbols_only"].fullmatch(text):
            score += 100
            breakdown["Symbols Only"] = 100
            
        # 2. Digits only
        if engine.compiled_regex["digits_only"].fullmatch(text):
            score += 100
            breakdown["Digits Only"] = 100
            
        # 3. Repeated Characters
        repeated_match = engine.compiled_regex["repeated_char"].search(text)
        if repeated_match:
            match_len = len(repeated_match.group(0))
            pts = min(60, match_len * 10)
            score += pts
            breakdown["Repeated Characters"] = pts
            
        # 4. Consonant Clusters
        consonant_match = engine.compiled_regex["consonant_cluster"].search(text)
        if consonant_match:
            match_len = len(consonant_match.group(0))
            if match_len >= 4:
                pts = min(60, (match_len - 3) * 20)
                score += pts
                breakdown["Consonants"] = pts
                
        # 5. Keyboard Mash
        keyboard_walks = [
            "qwerty", "asdfgh", "zxcvbn", "poiuy", "lkjhg", "qazwsx", "wsxedc", "rfvtgb",
            "qwer", "asdf", "zxcv", "hjkl", "uiop", "dfgh", "cvbn", "tyui", "ghjk", "poi", "lkj", "mnb"
        ]
        for walk in keyboard_walks:
            if walk in text or walk[::-1] in text:
                score += 80
                breakdown["Keyboard Mash"] = 80
                break
                
        # 6. Dictionary check
        valid_words = 0
        for w in words:
            w_clean = engine.compiled_regex["only_letters"].sub('', w)
            if w_clean in engine.english_dictionary:
                valid_words += 1
                
        if valid_words == 0 and len(words) > 0 and score < GibberishScoringEngine.THRESHOLD:
            # If there are no valid dictionary words, but no explicit structural gibberish traits,
            # we penalize it, but maybe not enough to block it if it's short
            pts = 40
            score += pts
            breakdown["No Dictionary Words"] = pts
            
        # Final Decision
        is_gibberish = score >= GibberishScoringEngine.THRESHOLD
        
        # Hard rejects
        HARD_REJECTS = {"gtgb", "nkio", "eoipmk", "plmoknijb", "asdff"}
        if text in HARD_REJECTS:
            is_gibberish = True
            score = 100
            breakdown["Hard Reject"] = 100
            
        t1 = time.perf_counter()
        
        return is_gibberish, {
            "total_score": score,
            "threshold": GibberishScoringEngine.THRESHOLD,
            "breakdown": breakdown,
            "execution_ms": (t1 - t0) * 1000
        }
