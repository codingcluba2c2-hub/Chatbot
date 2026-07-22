from core.logger import get_logger
"""
Purpose: LLM integration.
Responsibilities: Connect to Groq, Gemini, etc.
Flow: Used by generation steps.
"""

from abc import ABC, abstractmethod
from chatbot.pipeline import PipelineContext
from typing import Dict, Any, List, Optional, Tuple
from typing import Tuple, Dict, Any
import json
import os
import re
import time
import urllib.error
import urllib.request


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
        rag_context = context.metadata.get("rag_context", "")
        
        system_prompt = (
            "You are a highly secure Enterprise AI Assistant.\n"
            "STRICT RAG RULES:\n"
            "1. If CONTEXT INFORMATION (RAG) is provided, you MUST base your entire answer on it.\n"
            "2. NEVER invent facts, salaries, numerical figures, or use outside world knowledge if company data exists.\n"
            "3. Maintain strict Markdown formatting. Preserve document headings, bullet points, numbered lists, and tables.\n"
            "4. Do NOT combine unrelated chunks. Do NOT invent sections that do not exist in the context."
        )
        
        prompt = PromptBuilder.build(
            user_message=context.original_message,
            system_instructions=system_prompt,
            rag_context=rag_context,
            memory_facts={}
        )
        context.metadata["llm_prompt"] = prompt
        
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
            
            context.metadata["llm_output"] = result.text
            
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



_llm_instance = None

def get_llm_provider():
    global _llm_instance
    if not _llm_instance:
        if os.environ.get("GROK_API_KEY"):
            try:
                _llm_instance = GrokProvider()
            except Exception as e:
                logger.error(f"Failed to init GrokProvider: {e}")
                _llm_instance = GroqProvider() if os.environ.get("GROQ_API_KEY") else GeminiProvider()
        elif os.environ.get("GROQ_API_KEY"):
            _llm_instance = GroqProvider()
        else:
            _llm_instance = GeminiProvider()
    return _llm_instance



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



class PromptBuilder:
    @staticmethod
    def build(
        user_message: str, 
        system_instructions: str, 
        rag_context: str, 
        memory_facts: Dict[str, Any], 
        language: str = "en"
    ) -> str:
        
        memory_str = "\n".join([f"- {k}: {v}" for k, v in memory_facts.items()]) if memory_facts else "None"
        
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
            with urllib.request.urlopen(req, timeout=10) as response:
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


class GrokProvider(BaseLLMProvider):
    def __init__(self):
        super().__init__()
        self.api_key = os.environ.get("GROK_API_KEY")
        if not self.api_key:
            logger.warning("GROK_API_KEY is not set. API calls will fail.")
            
    def generate(self, prompt: str, config: Dict[str, Any]) -> LLMResult:
        if not self.api_key:
            raise ValueError("Grok API Key is missing.")
            
        system_prompt = config.get("system_prompt", "You are a helpful assistant.")
        temperature = config.get("temperature", 0.2)
        max_tokens = config.get("max_tokens", 1000)
        
        url = "https://api.x.ai/v1/chat/completions"
        
        payload = {
            "model": "grok-beta", 
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
            with urllib.request.urlopen(req, timeout=15) as response:
                result_data = json.loads(response.read().decode("utf-8"))
                
            output_text = result_data["choices"][0]["message"]["content"]
            usage = result_data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            
            cost = ((input_tokens + output_tokens) / 1000000) * 0.10
            
            return LLMResult(
                text=output_text,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=cost,
                model="grok-2-latest"
            )
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            logger.error(f"Grok API Error: {e.code} - {error_body}")
            raise RuntimeError(f"Grok generation failed: {error_body}")
        except Exception as e:
            logger.error(f"Grok Request Error: {e}")
            raise
