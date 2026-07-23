from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseLLMProvider(ABC):
    """
    Base class for LLM Providers to ensure a standard interface.
    """
    
    @abstractmethod
    def generate_response(self, prompt: str, system_prompt: str, timeout: int) -> Dict[str, Any]:
        """
        Generate a response from the LLM provider.
        
        Args:
            prompt (str): The user query and context.
            system_prompt (str): The system instructions.
            timeout (int): The timeout in seconds.
            
        Returns:
            Dict[str, Any]: A dictionary containing:
                - "success": bool indicating if the generation was successful.
                - "response": str with the generated markdown.
                - "error": str with the error message if success is False.
        """
        pass
