import logging
from chatbot.pipeline import PipelineStep, PipelineContext, PipelineResult
from chatbot.state_manager import ConversationStateManager

logger = logging.getLogger(__name__)

class ConversationContextResolverStep(PipelineStep):
    """
    Enterprise Tri-Mode Context Resolver.
    """
    def process(self, context: PipelineContext) -> PipelineResult:
        message = context.normalized_message
        words = message.split()
        
        is_followup = context.metadata.get("is_followup", False)
        state = ConversationStateManager.get_state(context.session_id)
        current_entity = state.get("current_entity") if state else None
        
        step_metadata = {
            "Original Query": context.original_message,
            "Complete Query?": "NO",
            "Entity": current_entity or "None",
            "Heading": state.get("current_heading", "None") if state else "None",
            "Rewrite Needed?": "NO"
        }
        
        # MODE 1: Complete Query or New Topic
        # If it's not a followup, let the pipeline handle it normally (it might be a new topic like "Product Designer")
        if not is_followup:
            step_metadata["Complete Query?"] = "YES"
            formatted_metadata = "\n".join([f"{k}: {v}" for k, v in step_metadata.items()])
            context.metadata["ConversationContextResolver"] = formatted_metadata
            return PipelineResult(continue_pipeline=True, metadata={
                "ConversationContextResolver": formatted_metadata
            })
            
        # MODE 2: Incomplete Query (Needs Rewrite)
        if not current_entity:
            # We don't have an entity to anchor this followup to!
            clarification_msg = "Could you please specify which role or topic you're referring to?"
            context.metadata["FollowUpResolver"] = "Requested clarification."
            return PipelineResult(
                continue_pipeline=False,
                stop=True,
                intent="Clarification",
                response=clarification_msg
            )
            
        step_metadata["Rewrite Needed?"] = "YES"
        
        # Deterministic Rewrite
        rewritten_query = f"What is the {message.lower().strip()} of {current_entity}?"
        
        logger.info(f"ContextResolver deterministically rewrote '{message}' -> '{rewritten_query}' using entity '{current_entity}'")
        
        context.normalized_message = rewritten_query
        step_metadata["Rewritten Query"] = rewritten_query
        
        context.metadata["previous_entity"] = current_entity
        
        # Directly grab context from the state
        if state.get("retrieved_chunk_ids"):
            context.metadata["previous_retrieved_chunks"] = [{"id": cid} for cid in state.get("retrieved_chunk_ids", [])]
        if state.get("knowledge_node"):
            context.metadata["previous_knowledge_node"] = state.get("knowledge_node")
            
        # Format for frontend UI
        formatted_metadata = "\n".join([f"{k}: {v}" for k, v in step_metadata.items()])
        context.metadata["ConversationContextResolver"] = formatted_metadata
        context.metadata["rewritten_query"] = rewritten_query
            
        return PipelineResult(continue_pipeline=True, metadata={
            "ConversationContextResolver": formatted_metadata,
            "rewritten_query": rewritten_query
        })
