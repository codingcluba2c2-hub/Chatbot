# backend/steps/gibberish_step.py
from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult
from services.gibberish_service import GibberishService
from core.constants import INTENT_GIBBERISH

class GibberishStep(PipelineStep):
    def process(self, context: PipelineContext) -> PipelineResult:
        if not context.metadata.get("is_meaningful", True):
            suggestions = ["Overview", "Office Timings", "Leave Policy", "Contact", "Services", "Career", "Help"]
            
            from components.factory import ComponentBuilder
            
            # Use the fallback component for gibberish to maintain a premium enterprise feel
            fallback_component = ComponentBuilder.fallback(
                query=context.normalized_message, 
                suggestions=suggestions,
                prefix="That doesn't look like a valid message. I couldn't understand",
                suffix="Please try asking a clear question about one of the topics below."
            )
            
            # We can change the title specifically for gibberish
            fallback_component["title"] = "Invalid Message"

            return PipelineResult(
                continue_pipeline=False,
                stop=True,
                intent=INTENT_GIBBERISH,
                response="",
                components=[fallback_component],
                metadata={"reason": "Caught by GibberishStep"}
            )
            
        return PipelineResult(continue_pipeline=True)
