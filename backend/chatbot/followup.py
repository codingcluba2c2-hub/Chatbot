from chatbot.pipeline import PipelineStep, PipelineContext, PipelineResult
import time

class FollowUpResolverStep(PipelineStep):
    def process(self, context: PipelineContext) -> PipelineResult:
        t0 = time.perf_counter()
        
        msg_lower = context.normalized_message.lower().strip()
        
        # Follow-up keyword triggers
        # If user just types these words, we automatically rewrite based on the active entity
        FOLLOWUP_TRIGGERS = [
            "salary", "experience", "education", "location", "skills", 
            "benefits", "responsibilities", "office timings", "leave policy", 
            "maternity leave", "paternity leave"
        ]
        
        memory_data = context.metadata.get("conversation_memory", {})
        last_entity = memory_data.get("last_retrieved_entity", "")
        
        # We also want to capture variations, e.g. "what is the salary", "salary details"
        is_trigger = False
        for trigger in FOLLOWUP_TRIGGERS:
            if trigger in msg_lower and len(msg_lower.split()) <= 4:
                is_trigger = True
                break
                
        if is_trigger and last_entity:
            # Deterministic Template Rewriting
            if "salary" in msg_lower:
                rewritten_query = f"What is the salary of {last_entity}?"
            elif "experience" in msg_lower:
                rewritten_query = f"What is the experience required for {last_entity}?"
            elif "education" in msg_lower:
                rewritten_query = f"What is the education required for {last_entity}?"
            elif "location" in msg_lower:
                rewritten_query = f"Where is the {last_entity} position located?"
            elif "office timings" in msg_lower or "saturday" in msg_lower:
                rewritten_query = f"What are the office timings for {last_entity}?"
                if "saturday" in msg_lower:
                    rewritten_query = "What are the Saturday office timings?"
            elif "maternity" in msg_lower or "leave" in msg_lower:
                rewritten_query = "What does the Leave Policy say about Maternity Leave?" if "maternity" in msg_lower else "What is the Leave Policy?"
            else:
                rewritten_query = f"What are the {msg_lower} details for {last_entity}?"
            
            context.metadata["original_query"] = context.normalized_message
            context.metadata["rewritten_query"] = rewritten_query
            context.metadata["rewrite_reason"] = "Deterministic Template Match"
            context.metadata["resolved_entity"] = last_entity
            
            context.normalized_message = rewritten_query
            context.metadata["is_followup"] = True
                    
        context.metadata["followup_latency_ms"] = int((time.perf_counter() - t0) * 1000)
        return PipelineResult(continue_pipeline=True)
