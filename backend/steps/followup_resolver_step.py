# backend/steps/followup_resolver_step.py
from typing import Dict, Any, List
from .base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult
from services.conversation_memory_service import ConversationMemoryService
from services.followup_registry import followup_registry
from core.logger import get_logger

logger = get_logger(__name__)

class FollowUpResolverStep(PipelineStep):
    """
    Deterministically resolves short follow-up messages into full queries using session memory,
    without invoking an LLM.
    """
    def process(self, context: PipelineContext) -> PipelineResult:
        result = PipelineResult()
        
        normalized = context.normalized_message
        words = normalized.split()
        
        # 1. Check if it is a short or incomplete query
        if len(normalized) > 25 or len(words) > 3:
            result.metadata["followup_confidence"] = 0.0
            result.metadata["reason"] = "Query too long for strict deterministic follow-up"
            return result
            
        # Check registry
        keyword = words[0] if words else ""
        # Sometimes user says "my name" or "what salary", try last word too if first doesn't match
        pattern_data = followup_registry.get_pattern(keyword)
        if not pattern_data and len(words) > 1:
            keyword = words[-1]
            pattern_data = followup_registry.get_pattern(keyword)
            
        if not pattern_data:
            result.metadata["followup_confidence"] = 0.0
            result.metadata["reason"] = "No matching keyword pattern found"
            return result
            
        # 2. Fetch Structured Context Store
        global_ctx = ConversationMemoryService.get_context(context.session_id)
        
        # 3. Apply Rewrite Rules based on Context
        rewritten_query = None
        last_entity = None
        
        if keyword in ["name", "my name"]:
            if global_ctx.get("last_memory_operation"):
                rewritten_query = "What should you call me?"
            else:
                rewritten_query = "What is my name?"
                
        else:
            # Need an entity for other keywords
            entities = global_ctx.get("last_entities", [])
            if entities:
                last_entity = entities[-1]
                
            if not last_entity:
                result.metadata["followup_confidence"] = 0.3
                result.metadata["reason"] = "Missing last_entities in Context Store to resolve the rewrite."
                return result
                
            template = pattern_data["template"]
            rewritten_query = template.replace("{last_entity}", last_entity)
            
        confidence = 0.95
        
        # 6. Apply state updates
        context.normalized_message = rewritten_query
        
        result.metadata["rewritten_query"] = rewritten_query
        result.metadata["original_query"] = normalized
        result.metadata["followup_confidence"] = confidence
        result.metadata["last_entity"] = last_entity
        
        logger.info(f"FollowUpResolver applied: '{normalized}' -> '{rewritten_query}' (entity: {last_entity})")
        
        return result
