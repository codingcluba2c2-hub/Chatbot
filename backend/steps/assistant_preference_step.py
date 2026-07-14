import re
from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult

class AssistantPreferenceStep(PipelineStep):
    def __init__(self):
        # Patterns for setting assistant name
        self.preference_patterns = [
            re.compile(r"call yourself\s+([a-zA-Z]+)", re.IGNORECASE),
            re.compile(r"your name is\s+([a-zA-Z]+)", re.IGNORECASE),
            re.compile(r"i prefer your name\s+([a-zA-Z]+)", re.IGNORECASE),
            re.compile(r"i prefer to call you\s+([a-zA-Z]+)", re.IGNORECASE),
            re.compile(r"can i call you\s+([a-zA-Z]+)", re.IGNORECASE),
            re.compile(r"i['’]?ll call you\s+([a-zA-Z]+)", re.IGNORECASE),
            re.compile(r"rename yourself\s+([a-zA-Z]+)", re.IGNORECASE),
            re.compile(r"(?:from now on )?your name is\s+([a-zA-Z]+)", re.IGNORECASE),
            re.compile(r"i want to call you\s+([a-zA-Z]+)", re.IGNORECASE),
            re.compile(r"you are\s+([a-zA-Z]+)", re.IGNORECASE),
            re.compile(r"you should be called\s+([a-zA-Z]+)", re.IGNORECASE),
            re.compile(r"my preferred name for you is\s+([a-zA-Z]+)", re.IGNORECASE)
        ]

    def process(self, context: PipelineContext) -> PipelineResult:
        text = context.normalized_message.strip()
        
        for pattern in self.preference_patterns:
            match = pattern.search(text)
            if match:
                extracted_name = match.group(1).capitalize()
                
                actions = [{
                    "type": "UPDATE_MEMORY",
                    "payload": {
                        "assistant_name": extracted_name
                    }
                }]
                
                context.metadata["Memory Updated"] = True
                context.metadata["Assistant Name Updated"] = extracted_name
                context.metadata["Storage"] = "localStorage"
                
                response = f"Got it! 😊 You can call me {extracted_name} from now on. I'll remember that as your preferred name."
                
                return PipelineResult(
                    stop=True,
                    intent="AssistantPreference",
                    response=response,
                    actions=actions
                )
                
        return PipelineResult(continue_pipeline=True)
