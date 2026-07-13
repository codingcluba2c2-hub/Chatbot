import json
from typing import Tuple, Dict, Any

class OutputValidator:
    @staticmethod
    def validate(response_text: str) -> Tuple[bool, str, Dict[str, Any]]:
        try:
            # Strip markdown json blocks if present
            cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
            
            data = json.loads(cleaned_text)
            
            if "response" not in data:
                return False, "Missing 'response' field in LLM output.", {}
                
            return True, "Passed", data
            
        except json.JSONDecodeError:
            return False, "Failed to parse JSON response from LLM.", {}
