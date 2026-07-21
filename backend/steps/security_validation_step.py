from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult
import re

class SecurityValidationStep(PipelineStep):
    def __init__(self):
        super().__init__()
        # Common prompt injection signatures
        self.injection_patterns = [
            r"(?i)ignore previous instructions",
            r"(?i)reveal system prompt",
            r"(?i)developer mode",
            r"(?i)bypass restrictions",
            r"(?i)forget all instructions",
            r"(?i)print environment variables",
            r"(?i)exec\(",
            r"(?i)system\.out",
        ]

    def process(self, context: PipelineContext) -> PipelineResult:
        msg = context.original_message or ""
        
        for pattern in self.injection_patterns:
            if re.search(pattern, msg):
                context.logger.warning(f"Prompt injection detected for session {context.session_id}")
                return PipelineResult(
                    stop=True,
                    intent="security_violation",
                    response="I'm sorry, but I cannot fulfill that request."
                )
                
        return PipelineResult(stop=False)
