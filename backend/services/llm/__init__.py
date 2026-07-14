from .providers.gemini_provider import GeminiProvider

_llm_instance = None

def get_llm_provider():
    global _llm_instance
    if not _llm_instance:
        _llm_instance = GeminiProvider()
    return _llm_instance
