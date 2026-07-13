# backend/steps/farewell_step.py
from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult
from utils.detectors import detect_farewell
from services.response_service import ResponseService
from core.constants import INTENT_FAREWELL

class FarewellStep(PipelineStep):
    def process(self, context: PipelineContext) -> PipelineResult:
        has_farewell, pattern, conf, response = detect_farewell(context.normalized_message)
        
        if has_farewell:
            final_response = ResponseService.get_sequential_response(
                context.session_id, 
                f"farewell_{pattern}", 
                response or "Goodbye! 👋 Have a wonderful day!"
            )
            return PipelineResult(
                stop=True,
                intent=INTENT_FAREWELL,
                response=final_response,
                metadata={"pattern": pattern, "confidence": conf}
            )
            
        return PipelineResult(continue_pipeline=True)
