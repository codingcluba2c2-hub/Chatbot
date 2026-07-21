import re
import time
from typing import Optional, Tuple
from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult

class MemoryDetectorStep(PipelineStep):
    def __init__(self):
        super().__init__()
        # Patterns for UPDATE
        self.update_patterns = [
            (r"(?i)^(?:my name is|i'm|i am|call me|you can call me|remember my name is|remember me as|save my name as|my name's|my new name is) (.+)", "user_name"),
            (r"(?i)^(?:change my name to|update my name to|update my name) (.+)", "user_name"),
            (r"(?i)^(?:i call you|i can call you|call yourself|your name is|your nickname is|i want to call you|from now on i'll call you) (.+)", "assistant_name")
        ]
        
        # Patterns for DELETE
        self.delete_patterns = [
            (r"(?i)^(?:forget my name|clear my name|delete my name)", "user_name")
        ]
        
        # Patterns for LOOKUP
        self.lookup_patterns = [
            (r"(?i)^(?:what's my name|what is my name|who am i|do you know my name|what do you call me|what should you call me|my name)[?.\s]*$", "user_name"),
            (r"(?i)^(?:what's your name|what is your name|who are you|what do i call you|your name)[?.\s]*$", "assistant_name")
        ]

    def _extract_name(self, text: str) -> str:
        # Simple cleanup (e.g., remove trailing punctuation)
        return re.sub(r'[^\w\s]', '', text).strip().title()

    def process(self, context: PipelineContext) -> PipelineResult:
        t0 = time.perf_counter()
        text = context.normalized_message.strip()
        memory = context.metadata.get("memory", {})
        
        # Check DELETE first
        for pattern, field in self.delete_patterns:
            if re.search(pattern, text):
                t1 = time.perf_counter()
                context.metadata["memory_intent"] = "DELETE"
                context.metadata["detected_field"] = field
                context.metadata["previous_value"] = memory.get(field)
                context.metadata["updated_value"] = None
                context.metadata["storage"] = "localStorage"
                context.metadata["execution_time_ms"] = int((t1 - t0) * 1000)
                
                context.current_intent = "Memory (Delete)"
                return PipelineResult(
                    continue_pipeline=False,
                    stop=True,
                    intent="Memory (Delete)",
                    response="Okay. I've forgotten your saved name.",
                    actions=[{"type": "UPDATE_MEMORY", "payload": {field: None}}]
                )
        
        # Check UPDATE
        for pattern, field in self.update_patterns:
            match = re.match(pattern, text)
            if match:
                value = self._extract_name(match.group(1))
                t1 = time.perf_counter()
                
                context.metadata["memory_intent"] = "UPDATE"
                context.metadata["detected_field"] = field
                context.metadata["previous_value"] = memory.get(field)
                context.metadata["updated_value"] = value
                context.metadata["storage"] = "localStorage"
                context.metadata["execution_time_ms"] = int((t1 - t0) * 1000)
                
                context.current_intent = "Memory (Update)"
                
                # Dynamic response
                response_text = ""
                if field == "user_name":
                    if "change" in text.lower() or "update" in text.lower():
                        response_text = f"Done! I'll remember your name as {value}."
                    elif "call me" in text.lower():
                        response_text = f"Sure! I'll call you {value} from now on."
                    else:
                        response_text = f"Nice to meet you, {value}! I'll remember your name."
                elif field == "assistant_name":
                    response_text = f"Sounds good! You can call me {value}."
                    
                return PipelineResult(
                    continue_pipeline=False,
                    stop=True,
                    intent="Memory (Update)",
                    response=response_text,
                    actions=[{"type": "UPDATE_MEMORY", "payload": {field: value, "preferred_name": value if field == "user_name" else memory.get("preferred_name")}}]
                )
                
        # Check LOOKUP
        for pattern, field in self.lookup_patterns:
            if re.search(pattern, text):
                t1 = time.perf_counter()
                val = memory.get(field)
                
                context.metadata["memory_intent"] = "LOOKUP"
                context.metadata["detected_field"] = field
                context.metadata["lookup_value"] = val
                context.metadata["storage"] = "localStorage"
                context.metadata["execution_time_ms"] = int((t1 - t0) * 1000)
                
                context.current_intent = "Memory (Lookup)"
                
                if field == "user_name":
                    if val:
                        response_text = f"Your name is {val}." if "what" in text.lower() else f"You're {val}."
                        if "what do you call me" in text.lower():
                            response_text = f"I call you {val}."
                    else:
                        response_text = "I don't know your name yet. What should I call you?"
                elif field == "assistant_name":
                    if val:
                        response_text = f"You can call me {val}."
                    else:
                        response_text = "I am Mobiloitte AI Assistant."
                        
                return PipelineResult(
                    continue_pipeline=False,
                    stop=True,
                    intent="Memory (Lookup)",
                    response=response_text
                )
                
        return PipelineResult(continue_pipeline=True)
