from chatbot.pipeline import PipelineStep, PipelineStepResult, PipelineContext
"""
Purpose: Handle greetings.
Responsibilities: Detect and respond to greetings.
Flow: Early step in pipeline.
"""

from datetime import datetime
from rapidfuzz import process, fuzz
from typing import Tuple, Optional
import time
from chatbot.memory import SessionManager
from chatbot.pipeline import PipelineResult

class GreetingEngine:
    # 1. Spelling dictionary for common greetings
    GREETING_DICTIONARY = [
        "hi", "hello", "hey", "heya", "yo", "greetings", 
        "good morning", "morning", "good afternoon", "afternoon", 
        "good evening", "evening", "good night", "night", "gm", "gn",
        "bye", "goodbye", "see you", "take care", "thanks", "thank you",
        "welcome", "have a nice day", "have a good day", "nice to meet you",
        "have a nice weekend", "see you tomorrow", "good luck", "welcome back"
    ]
    
    # 2. Response Templates (Cyclical 3-step responses)
    TEMPLATES = {
        "GENERAL": [
            "Hello! How can I help you today?", 
            "Hi again! What can I do for you?", 
            "Hello once more! Ready when you are."
        ],
        "MORNING": [
            "Good morning! How can I help you today?",
            "Good morning again! What can I do for you?",
            "Still morning here! Ready when you are."
        ],
        "AFTERNOON": [
            "Good afternoon! How can I help you today?",
            "Good afternoon again! What can I do for you?",
            "Still afternoon here! Ready when you are."
        ],
        "EVENING": [
            "Good evening! How can I help you today?",
            "Good evening again! What can I do for you?",
            "Still evening here! Ready when you are."
        ],
        "NIGHT": [
            "Good night! How can I help you today?",
            "Good night again! What can I do for you?",
            "Still night here! Ready when you are."
        ]
    }
    
    def _normalize_greeting(self, text: str) -> Tuple[Optional[str], Optional[str], str]:
        """
        Searches for a greeting anywhere in the text. Returns (corrected, matched_text, remaining_query).
        """
        words = text.split()
        for i in range(len(words)):
            # Try 3-word, 2-word, 1-word greetings starting at index i
            for length in [3, 2, 1]:
                if i + length <= len(words):
                    potential = " ".join(words[i:i+length])
                    result = process.extractOne(potential.lower(), self.GREETING_DICTIONARY, scorer=fuzz.ratio)
                    if result:
                        match, score, index = result
                        if score >= 90:
                            # Found a greeting! The remaining query is everything else
                            remaining = " ".join(words[:i] + words[i+length:])
                            return match, potential, remaining
                            
        return None, None, text

    def _get_time_bucket(self, current_hour: int) -> str:
        if 5 <= current_hour < 12:
            return "MORNING"
        elif 12 <= current_hour < 17:
            return "AFTERNOON"
        elif 17 <= current_hour < 21:
            return "EVENING"
        else:
            return "NIGHT"

    def _get_greeting_bucket(self, corrected_greeting: str) -> str:
        if "morning" in corrected_greeting or corrected_greeting == "gm":
            return "MORNING"
        elif "afternoon" in corrected_greeting:
            return "AFTERNOON"
        elif "evening" in corrected_greeting:
            return "EVENING"
        elif "night" in corrected_greeting or corrected_greeting == "gn":
            return "NIGHT"
        return "GENERAL"

    def process(self, raw_message: str, session_id: str, user_name: Optional[str] = None) -> dict:
        t0 = time.perf_counter()
        
        # 1. Normalize
        corrected_greeting, original_greeting_matched, remaining_query = self._normalize_greeting(raw_message)
        
        if not corrected_greeting:
            return {
                "is_greeting": False,
                "remaining_query": raw_message,
                "execution_time_ms": int((time.perf_counter() - t0) * 1000)
            }
            
        # 2. Determine Types
        detected_bucket = self._get_greeting_bucket(corrected_greeting)
        
        # 3. Detect Server Time
        current_dt = datetime.now()
        server_hour = current_dt.hour
        server_time_str = current_dt.strftime("%H:%M")
        server_bucket = self._get_time_bucket(server_hour)
        
        # 4. Conversation Awareness
        session = SessionManager.get_session(session_id) or {}
        count = session.get("greeting_count", 0) + 1
        SessionManager.update_session(session_id, {"greeting_count": count})
        
        # 5. Template Selection
        selected_template = ""
        
        if detected_bucket != "GENERAL" and detected_bucket != server_bucket:
            # Time Mismatch Handling
            if detected_bucket == "MORNING":
                if server_bucket in ["EVENING", "NIGHT"]:
                    selected_template = f"Good {server_bucket.lower()}! 😊 Looks like it's already {server_bucket.lower()} here. How can I help you today?"
                else:
                    selected_template = f"Good {server_bucket.lower()}! Looks like it's {server_bucket.lower()} here. How can I assist you?"
            elif detected_bucket == "NIGHT":
                if server_bucket in ["MORNING", "AFTERNOON"]:
                    selected_template = "Looks like it's still daytime 😊 How can I help you?"
                else:
                    selected_template = f"Good {server_bucket.lower()}! How can I assist you?"
            elif detected_bucket == "EVENING":
                if server_bucket == "MORNING":
                    selected_template = "Good morning! 😊 Looks like it's morning here. How can I assist you?"
                else:
                    selected_template = f"Good {server_bucket.lower()}! How can I help you?"
            else:
                # Default mismatch
                selected_template = f"Actually, it's {server_bucket.lower()} here! 😊 How can I help?"
        else:
            # Normal template selection using cyclical rotation based on greeting_count
            pool = self.TEMPLATES.get(detected_bucket, self.TEMPLATES["GENERAL"])
            index = (count - 1) % len(pool)
            selected_template = pool[index]
            
        # Enterprise Grade Name Extraction
        extracted_name = None
        if remaining_query and len(remaining_query.split()) == 1:
            lower_remaining = remaining_query.lower().strip()
            excluded = ["there", "friend", "man", "bro", "how", "what", "can", "bot", "assistant", "again"]
            # Basic gibberish check for the name (no >=4 consecutive consonants, has vowels)
            import re
            has_vowels = bool(re.search(r'[aeiouy]', lower_remaining))
            has_smashes = bool(re.search(r'(.)\1{3,}', lower_remaining))
            has_consonant_cluster = bool(re.search(r'[bcdfghjklmnpqrstvwxz]{4,}', lower_remaining))
            
            if not any(ex in lower_remaining for ex in excluded) and has_vowels and not has_smashes and not has_consonant_cluster:
                extracted_name = remaining_query.title()
                # Clear remaining query since it was just a name
                remaining_query = ""
                
        final_user_name = extracted_name or user_name
        
        # Memory Integration
        if final_user_name:
            if extracted_name:
                from chatbot.memory import ConversationMemoryService
                ConversationMemoryService.update_context(session_id, {"preferred_name": extracted_name, "user_name": extracted_name})
                
            bold_name = f"**{final_user_name}**"
                
            if "{name}" in selected_template:
                selected_template = selected_template.replace("{name}", bold_name)
            else:
                # Safely inject name before first punctuation, or append it if none
                import re
                if re.search(r'[!.,]', selected_template):
                    selected_template = re.sub(r'^([^!.,]+)([!.,])', rf'\1 {bold_name}\2', selected_template, 1)
                else:
                    selected_template = f"{selected_template} {bold_name}"
                    
        t1 = time.perf_counter()
        
        return {
            "is_greeting": True,
            "response": selected_template,
            "remaining_query": remaining_query,
            "metadata": {
                "greeting_type": detected_bucket,
                "corrected_greeting": f"{original_greeting_matched} -> {corrected_greeting}",
                "detected_time": server_time_str,
                "time_bucket": server_bucket,
                "greeting_count": count,
                "selected_template": selected_template,
                "remaining_query": remaining_query,
                "execution_time_ms": int((t1 - t0) * 1000)
            }
        }

class GreetingStep(PipelineStep):
    def __init__(self):
        super().__init__()
        self.greeting_engine = GreetingEngine()
        
    def process(self, context: PipelineContext) -> PipelineResult:
        # Check Greeting
        engine_result = self.greeting_engine.process(
            context.normalized_message, 
            context.session_id, 
            context.metadata.get("memory", {}).get("preferred_name") or context.metadata.get("memory", {}).get("user_name")
        )
        
        if engine_result.get("is_greeting"):
            context.metadata.update(engine_result["metadata"])
            context.metadata["greeting_detected"] = True
            context.metadata["greeting_prefix"] = engine_result["response"]
            
            remaining = engine_result.get("remaining_query", "").strip()
            
            if not remaining:
                context.metadata["routing"] = "Greeting -> STOP"
                context.current_intent = "Greeting"
                return PipelineResult(
                    continue_pipeline=False, 
                    stop=True, 
                    intent="Greeting", 
                    response=engine_result["response"]
                )
            else:
                context.metadata["routing"] = "Greeting -> CONTINUE"
                context.normalized_message = remaining
        
        return PipelineResult(continue_pipeline=True)
