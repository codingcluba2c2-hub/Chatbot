import time
from typing import Dict, Any, Tuple
from chatbot.in_memory_engine import engine
from core.logger import get_logger

logger = get_logger("scope_engine")

class KnowledgeScopeEngine:
    """
    Fast deterministic engine to verify if a query belongs to the enterprise domain.
    Target execution time: < 1 ms.
    """
    
    @staticmethod
    def evaluate(raw_text: str) -> Tuple[bool, Dict[str, Any]]:
        t0 = time.perf_counter()
        
        text = raw_text.lower()
        text = engine.compiled_regex["unicode_noise"].sub('', text)
        words = engine.compiled_regex["collapse_spaces"].sub(' ', text).strip().split()
        
        # We strip punctuation from words to check against our keyword set
        clean_words = []
        for w in words:
            cw = engine.compiled_regex["only_letters"].sub('', w)
            if cw:
                clean_words.append(cw)
                
        # If no recognizable words, let it pass (could be weird acronyms that aren't gibberish)
        # Actually Gibberish Engine handles that. So here we just check if it matches enterprise scope.
        if not clean_words:
            t1 = time.perf_counter()
            return True, {"in_scope": True, "reason": "no_letters", "execution_ms": (t1 - t0) * 1000}
            
        in_scope = False
        matched_keyword = None
        
        for w in clean_words:
            if w in engine.scope_keywords:
                in_scope = True
                matched_keyword = w
                break
                
            # Basic stemming check (e.g., 'services' -> 'service')
            if w.endswith('s') and w[:-1] in engine.scope_keywords:
                in_scope = True
                matched_keyword = w[:-1]
                break
                
            if w.endswith('es') and w[:-2] in engine.scope_keywords:
                in_scope = True
                matched_keyword = w[:-2]
                break
                
            if w.endswith('ing') and w[:-3] in engine.scope_keywords:
                in_scope = True
                matched_keyword = w[:-3]
                break

        # Also check against alias intents to be safe (they are in scope)
        if not in_scope:
            for alias in engine.all_aliases:
                if alias in text:
                    in_scope = True
                    matched_keyword = alias
                    break
        
        t1 = time.perf_counter()
        return in_scope, {
            "in_scope": in_scope,
            "matched_keyword": matched_keyword,
            "execution_ms": (t1 - t0) * 1000
        }
