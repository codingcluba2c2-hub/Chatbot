import time
from typing import Dict, Any
from .base import BaseLLMProvider, LLMResult

class GeminiProvider(BaseLLMProvider):
    def generate(self, prompt: str, config: Dict[str, Any]) -> LLMResult:
        # Mock Gemini Generation
        # Calculates fake tokens based on string length to simulate a real model
        input_tokens = len(prompt) // 4
        
        # Simulate processing time
        time.sleep(0.5)
        
        output_text = (
            "{\n"
            "  \"response\": \"Based on the provided knowledge, this is a highly deterministic and safe response.\",\n"
            "  \"components\": [],\n"
            "  \"actions\": []\n"
            "}"
        )
        
        output_tokens = len(output_text) // 4
        
        # Calculate Mock Cost (e.g., $0.50 per 1M tokens)
        cost = ((input_tokens + output_tokens) / 1000000) * 0.50
        
        return LLMResult(
            text=output_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            model="gemini-1.5-pro-mock"
        )
