import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any
from .base_provider import BaseLLMProvider

class GroqProvider(BaseLLMProvider):
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.endpoint = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama3-8b-8192" # Default, can be configurable
        
    def generate_response(self, prompt: str, system_prompt: str, timeout: int) -> Dict[str, Any]:
        if not self.api_key:
            return {"success": False, "response": "", "error": "GROQ_API_KEY not found"}
            
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        }
        
        req = urllib.request.Request(
            self.endpoint,
            data=json.dumps(data).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            },
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                result_bytes = response.read()
                if not result_bytes:
                    return {"success": False, "response": "", "error": "Empty Response"}
                    
                result_json = json.loads(result_bytes.decode("utf-8"))
                
                # Check for standard OpenAI-compatible response structure
                choices = result_json.get("choices", [])
                if not choices:
                    return {"success": False, "response": "", "error": "No choices in response"}
                    
                content = choices[0].get("message", {}).get("content", "")
                if not content:
                    return {"success": False, "response": "", "error": "Empty content in response"}
                    
                # The prompt asks for JSON but sometimes LLMs wrap it in codeblocks or return string
                # We expect the AI to return string (markdown) based on system prompt.
                
                # Try to parse if it's returning a JSON structure wrapped inside content
                try:
                    parsed = json.loads(content)
                    if isinstance(parsed, dict) and "response" in parsed:
                        content = parsed["response"]
                except json.JSONDecodeError:
                    pass
                    
                return {"success": True, "response": content, "error": None}
                
        except urllib.error.HTTPError as e:
            return {"success": False, "response": "", "error": f"HTTPError {e.code}: {e.reason}"}
        except urllib.error.URLError as e:
            return {"success": False, "response": "", "error": f"URLError: {e.reason}"}
        except TimeoutError:
            return {"success": False, "response": "", "error": "Timeout"}
        except json.JSONDecodeError:
            return {"success": False, "response": "", "error": "Invalid JSON"}
        except Exception as e:
            return {"success": False, "response": "", "error": f"Exception: {str(e)}"}
