from chatbot.pipeline import PipelineStep, PipelineContext, PipelineResult
import time
from core.logger import get_logger

logger = get_logger(__name__)

# Enterprise vocabulary
KNOWN_ENTITIES = [
    "Product Designer", "AI Engineer", "Software Engineer", "Frontend Developer", 
    "Backend Developer", "Data Scientist", "Product Manager", "Project Manager",
    "Human Resources", "Finance", "Marketing", "Sales", "Support", "Engineering",
    "Office Timings", "Leave Policy", "Maternity Leave", "Paternity Leave",
    "Salary", "Bonus", "Stock Options", "Experience", "Skills", "Education"
]

# Alias mapping
ALIAS_DICT = {
    "sde": "Software Engineer",
    "swe": "Software Engineer",
    "fe": "Frontend Developer",
    "be": "Backend Developer",
    "pm": "Product Manager",
    "hr": "Human Resources",
    "ux designer": "Product Designer",
    "ui designer": "Product Designer",
    "ui/ux designer": "Product Designer",
    "ui ux designer": "Product Designer",
    "ux desginer": "Product Designer",
    "ui ux desginer": "Product Designer"
}

class SpellCorrectionStep(PipelineStep):
    def process(self, context: PipelineContext) -> PipelineResult:
        try:
            from rapidfuzz import process, fuzz
        except ImportError:
            return PipelineResult(continue_pipeline=True)
            
        t0 = time.perf_counter()
        
        msg = context.normalized_message
        
        result = process.extractOne(msg, KNOWN_ENTITIES, scorer=fuzz.WRatio)
        if result:
            match, score, _ = result
            # Only auto-correct if confidence is reasonably high, but not 100
            if 80 <= score < 100:
                context.metadata["spell_corrected"] = True
                context.metadata["original_query_before_spell"] = msg
                context.normalized_message = match
                
        context.metadata["spell_latency_ms"] = int((time.perf_counter() - t0) * 1000)
        return PipelineResult(continue_pipeline=True)

class AliasExpansionStep(PipelineStep):
    def process(self, context: PipelineContext) -> PipelineResult:
        t0 = time.perf_counter()
        
        msg_lower = context.normalized_message.lower().strip()
        
        if msg_lower in ALIAS_DICT:
            context.metadata["alias_expanded"] = True
            context.metadata["original_query_before_alias"] = context.normalized_message
            context.normalized_message = ALIAS_DICT[msg_lower]
            
        context.metadata["alias_latency_ms"] = int((time.perf_counter() - t0) * 1000)
        return PipelineResult(continue_pipeline=True)


class QueryRewriteStep(PipelineStep):
    def process(self, context: PipelineContext) -> PipelineResult:
        t0 = time.perf_counter()
        
        # We only rewrite if the query is short or needs context
        msg = context.normalized_message.strip()
        memory = context.metadata.get("conversation_memory", "")
        
        # If there's no memory or the message is already very long, skip rewriting
        if not memory or len(msg) > 100:
            context.metadata["rewritten_query"] = msg
            context.metadata["rewrite_latency_ms"] = int((time.perf_counter() - t0) * 1000)
            return PipelineResult(continue_pipeline=True)
            
        try:
            from services.llm_manager import get_llm_manager
            manager = get_llm_manager()
            
            system_prompt = (
                "You are an intelligent query rewriter for an enterprise search system.\n"
                "Your task is to convert the user's short or ambiguous query into a fully qualified standalone question using the provided conversation history.\n"
                "For example, if the history mentions 'Mobiloitte Technologies' and the user asks 'company about', rewrite it to 'Tell me about Mobiloitte Technologies.'\n"
                "Return ONLY the rewritten query. Do not add any conversational filler or quotes."
            )
            
            prompt = f"Conversation History:\n{memory}\n\nUser Query: {msg}\n\nRewritten Query:"
            
            result = manager.generate(prompt, system_prompt, {})
            rewritten = result.get("response", "").strip()
            
            # Clean up potential LLM artifacts
            if rewritten.startswith('"') and rewritten.endswith('"'):
                rewritten = rewritten[1:-1]
                
            if rewritten and len(rewritten) > 5:
                context.metadata["rewritten_query"] = rewritten
                context.normalized_message = rewritten
            else:
                context.metadata["rewritten_query"] = msg
                
        except Exception as e:
            logger.error(f"QueryRewriteStep failed: {e}")
            context.metadata["rewritten_query"] = msg
            
        context.metadata["rewrite_latency_ms"] = int((time.perf_counter() - t0) * 1000)
        return PipelineResult(continue_pipeline=True)
