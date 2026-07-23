import time
import re
import difflib
from rapidfuzz import process, fuzz
from typing import Dict, Any, Tuple
from core.logger import get_logger
from chatbot.in_memory_engine import engine
from chatbot.memory import SessionManager, ConversationMemoryService
from chatbot.utils import INTENT_FAQ
from chatbot.gibberish_engine import GibberishScoringEngine
from chatbot.scope_engine import KnowledgeScopeEngine

def format_trace_steps(times: Dict[str, float]) -> list:
    steps = []
    current_time = time.time() - times.get("Total", 0)
    for k, v in times.items():
        if k == "Total": continue
        steps.append({
            "step_name": f"Fast_{k}",
            "start_time": current_time,
            "status": "success",
            "duration": int(v * 1000),
            "metadata": {}
        })
        current_time += v
    return steps

logger = get_logger("fast_pipeline")

def normalize_text(text: str) -> str:
    # Convert lowercase, collapse spaces
    q = text.lower()
    q = engine.compiled_regex["collapse_spaces"].sub(' ', q).strip()
    return q



def check_greeting(text: str) -> Tuple[bool, str, str]:
    for phrase, match_str, resp in engine.greeting_phrases:
        if text.startswith(phrase):
            rem = text[len(phrase):].strip()
            rem = re.sub(r'^[^\w\s]+', '', rem).strip()
            return True, resp, rem
    return False, "", text

def check_enterprise_overview(text: str) -> bool:
    # Rule 1: Length > 150 chars
    if len(text) > 150:
        return True
        
    # Rule 2: 10+ topics (counting commas as a rough proxy for multiple topics in a list, or just word count if very long)
    if text.count(',') >= 5:
        return True
        
    # Rule 3: Specific comprehensive keywords
    keywords = [
        "everything", "complete", "comprehensive", "overview", "organization", 
        "prepare for interview", "candidate", "before joining", "tell me about company", 
        "know everything", "company profile"
    ]
    if any(k in text.lower() for k in keywords):
        return True
        
    return False

def check_faq_exact(text: str) -> Tuple[bool, Any]:
    if text in engine.faq_exact_map:
        return True, engine.faq_exact_map[text][1]
    
    # Substring check only if text is meaningful length and not just 1-2 words
    if len(text) > 10 and len(text.split()) > 2:
        for phrase, (orig, faq_obj) in engine.faq_exact_map.items():
            if phrase in text:
                return True, faq_obj
            
    return False, None

def check_alias(text: str) -> str:
    # Spell correct first
    words = text.split()
    corrected_words = []
    for w in words:
        corrected_words.append(engine.spelling_dict.get(w, w))
    corrected = " ".join(corrected_words)
    
    # Check alias
    for alias in engine.all_aliases:
        if alias == corrected or f" {alias} " in f" {corrected} ":
            return engine.alias_map[alias]
            
    # Fuzzy match alias
    best_score = 0.0
    best_match = None
    for alias in engine.all_aliases:
        score = difflib.SequenceMatcher(None, corrected, alias).ratio()
        if score > best_score:
            best_score = score
            best_match = alias
            
    if best_score >= 0.85 and best_match:
        return engine.alias_map[best_match]
        
    return ""

def check_rapidfuzz(text: str) -> Tuple[bool, Any]:
    if not engine.faq_rapidfuzz_choices:
        return False, None
    result = process.extractOne(text, engine.faq_rapidfuzz_choices, scorer=fuzz.token_set_ratio)
    if result:
        match, score, index = result
        if score >= 85:
            return True, engine.faq_exact_map[match][1]
    return False, None

def build_faq_response(faq_obj, matched_question: str) -> Dict[str, Any]:
    answer = getattr(faq_obj, "answer", "") or ""
    components = []
    
    children = engine.faq_children_map.get(faq_obj.id, [])
    if children:
        items = [getattr(c, "title", "") for c in children if getattr(c, "title", "")]
        components.append({
            "type": "quickReplies",
            "items": items
        })
            
    return {
        "intent": INTENT_FAQ,
        "response": answer,
        "components": components,
        "metadata": {"matched_question": matched_question, "faq_id": faq_obj.id}
    }

def spell_correction_rapidfuzz(text: str) -> Tuple[bool, str]:
    from chatbot.entity_detector import EntityDetector
    all_enterprise_words = []
    for words in EntityDetector.ENTITIES.values():
        all_enterprise_words.extend(words)
        
    corrected_words = []
    has_correction = False
    
    for word in text.split():
        if len(word) >= 4:
            # Check rapidfuzz against enterprise words
            result = process.extractOne(word, all_enterprise_words, scorer=fuzz.ratio)
            if result:
                match, score, _ = result
                if score >= 85 and match != word:
                    corrected_words.append(match)
                    has_correction = True
                    continue
        corrected_words.append(word)
        
    return has_correction, " ".join(corrected_words)

def run_fast_pipeline(raw_text: str, session_id: str, metadata: dict) -> Dict[str, Any]:
    times = {}
    t_start = time.perf_counter()
    
    # 1. Normalize
    t0 = time.perf_counter()
    norm = normalize_text(raw_text)
    times["Normalize"] = time.perf_counter() - t0
    
    # 1.5 Enterprise Overview Check (Overrides FAQ/Greeting)
    if check_enterprise_overview(raw_text):
        return {
            "success": False,
            "forward_to": "RAG",
            "alias_intent": "ENTERPRISE_OVERVIEW",
            "normalized": norm,
            "trace": {"totalBackendTimeMs": (time.perf_counter() - t_start) * 1000, "steps": format_trace_steps(times)}
        }
    
    # 2. Greeting
    t0 = time.perf_counter()
    is_greeting, greet_resp, remaining = check_greeting(norm)
    times["Greeting"] = time.perf_counter() - t0
    if is_greeting and not remaining:
        times["Total"] = time.perf_counter() - t_start
        
        session = SessionManager.get_session(session_id) or {}
        count = session.get("greeting_count", 0) + 1
        SessionManager.update_session(session_id, {"greeting_count": count})
        
        from chatbot.greeting import GreetingEngine
        greeting_engine = GreetingEngine()
        bucket = greeting_engine._get_greeting_bucket(norm)
        server_hour = time.localtime().tm_hour
        
        pool = greeting_engine.TEMPLATES.get(bucket, greeting_engine.TEMPLATES["GENERAL"])
        index = (count - 1) % len(pool)
        resp = pool[index]
        
        _print_times(times)
        return {
            "success": True,
            "intent": "Greeting",
            "response": resp,
            "components": [],
            "actions": [],
            "trace": {"totalBackendTimeMs": times["Total"] * 1000, "steps": format_trace_steps(times)}
        }
        
    # 3. FAQ Exact
    t0 = time.perf_counter()
    is_faq, faq_obj = check_faq_exact(norm)
    times["FAQ"] = time.perf_counter() - t0
    if is_faq:
        times["Total"] = time.perf_counter() - t_start
        _print_times(times)
        resp_data = build_faq_response(faq_obj, norm)
        return {
            "success": True,
            "intent": resp_data["intent"],
            "response": resp_data["response"],
            "components": resp_data["components"],
            "actions": [],
            "trace": {"totalBackendTimeMs": times["Total"] * 1000, "steps": format_trace_steps(times)}
        }

    # 4. Alias
    t0 = time.perf_counter()
    alias_intent = check_alias(norm)
    times["Alias"] = time.perf_counter() - t0

    # 5. Spell Correction
    t0 = time.perf_counter()
    has_correction, corrected_text = spell_correction_rapidfuzz(norm)
    times["SpellCorrection"] = time.perf_counter() - t0
    
    query_to_use = corrected_text if has_correction else norm

    # 6. Entity Detection
    t0 = time.perf_counter()
    from chatbot.entity_detector import EntityDetector
    has_entity, found_entities = EntityDetector.evaluate(query_to_use)
    times["EntityDetection"] = time.perf_counter() - t0

    # 7. Gibberish Detection
    # Only run Gibberish if we haven't found any meaningful signals
    if not has_entity and not has_correction and not alias_intent:
        t0 = time.perf_counter()
        is_gibberish, gibberish_meta = GibberishScoringEngine.evaluate(raw_text)
        times["Gibberish"] = time.perf_counter() - t0
        
        if is_gibberish:
            from utils.responses import GIBBERISH_MESSAGE
            times["Total"] = time.perf_counter() - t_start
            _print_times(times)
            return {
                "success": True,
                "intent": "Gibberish",
                "response": GIBBERISH_MESSAGE,
                "components": [{
                    "type": "fallback",
                    "prefix": "That doesn't look like a valid message. I couldn't understand",
                    "query": raw_text,
                    "suffix": ". Please try asking a clear question about one of the topics below.",
                    "suggestions": ["Overview", "Office Timings", "Leave Policy", "Contact", "Services", "Career", "Help"]
                }],
                "actions": [],
                "trace": {
                    "totalBackendTimeMs": times["Total"] * 1000, 
                    "steps": format_trace_steps(times),
                    "gibberish_metadata": gibberish_meta
                }
            }

    # 8. RAG Fallthrough
    times["Total"] = time.perf_counter() - t_start
    _print_times(times)
    
    return {
        "success": False,
        "forward_to": "RAG",
        "alias_intent": alias_intent,
        "normalized": query_to_use,
        "entities": found_entities,
        "remaining_query": remaining if is_greeting else query_to_use,
        "trace": {"steps": format_trace_steps(times), "totalBackendTimeMs": times["Total"] * 1000}
    }

def _print_times(times: Dict[str, float]):
    print("\n=========================================")
    print("IN-MEMORY ENGINE TIMING")
    print("=========================================")
    for k, v in times.items():
        if k != "Total":
            print(f"{k:<15} {v * 1000:>8.3f} ms")
    print("-----------------------------------------")
    print(f"Total           {times.get('Total', 0) * 1000:>8.3f} ms")
    print("=========================================\n")
