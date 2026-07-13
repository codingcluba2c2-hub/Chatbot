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
