# backend/steps/session_memory_step.py
import re
from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult
from services.response_service import ResponseService
from core.constants import INTENT_GREETING

class SessionMemoryStep(PipelineStep):
    def __init__(self):
        # Patterns for detecting name introduction
        # e.g., "My name is Akhlaque", "I'm Akhlaque", "Call me Akhlaque", "I am Akhlaque"
        self.intro_patterns = [
            re.compile(r"my name is\s+([A-Za-z]+)", re.IGNORECASE),
            re.compile(r"i['’]m\s+([A-Za-z]+)", re.IGNORECASE),
            re.compile(r"i am\s+([A-Za-z]+)", re.IGNORECASE),
            re.compile(r"call me\s+([A-Za-z]+)", re.IGNORECASE),
            re.compile(r"you can call me\s+([A-Za-z]+)", re.IGNORECASE)
        ]

        # Patterns for name lookup
        self.lookup_patterns = [
            re.compile(r"what is my name", re.IGNORECASE),
            re.compile(r"what['’]s my name", re.IGNORECASE),
            re.compile(r"do you know my name", re.IGNORECASE),
            re.compile(r"remember my name", re.IGNORECASE),
            re.compile(r"who am i", re.IGNORECASE)
        ]

    def process(self, context: PipelineContext) -> PipelineResult:
        text = context.normalized_message.strip()
        memory = context.metadata.get("memory") or {}
        
        # 1. Check for Memory Lookup
        for pattern in self.lookup_patterns:
            if pattern.search(text):
                user_name = memory.get("user_name")
                
                context.metadata["Memory Lookup"] = "Found"
                context.metadata["Storage"] = "localStorage"
                
                if user_name:
                    if "who am i" in text.lower():
                        response = f"You are {user_name}."
                    else:
                        response = f"Your name is {user_name}."
                else:
                    response = "I don't know your name yet. You can tell me by saying \"My name is John.\""
                
                return PipelineResult(
                    stop=True,
                    intent="Memory Lookup",
                    response=response
                )

        # 2. Check for Name Introduction (Full phrase)
        extracted_name = None
        is_update = False
        for pattern in self.intro_patterns:
            match = pattern.search(text)
            if match:
                extracted_name = match.group(1).capitalize()
                is_update = True
                break
                
        # 3. Check for Greeting + Name combination
        if context.metadata.get("greeting_detected"):
            routing = context.metadata.get("routing")
            
            if not extracted_name and routing == "Greeting + Name":
                extracted_name = text.capitalize()
                is_update = True
                
            if extracted_name:
                actions = [{
                    "type": "UPDATE_MEMORY",
                    "payload": {
                        "user_name": extracted_name
                    }
                }]
                
                context.metadata["Memory Updated"] = True
                context.metadata["Extracted Name"] = extracted_name
                context.metadata["Storage"] = "localStorage"
                
                prefix = context.metadata.get("greeting_prefix", "Hello!")
                response = f"{prefix} {extracted_name}! Nice to meet you. How can i help you today."
                return PipelineResult(
                    stop=True,
                    intent=INTENT_GREETING,
                    response=response,
                    actions=actions
                )
            elif routing == "Greeting (Empty remaining query)":
                prefix = context.metadata.get("greeting_prefix", "Hello!")
                base_opener = context.metadata.get("greeting_token", "Hello")
                final_response = ResponseService.get_sequential_response(
                    context.session_id, 
                    f"greeting_{base_opener.lower()}", 
                    f"{prefix} How can I assist you today?"
                )
                return PipelineResult(
                    stop=True,
                    intent=INTENT_GREETING,
                    response=final_response
                )
        
        if extracted_name:
            # It was just "My name is Akhlaque" without a greeting
            actions = [{
                "type": "UPDATE_MEMORY",
                "payload": {
                    "user_name": extracted_name
                }
            }]
            
            context.metadata["Memory Updated"] = True
            context.metadata["Extracted Name"] = extracted_name
            context.metadata["Storage"] = "localStorage"
            
            if is_update:
                response = f"Got it! I'll remember that your name is {extracted_name}."
                return PipelineResult(
                    stop=True,
                    intent="Memory Update",
                    response=response,
                    actions=actions
                )

        return PipelineResult(continue_pipeline=True)
