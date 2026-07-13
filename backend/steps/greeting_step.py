# backend/steps/greeting_step.py
from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult
from utils.detectors import detect_greeting
from services.response_service import ResponseService
from core.constants import INTENT_GREETING

class GreetingStep(PipelineStep):
    def process(self, context: PipelineContext) -> PipelineResult:
        has_greeting, pattern, conf, response = detect_greeting(context.normalized_message)
        
        if has_greeting:
            final_response = ResponseService.get_sequential_response(
                context.session_id, 
                f"greeting_{pattern}", 
                response or "Hello! How can I assist you?"
            )
            return PipelineResult(
                stop=True,
                intent=INTENT_GREETING,
                response=final_response,
                metadata={"pattern": pattern, "confidence": conf}
            )
            
        return PipelineResult(continue_pipeline=True)
