# backend/services/gibberish_service.py
from utils.responses import GIBBERISH_MESSAGE

class GibberishService:
    @staticmethod
    def get_response() -> str:
        return GIBBERISH_MESSAGE
