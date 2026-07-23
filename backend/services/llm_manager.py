import os
import time
import logging
from typing import Dict, Any, List
from providers.groq_provider import GroqProvider
from providers.gemini_provider import GeminiProvider
from providers.local_formatter import LocalMarkdownFormatter

logger = logging.getLogger("llm_manager")

class LLMProviderManager:
    def __init__(self):
        self.providers = {
            "groq": GroqProvider(),
            "gemini": GeminiProvider()
        }
        self.local_formatter = LocalMarkdownFormatter()
        
        self.primary = os.getenv("PRIMARY_LLM", "groq")
        self.secondary = os.getenv("SECONDARY_LLM", "gemini")
        self.groq_timeout = int(os.getenv("GROQ_TIMEOUT", 8))
        self.gemini_timeout = int(os.getenv("GEMINI_TIMEOUT", 8))
        self.failover_enabled = os.getenv("LLM_FAILOVER", "true").lower() == "true"
        
        self.health_cache = {
            "groq": 0,
            "gemini": 0
        }
        self.cooldown_period = 60  # seconds

    def _is_provider_healthy(self, name: str) -> bool:
        if name not in self.health_cache:
            return True
        time_since_failure = time.time() - self.health_cache[name]
        return time_since_failure > self.cooldown_period

    def _mark_failed(self, name: str):
        self.health_cache[name] = time.time()

    def generate(self, prompt: str, system_prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attempt generation using primary, fallback to secondary, and finally local.
        Returns result dict with final trace.
        """
        trace = {
            "Groq Status": "Skipped",
            "Gemini Status": "Skipped",
            "Provider Attempt": 0,
            "Chosen Provider": "None",
            "Response Source": "None",
            "Fallback Used": False
        }
        
        sequence = [self.primary, self.secondary] if self.failover_enabled else [self.primary]
        timeouts = {"groq": self.groq_timeout, "gemini": self.gemini_timeout}
        
        final_response = None
        
        for provider_name in sequence:
            if not self._is_provider_healthy(provider_name):
                trace[f"{provider_name.capitalize()} Status"] = "Cooldown (Failed Recently)"
                continue
                
            trace["Provider Attempt"] += 1
            provider = self.providers.get(provider_name)
            
            if not provider:
                continue
                
            logger.info(f"Attempting LLM generation with {provider_name}")
            result = provider.generate_response(prompt, system_prompt, timeout=timeouts.get(provider_name, 8))
            
            if result.get("success"):
                trace[f"{provider_name.capitalize()} Status"] = "Success"
                trace["Chosen Provider"] = provider_name.capitalize()
                trace["Response Source"] = provider_name.capitalize()
                final_response = result.get("response")
                break
            else:
                error_msg = result.get("error", "Unknown Error")
                logger.warning(f"{provider_name.capitalize()} failed: {error_msg}")
                trace[f"{provider_name.capitalize()} Status"] = f"Failed ({error_msg})"
                self._mark_failed(provider_name)
                
        # If all providers failed, fallback to local formatter
        if not final_response:
            logger.warning("All LLM providers failed. Using Local Enterprise Formatter.")
            print(f"Provider {self.primary.capitalize()} Failed")
            print(f"Provider {self.secondary.capitalize()} Failed")
            print("Using Local Enterprise Formatter")
            
            trace["Fallback Used"] = True
            trace["Chosen Provider"] = "LocalFormatter"
            trace["Response Source"] = "Local Markdown Formatter"
            
            rag_context = context.get("rag_context", "")
            chunks = context.get("rag_chunks", [])
            local_result = self.local_formatter.generate_response(chunks, rag_context)
            final_response = local_result.get("response", "Could not format context locally.")
            
        return {
            "response": final_response,
            "trace": trace
        }

_instance = None
def get_llm_manager() -> LLMProviderManager:
    global _instance
    if _instance is None:
        _instance = LLMProviderManager()
    return _instance
