from chatbot.pipeline import PipelineStep, PipelineStepResult, PipelineContext
"""
Purpose: Handle greetings.
Responsibilities: Detect and respond to greetings.
Flow: Early step in pipeline.
"""

from datetime import datetime
from chatbot.pipeline import PipelineContext
from chatbot.pipeline import PipelineResult
from rapidfuzz import process, fuzz
from typing import Tuple, Optional
import random
import time
import time

class GreetingEngine:
    # 1. Spelling dictionary for common greetings
    GREETING_DICTIONARY = [
        "hi", "hello", "hey", "heya", "yo", "greetings", 
        "good morning", "morning", "good afternoon", "afternoon", 
        "good evening", "evening", "good night", "night", "gm", "gn"
    ]
    
    # 2. Response Templates
    TEMPLATES = {
        "GENERAL": [
            "Hello! How can I help you today?", "Hi there!", "Nice to see you!",
            "Hello again!", "Hey again!", "Hi 😊How can I help you today?",
            "Hi! How can I assist you?", "Good to see you!",
            "How can I help you today?", "What can I do for you?"
        ],
        "MORNING": [
            "Good morning!", "Morning!", "Good morning 😊", "Morning 👋",
            "Hope you're having a wonderful start to your day.", "Good morning! How can I help?",
            "Top of the morning to you!", "Morning there!", "Good morning, friend!",
            "Have a great morning! What can I do for you?"
        ],
        "AFTERNOON": [
            "Good afternoon!", "Afternoon!", "Good afternoon 😊", "Afternoon 👋",
            "Hope your afternoon is going well.", "Good afternoon! How can I help?",
            "Good afternoon, friend!", "Afternoon there!", "Hope you're having a great day.",
            "Good afternoon! What can I do for you?"
        ],
        "EVENING": [
            "Good evening!", "Evening!", "Good evening 😊", "Evening 👋",
            "Hope you had a great day.", "Good evening! How can I help?",
            "Good evening, friend!", "Evening there!", "Hope your night is going well.",
            "Good evening! What can I do for you?"
        ],
        "NIGHT": [
            "Good night!", "Night!", "Good night 😊", "Night 👋",
            "Hope you had a great day. Sleep well soon!", "Working late? How can I help?",
            "Good night, friend!", "Night there!", "Have a restful night.",
            "Good night! What can I do for you?"
        ]
    }
    
    REPEATS = [
        "Hey again! How's everything going?",
        "Hello again! Looks like we're greeting each other twice 😄 What would you like help with?",
        "😄 We're stuck in a greeting loop. Tell me what you'd like to know.",
        "Hi once more! Still here to help.",
        "Hello again! Ready when you are."
    ]

    def _normalize_greeting(self, text: str) -> Tuple[Optional[str], Optional[str], str]:
        """
        Splits out the greeting, fuzzy-matches it, and returns (corrected_greeting, raw_greeting_matched, remaining_query).
        """
        # We assume greetings are typically the first 1-3 words
        words = text.split()
        for length in [3, 2, 1]:
            if len(words) >= length:
                potential_greeting = " ".join(words[:length])
                
                # Check dictionary
                result = process.extractOne(potential_greeting.lower(), self.GREETING_DICTIONARY, scorer=fuzz.ratio)
                if result:
                    match, score, index = result
                    if score >= 90:
                        remaining = " ".join(words[length:])
                        return match, potential_greeting, remaining
                        
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
            # Normal template selection
            pool = self.TEMPLATES.get(detected_bucket, self.TEMPLATES["GENERAL"])
            selected_template = random.choice(pool)
            
        # 6. Memory Integration
        if user_name and "{name}" not in selected_template:
            # Simply prepend name if not formatted natively
            # Alternatively, we could inject it into the string.
            # For this simple implementation, let's just use it if it's "Hi!" -> "Hi Name!"
            if selected_template.startswith("Hi!"):
                selected_template = selected_template.replace("Hi!", f"Hi {user_name}!")
            elif selected_template.startswith("Hello!"):
                selected_template = selected_template.replace("Hello!", f"Welcome back {user_name}!")
                
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



class GreetingFarewellStep(PipelineStep):
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
            context.metadata["routing"] = "Greeting -> STOP"
            context.current_intent = "Greeting"
            return PipelineResult(
                continue_pipeline=False, 
                stop=True, 
                intent="Greeting", 
                response=engine_result["response"]
            )
                
        # Check Farewell
        from chatbot.detector import detect_farewell
        is_farewell, matched_pattern, confidence, response, remaining_query = detect_farewell(context.normalized_message)
        
        if is_farewell:
            context.metadata["farewell_detected"] = True
            context.metadata["farewell_token"] = matched_pattern
            context.metadata["farewell_prefix"] = response
            
            if not remaining_query.strip():
                context.metadata["routing"] = "Farewell -> STOP"
                context.current_intent = "Farewell"
                return PipelineResult(
                    continue_pipeline=False, 
                    stop=True, 
                    intent="Farewell", 
                    response=response
                )
            else:
                context.metadata["routing"] = "Farewell -> CONTINUE"
                context.metadata["remaining_query"] = remaining_query
                context.normalized_message = remaining_query
        
        return PipelineResult(continue_pipeline=True)


import random
import time
from datetime import datetime
from rapidfuzz import process, fuzz
from typing import Tuple, Optional
from chatbot.memory import SessionManager

class GreetingEngine:
    # 1. Spelling dictionary for common greetings
    GREETING_DICTIONARY = [
        "hi", "hello", "hey", "heya", "yo", "greetings", 
        "good morning", "morning", "good afternoon", "afternoon", 
        "good evening", "evening", "good night", "night", "gm", "gn"
    ]
    
    # 2. Response Templates
    TEMPLATES = {
        "GENERAL": [
            "Hello! How can I help you today?", "Hi there!", "Nice to see you!",
            "Hello again!", "Hey again!", "Hi 😊How can I help you today?",
            "Hi! How can I assist you?", "Good to see you!",
            "How can I help you today?", "What can I do for you?"
        ],
        "MORNING": [
            "Good morning!", "Morning!", "Good morning 😊", "Morning 👋",
            "Hope you're having a wonderful start to your day.", "Good morning! How can I help?",
            "Top of the morning to you!", "Morning there!", "Good morning, friend!",
            "Have a great morning! What can I do for you?"
        ],
        "AFTERNOON": [
            "Good afternoon!", "Afternoon!", "Good afternoon 😊", "Afternoon 👋",
            "Hope your afternoon is going well.", "Good afternoon! How can I help?",
            "Good afternoon, friend!", "Afternoon there!", "Hope you're having a great day.",
            "Good afternoon! What can I do for you?"
        ],
        "EVENING": [
            "Good evening!", "Evening!", "Good evening 😊", "Evening 👋",
            "Hope you had a great day.", "Good evening! How can I help?",
            "Good evening, friend!", "Evening there!", "Hope your night is going well.",
            "Good evening! What can I do for you?"
        ],
        "NIGHT": [
            "Good night!", "Night!", "Good night 😊", "Night 👋",
            "Hope you had a great day. Sleep well soon!", "Working late? How can I help?",
            "Good night, friend!", "Night there!", "Have a restful night.",
            "Good night! What can I do for you?"
        ]
    }
    
    REPEATS = [
        "Hey again! How's everything going?",
        "Hello again! Looks like we're greeting each other twice 😄 What would you like help with?",
        "😄 We're stuck in a greeting loop. Tell me what you'd like to know.",
        "Hi once more! Still here to help.",
        "Hello again! Ready when you are."
    ]

    def _normalize_greeting(self, text: str) -> Tuple[Optional[str], Optional[str], str]:
        """
        Splits out the greeting, fuzzy-matches it, and returns (corrected_greeting, raw_greeting_matched, remaining_query).
        """
        # We assume greetings are typically the first 1-3 words
        words = text.split()
        for length in [3, 2, 1]:
            if len(words) >= length:
                potential_greeting = " ".join(words[:length])
                
                # Check dictionary
                result = process.extractOne(potential_greeting.lower(), self.GREETING_DICTIONARY, scorer=fuzz.ratio)
                if result:
                    match, score, index = result
                    if score >= 90:
                        remaining = " ".join(words[length:])
                        return match, potential_greeting, remaining
                        
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
            # Normal template selection
            pool = self.TEMPLATES.get(detected_bucket, self.TEMPLATES["GENERAL"])
            selected_template = random.choice(pool)
            
        # 6. Memory Integration
        if user_name and "{name}" not in selected_template:
            # Simply prepend name if not formatted natively
            # Alternatively, we could inject it into the string.
            # For this simple implementation, let's just use it if it's "Hi!" -> "Hi Name!"
            if selected_template.startswith("Hi!"):
                selected_template = selected_template.replace("Hi!", f"Hi {user_name}!")
            elif selected_template.startswith("Hello!"):
                selected_template = selected_template.replace("Hello!", f"Welcome back {user_name}!")
                
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


