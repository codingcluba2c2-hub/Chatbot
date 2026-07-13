# backend/services/faq_service.py
from repositories.registry import faq_repo

class FAQService:
    @staticmethod
    def get_response(query: str) -> str:
        # A simple keyword match or alias match for now
        faqs = faq_repo.get_all(limit=1000)
        query_lower = query.lower()
        
        for faq in faqs:
            if not faq.enabled:
                continue
            if query_lower == faq.question.lower() or query_lower in [a.lower() for a in faq.aliases]:
                return faq.answer
                
            # Basic keyword matching as a fallback
            if faq.keywords and any(k.lower() in query_lower for k in faq.keywords):
                return faq.answer
                
        return "FAQ matched placeholder"
