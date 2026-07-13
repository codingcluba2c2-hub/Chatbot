# backend/services/response_service.py
import datetime
import re
from utils.responses import FALLBACK_MESSAGE
from services.session_manager import SessionManager

class ResponseService:
    @staticmethod
    def get_fallback() -> str:
        return FALLBACK_MESSAGE

    @staticmethod
    def adjust_for_time_of_day(response: str) -> str:
        hour = datetime.datetime.now().hour
        if hour < 12:
            correct_greeting = "Good morning"
        elif 12 <= hour < 17:
            correct_greeting = "Good afternoon"
        else:
            correct_greeting = "Good evening"
            
        pattern = re.compile(r'(good\s+(morning|afternoon|evening))', re.IGNORECASE)
        
        def replacer(match):
            orig = match.group(1)
            if orig[0].isupper():
                return correct_greeting
            return correct_greeting.lower()
            
        return pattern.sub(replacer, response)

    @staticmethod
    def get_sequential_response(session_id: str, intent_key: str, raw_response: str) -> str:
        if not raw_response:
            return ""
            
        responses = [r.strip() for r in raw_response.split('||') if r.strip()]
        if not responses:
            return raw_response
            
        session = SessionManager.get_session(session_id)
        if not session:
            SessionManager.create_session(session_id)
            session = SessionManager.get_session(session_id) or {}
            
        counters = session.get("response_counters", {})
        count = counters.get(intent_key, 0)
        
        selected_response = responses[count % len(responses)]
        
        counters[intent_key] = count + 1
        session["response_counters"] = counters
        SessionManager.update_session(session_id, session)
        
        return ResponseService.adjust_for_time_of_day(selected_response)
