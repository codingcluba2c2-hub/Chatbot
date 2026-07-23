import logging
from chatbot.pipeline import PipelineStep, PipelineContext, PipelineResult
from chatbot.detector import detect_greeting, detect_faq, validate_query
import time

logger = logging.getLogger(__name__)

class IntentRouterStep(PipelineStep):
    """
    Enterprise Intent Router.
    Determines the minimum execution path for a query.
    """
    def process(self, context: PipelineContext) -> PipelineResult:
        query = context.normalized_message
        
        step_metadata = {}
        
        if context.current_intent == "ENTERPRISE_OVERVIEW":
            return PipelineResult(stop=False, metadata={"route": "ENTERPRISE_OVERVIEW", "router_metadata": {}})
            
        route = "RAG"
        
        # 1. Gibberish Check
        val_result = validate_query(query)
        if not val_result.get("isMeaningful", True):
            route = "Gibberish"
            step_metadata["reason"] = val_result.get("reason")
            return PipelineResult(stop=False, metadata={"route": route, "router_metadata": step_metadata})
            
        # 2. Greeting Check
        is_greet, greet_match, _, greet_resp, _ = detect_greeting(context.original_message)
        if is_greet:
            route = "Greeting"
            step_metadata["match"] = greet_match
            step_metadata["response"] = greet_resp
            return PipelineResult(stop=False, metadata={"route": route, "router_metadata": step_metadata})
            

        # 4. FAQ Check
        faq_matched, faq_match, faq_conf, _ = detect_faq(query)
        if faq_matched:
            route = "FAQ"
            step_metadata["match"] = faq_match
            return PipelineResult(stop=False, metadata={"route": route, "router_metadata": step_metadata})
            
        # 6. RAG Fallthrough
        route = "RAG"
        return PipelineResult(stop=False, metadata={"route": route, "router_metadata": step_metadata})
