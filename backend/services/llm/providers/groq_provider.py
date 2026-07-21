import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any
from .base import BaseLLMProvider, LLMResult
from core.logger import get_logger

logger = get_logger(__name__)

class GroqProvider(BaseLLMProvider):
    def __init__(self):
        super().__init__()
        self.api_key = os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            logger.warning("GROQ_API_KEY is not set. API calls will fail.")
            
    def generate(self, prompt: str, config: Dict[str, Any]) -> LLMResult:
        if not self.api_key:
            raise ValueError("Groq API Key is missing.")
            
        system_prompt = config.get("system_prompt", "You are a helpful assistant.")
        temperature = config.get("temperature", 0.2)
        max_tokens = config.get("max_tokens", 1000)
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        
        # Groq Llama 3 API format
        payload = {
            "model": "llama-3.1-8b-instant", 
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{prompt}\n\nPlease output your final answer as a JSON object with a single key 'response' containing your text."}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"}
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        
        try:
            with urllib.request.urlopen(req) as response:
                result_data = json.loads(response.read().decode("utf-8"))
                
            output_text = result_data["choices"][0]["message"]["content"]
            usage = result_data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            
            # Approximate Groq Llama 3 cost
            cost = ((input_tokens + output_tokens) / 1000000) * 0.05
            
            return LLMResult(
                text=output_text,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=cost,
                model="llama3-8b-8192"
            )
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            logger.error(f"Groq API Error: {e.code} - {error_body}")
            raise RuntimeError(f"Groq generation failed: {error_body}")
        except Exception as e:
            logger.error(f"Groq Request Error: {e}")
            raise
