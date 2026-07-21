from chatbot.pipeline import PipelineStep, PipelineStepResult, PipelineContext
"""
Purpose: Handle FAQs.
Responsibilities: Match and answer FAQs.
Flow: Executed before RAG.
"""

from chatbot.pipeline import PipelineContext
from chatbot.pipeline import PipelineResult
from chatbot.memory import ResponseService
from chatbot.utils import INTENT_FAQ

# backend/steps/faq_step.py

class FAQStep(PipelineStep):
    def process(self, context: PipelineContext) -> PipelineResult:
        from chatbot.detector import detect_faq
        is_faq, matched_question, conf, answer = detect_faq(context.normalized_message)
        
        if is_faq:
            final_response = ResponseService.get_sequential_response(
                context.session_id,
                f"faq_{matched_question}",
                [answer]
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


