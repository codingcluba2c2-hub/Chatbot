import time
import os
import json
from typing import Dict, Any
from .base import BaseLLMProvider, LLMResult
from core.logger import get_logger

logger = get_logger(__name__)

class GeminiProvider(BaseLLMProvider):
    def __init__(self):
        super().__init__()
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.client = None
        if not self.api_key:
            logger.warning("GEMINI_API_KEY is not set. API calls will fail.")

    def _get_client(self):
        if not self.client and self.api_key:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
        return self.client

    def generate(self, prompt: str, config: Dict[str, Any]) -> LLMResult:
        if "Expand this query" in prompt:
            original_query = prompt.split("'")[1] if "'" in prompt else prompt
            return LLMResult(
                text=original_query,
                input_tokens=0,
                output_tokens=0,
                cost=0.0,
                model="gemini-2.0-flash"
            )
            
        system_prompt = config.get("system_prompt", "You are a helpful assistant.")
        temperature = config.get("temperature", 0.3)
        max_tokens = config.get("max_tokens", 500)
        
        try:
            client = self._get_client()
            if not client:
                raise ValueError("Gemini Client could not be initialized (Missing API Key)")

            prompt_with_json = f"{prompt}\n\nPlease output your final answer as a JSON object with a single key 'response' containing your text."
            
            from google.genai import types
            
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt_with_json,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    response_mime_type="application/json"
                )
            )
            
            output_text = response.text
            
            # Estimate tokens if usage_metadata not populated properly in the new SDK
            input_tokens = len(prompt_with_json) // 4
            output_tokens = len(output_text) // 4
                
            cost = ((input_tokens + output_tokens) / 1000000) * 0.50
            
            return LLMResult(
                text=output_text,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=cost,
                model="gemini-2.0-flash"
            )
        except Exception as e:
            logger.error(f"Gemini API Error: {e}")
            raise
