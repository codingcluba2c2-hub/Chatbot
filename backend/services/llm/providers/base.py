from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class LLMResult:
    def __init__(self, text: str, input_tokens: int, output_tokens: int, cost: float, model: str):
        self.text = text
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.total_tokens = input_tokens + output_tokens
        self.cost = cost
        self.model = model

class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, config: Dict[str, Any]) -> LLMResult:
        pass
