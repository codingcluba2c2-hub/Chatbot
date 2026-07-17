# backend/steps/faq_step.py
from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult
from utils.detectors import detect_faq
from services.response_service import ResponseService
from core.constants import INTENT_FAQ

class FAQStep(PipelineStep):
    def process(self, context: PipelineContext) -> PipelineResult:
        is_faq, matched_question, conf, answer = detect_faq(context.normalized_message)
        
        if is_faq:
            final_response = ResponseService.get_sequential_response(
                context.session_id,
                f"faq_{matched_question}",
                answer
            )
            greeting_prefix = context.metadata.get("greeting_prefix", "")
            if greeting_prefix:
                final_response = f"{greeting_prefix}\n\n{final_response}"
                
            return PipelineResult(
                stop=True,
                intent=INTENT_FAQ,
                response=final_response,
                metadata={"matched_question": matched_question, "confidence": conf}
            )
            
        return PipelineResult(continue_pipeline=True)
