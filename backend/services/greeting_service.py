# backend/services/greeting_service.py
import random
from repositories.registry import greeting_repo
import repositories.seed  # Ensure seed is loaded

class GreetingService:
    last_generic_greeting = None

    @classmethod
    def get_greeting(cls, normalized_text: str) -> str:
        words = normalized_text.split()
        
        # We can still keep some fast string checks or we could move them entirely to DB.
        # But for now, we just pull the response from the greeting_repo
        
        greetings_db = greeting_repo.get_all(limit=1000)
        enabled_greetings = [g.greeting_text for g in greetings_db if g.enabled]
        
        if not enabled_greetings:
            return "Hello! How can I assist you?"
            
        available_greetings = [g for g in enabled_greetings if g != cls.last_generic_greeting]
        if not available_greetings:
            available_greetings = enabled_greetings
            
        response_text = random.choice(available_greetings)
        cls.last_generic_greeting = response_text
        return response_text
