from chatbot.pipeline import PipelineStep, PipelineContext, PipelineResult
from chatbot.memory import ConversationMemoryService
from chatbot.llm import get_llm_provider
from core.logger import get_logger
import time
import json

logger = get_logger(__name__)

class FollowUpResolverStep(PipelineStep):
    def process(self, context: PipelineContext) -> PipelineResult:
        t0 = time.perf_counter()
        
        message = context.normalized_message
        words = message.split()
        
        DEPENDENT_KEYWORDS = {"salary", "experience", "skills", "education", "responsibilities", "location", "email", "benefits", "working hours", "joining process", "contact", "salary band", "package"}
        
        is_dependent = any(word in message.lower() for word in DEPENDENT_KEYWORDS)
        
        if is_dependent:
            context.metadata["is_followup"] = True
            
        return PipelineResult(continue_pipeline=True)
