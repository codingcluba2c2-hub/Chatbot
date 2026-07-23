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
        is_faq, matched_question, conf, faq_obj = detect_faq(context.normalized_message)
        
        if is_faq and faq_obj:
            from chatbot.in_memory_engine import engine
            answer = getattr(faq_obj, "answer", "") or ""
            
            # Record sequential response
            final_response = ResponseService.get_sequential_response(
                context.session_id,
                f"faq_{matched_question}",
                answer
            )
            
            greeting_prefix = context.metadata.get("greeting_prefix", "")
            if greeting_prefix:
                final_response = f"{greeting_prefix}\n\n{final_response}"
                
            # Handle children
            components = []
            children = engine.faq_children_map.get(faq_obj.id, [])
            
            if children:
                quick_reply_items = [getattr(c, "title", "") for c in children if getattr(c, "title", "")]
                components.append({
                    "type": "quickReplies",
                    "items": quick_reply_items
                })

            return PipelineResult(
                stop=True,
                intent=INTENT_FAQ,
                response=final_response,
                components=components,
                metadata={"matched_question": matched_question, "confidence": conf, "faq_id": faq_obj.id}
            )
            
        return PipelineResult(continue_pipeline=True)


