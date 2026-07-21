from .providers.groq_provider import GroqProvider

_llm_instance = None

def get_llm_provider():
    global _llm_instance
    if not _llm_instance:
        _llm_instance = GroqProvider()
    return _llm_instance
