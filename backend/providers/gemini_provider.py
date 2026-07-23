import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any
from .base_provider import BaseLLMProvider

class GeminiProvider(BaseLLMProvider):
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = os.getenv("MODEL", "gemini-1.5-flash")
        self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
    def generate_response(self, prompt: str, system_prompt: str, timeout: int) -> Dict[str, Any]:
        if not self.api_key:
            return {"success": False, "response": "", "error": "GEMINI_API_KEY not found"}
            
        # Gemini REST API structure
        data = {
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2
            }
        }
        
        req = urllib.request.Request(
            self.endpoint,
            data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                result_bytes = response.read()
                if not result_bytes:
                    return {"success": False, "response": "", "error": "Empty Response"}
                    
                result_json = json.loads(result_bytes.decode("utf-8"))
                
                candidates = result_json.get("candidates", [])
                if not candidates:
                    return {"success": False, "response": "", "error": "No candidates in response"}
                    
                content = candidates[0].get("content", {}).get("parts", [])
                if not content:
                    return {"success": False, "response": "", "error": "Empty content parts in response"}
                    
                text = content[0].get("text", "")
                
                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, dict) and "response" in parsed:
                        text = parsed["response"]
                except json.JSONDecodeError:
                    pass
                    
                return {"success": True, "response": text, "error": None}
                
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
