import os
import json

os.makedirs('backend/services/llm/providers', exist_ok=True)
os.makedirs('backend/services/llm/guardrails', exist_ok=True)
os.makedirs('backend/services/llm/prompts', exist_ok=True)

with open('backend/services/llm/providers/base.py', 'w') as f:
    f.write('''\
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
''')

with open('backend/services/llm/providers/gemini_provider.py', 'w') as f:
    f.write('''\
import time
from .base import BaseLLMProvider, LLMResult

class GeminiProvider(BaseLLMProvider):
    def generate(self, prompt: str, config: Dict[str, Any]) -> LLMResult:
        # Mock Gemini Generation
        # Calculates fake tokens based on string length to simulate a real model
        input_tokens = len(prompt) // 4
        
        # Simulate processing time
        time.sleep(0.5)
        
        output_text = (
            "{\\n"
            "  \\"response\\": \\"Based on the provided knowledge, this is a highly deterministic and safe response.\\",\\n"
            "  \\"components\\": [],\\n"
            "  \\"actions\\": []\\n"
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
''')

with open('backend/services/llm/guardrails/input_guardrail.py', 'w') as f:
    f.write('''\
import re
from typing import Tuple

class InputGuardrail:
    RESTRICTED_PATTERNS = [
        r"(?i)ignore previous instructions",
        r"(?i)system prompt",
        r"(?i)drop table",
        r"(?i)SELECT .* FROM",
    ]

    @staticmethod
    def validate(user_message: str) -> Tuple[bool, str]:
        for pattern in InputGuardrail.RESTRICTED_PATTERNS:
            if re.search(pattern, user_message):
                return False, f"Prompt injection or restricted phrase detected."
                
        return True, "Passed"
''')

with open('backend/services/llm/guardrails/output_validator.py', 'w') as f:
    f.write('''\
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
''')

with open('backend/services/llm/prompts/builder.py', 'w') as f:
    f.write('''\
from typing import Dict, Any, List

class PromptBuilder:
    @staticmethod
    def build(
        user_message: str, 
        system_instructions: str, 
        rag_context: str, 
        memory_facts: Dict[str, Any], 
        language: str = "en"
    ) -> str:
        
        memory_str = "\\n".join([f"- {k}: {v}" for k, v in memory_facts.items()]) if memory_facts else "None"
        
        prompt = f"""
{system_instructions}

---
CONTEXT INFORMATION (RAG):
{rag_context if rag_context else 'None'}

---
CONVERSATION MEMORY:
{memory_str}

---
LANGUAGE: {language}

---
USER QUERY:
{user_message}

---
FORMAT REQUIREMENT:
You must reply ONLY with a valid JSON object matching this schema:
{{
  "response": "The text to show the user",
  "components": [],
  "actions": []
}}
"""
        return prompt.strip()
''')

with open('backend/services/llm/router.py', 'w') as f:
    f.write('''\
import time
from typing import Dict, Any, Tuple
from pipeline.pipeline_context import PipelineContext
from .providers.gemini_provider import GeminiProvider
from .guardrails.input_guardrail import InputGuardrail
from .guardrails.output_validator import OutputValidator
from .prompts.builder import PromptBuilder
from core.logger import get_logger

logger = get_logger(__name__)

class LLMRouter:
    def __init__(self):
        self.provider = GeminiProvider()
        
    def should_call_llm(self, context: PipelineContext) -> bool:
        # Strict deterministic checking: If any other module handled it, skip LLM.
        # However, LLMStep is usually the last step.
        # If it reaches here, it means we MIGHT need LLM.
        return True

    def execute(self, context: PipelineContext) -> Tuple[bool, str, Dict[str, Any]]:
        metrics = {
            "validation_time_ms": 0,
            "prompt_build_time_ms": 0,
            "llm_execution_time_ms": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "cost": 0,
            "model": "none",
            "status": "failed"
        }
        
        # 1. Input Guardrails
        start_time = time.time()
        is_safe, reason = InputGuardrail.validate(context.original_message)
        metrics["validation_time_ms"] += (time.time() - start_time) * 1000
        
        if not is_safe:
            metrics["status"] = "blocked_by_input_guardrail"
            context.metadata["llm_metrics"] = metrics
            return False, reason, {}

        # 2. Build Prompt
        start_time = time.time()
        
        # Extract RAG context if any
        rag_context = ""
        if "rag_metrics" in context.metadata and context.metadata["rag_metrics"]["accepted_count"] > 0:
            # Reconstruct RAG context from previous step or memory
            pass # In reality, we'd pass the actual chunks. 
            
        system_prompt = "You are a highly secure Enterprise AI Assistant."
        
        prompt = PromptBuilder.build(
            user_message=context.original_message,
            system_instructions=system_prompt,
            rag_context=rag_context,
            memory_facts={}
        )
        metrics["prompt_build_time_ms"] = (time.time() - start_time) * 1000
        
        # 3. Execute LLM
        start_time = time.time()
        try:
            config = {"temperature": 0.2, "top_p": 0.95, "top_k": 40}
            result = self.provider.generate(prompt, config)
            metrics["llm_execution_time_ms"] = (time.time() - start_time) * 1000
            
            metrics["input_tokens"] = result.input_tokens
            metrics["output_tokens"] = result.output_tokens
            metrics["cost"] = result.cost
            metrics["model"] = result.model
            
        except Exception as e:
            logger.error(f"LLM Provider Error: {e}")
            metrics["status"] = "provider_error"
            context.metadata["llm_metrics"] = metrics
            return False, "I'm currently unable to process this request.", {}

        # 4. Output Validation
        start_time = time.time()
        is_valid, reason, parsed_data = OutputValidator.validate(result.text)
        metrics["validation_time_ms"] += (time.time() - start_time) * 1000
        
        if not is_valid:
            metrics["status"] = "blocked_by_output_validator"
            context.metadata["llm_metrics"] = metrics
            return False, reason, {}
            
        metrics["status"] = "success"
        context.metadata["llm_metrics"] = metrics
        
        return True, parsed_data.get("response", ""), parsed_data
''')

with open('backend/steps/llm_step.py', 'w') as f:
    f.write('''\
from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult
from services.llm.router import LLMRouter

class LLMStep(PipelineStep):
    def __init__(self):
        self.router = LLMRouter()

    def process(self, context: PipelineContext) -> PipelineResult:
        # If intent is already resolved by Tool or RAG, do not call LLM
        # But this step only fires if earlier steps didn't stop the pipeline.
        
        success, response_text, data = self.router.execute(context)
        
        if success:
            return PipelineResult(
                continue_pipeline=False,
                stop=True,
                intent="LLM_Generated",
                response=response_text,
                components=data.get("components", []),
                actions=data.get("actions", [])
            )
        else:
            return PipelineResult(
                continue_pipeline=False,
                stop=True,
                intent="LLM_Blocked",
                response="I'm sorry, I cannot process that request at this time."
            )
''')
