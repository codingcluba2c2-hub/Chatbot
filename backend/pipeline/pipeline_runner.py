# backend/pipeline/pipeline_runner.py
import time
from typing import List, Dict, Any, Type
from core.logger import get_logger
from core.config import PIPELINE_STEPS, DEVELOPER_MODE
from pipeline.pipeline_context import PipelineContext
from steps.base_step import PipelineStep

logger = get_logger(__name__)

class PipelineRunner:
    def __init__(self):
        self.steps: Dict[str, PipelineStep] = {}

    def register_step(self, name: str, step: PipelineStep):
        self.steps[name] = step

    def process(self, context: PipelineContext) -> Dict[str, Any]:
        trace_steps: List[Dict[str, Any]] = []
        total_start = time.perf_counter()
        
        final_intent = "Fallback"
        final_response = ""
        
        for step_name in PIPELINE_STEPS:
            if step_name not in self.steps:
                logger.warning(f"Step '{step_name}' is configured but not registered. Skipping.")
                continue
                
            step = self.steps[step_name]
            
            t0 = time.perf_counter()
            start_timestamp = time.time()
            logger.info(f"Started step: {step_name}")
            
            # Capture state before step
            input_state = {
                "message": context.normalized_message,
                "entities": dict(context.entities)
            }
            
            status = "success"
            decision = "Continue"
            
            try:
                result = step.process(context)
                if result.stop:
                    decision = "Stop"
            except Exception as e:
                import traceback
                logger.error(f"Error in step '{step_name}': {e}")
                logger.error(traceback.format_exc())
                return {
                    "success": False,
                    "step": step_name,
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                    "developer_message": f"Step '{step_name}' crashed during execution.",
                    "user_message": "Internal server error."
                }
                
            t1 = time.perf_counter()
            end_timestamp = time.time()
            duration_ms = (t1 - t0) * 1000
            
            # Capture state after step
            output_state = {
                "message": context.normalized_message,
                "entities": dict(context.entities)
            }
            
            if DEVELOPER_MODE:
                trace_steps.append({
                    "step_name": step_name,
                    "status": status,
                    "start_time": start_timestamp,
                    "end_time": end_timestamp,
                    "duration": round(duration_ms, 3),
                    "input": input_state,
                    "output": output_state,
                    "decision": decision,
                    "metadata": result.metadata if hasattr(result, 'metadata') else {}
                })
            
            logger.info(f"Finished step: {step_name} - Execution Time: {duration_ms:.2f} ms - Decision: {decision}")
            
            if hasattr(result, 'intent') and result.intent:
                final_intent = result.intent
            if hasattr(result, 'response') and result.response is not None:
                final_response = result.response
                
            # Context Store Automatic Update
            if hasattr(result, 'metadata') and result.metadata:
                from services.conversation_memory_service import ConversationMemoryService
                context_updates = {}
                if "memory_intent" in result.metadata:
                    context_updates["last_memory_operation"] = f"{result.metadata['memory_intent']}_{result.metadata.get('detected_field', 'unknown')}"
                if "topic" in result.metadata:
                    context_updates["current_topic"] = result.metadata["topic"]
                if "knowledge_node" in result.metadata:
                    context_updates["last_knowledge_node"] = result.metadata["knowledge_node"]
                
                if context_updates:
                    ConversationMemoryService.update_context(context.session_id, context_updates)
                    
            # If the step returned components or actions, we capture them
            # For simplicity, we just take the last step's components/actions if they exist
            if hasattr(result, 'components') and result.components:
                final_components = getattr(result, 'components', [])
            if hasattr(result, 'actions') and result.actions:
                final_actions = getattr(result, 'actions', [])
                
            if hasattr(result, 'stop') and result.stop:
                break
                
        total_time = (time.perf_counter() - total_start) * 1000
        
        from services.conversation_memory_service import ConversationMemoryService
        context_updates = {
            "last_intent": final_intent
        }
        if context.entities:
            context_updates["last_entities"] = list(context.entities.values())
            
        ConversationMemoryService.update_context(context.session_id, context_updates)
        
        trace = None
        if DEVELOPER_MODE:
            trace = {
                "steps": trace_steps,
                "totalBackendTimeMs": round(total_time, 3),
                "metadata": dict(context.metadata),
                "global_context": ConversationMemoryService.get_context(context.session_id)
            }
        
        # Handle fastpath prefix if it was a multi-intent query
        if "fastpath_prefix" in context.metadata and final_intent != "FastPath":
            final_response = f"{context.metadata['fastpath_prefix']}\n\n{final_response}"
        
        response_obj = {
            "success": True,
            "intent": final_intent,
            "response": final_response,
            "components": locals().get('final_components', []),
            "actions": locals().get('final_actions', []),
            "session_id": context.session_id
        }
        
        if DEVELOPER_MODE:
            response_obj["trace"] = trace
            
        return response_obj

    async def process_stream(self, context: PipelineContext):
        """
        Asynchronous generator that yields live pipeline events and streaming LLM tokens.
        """
        import asyncio
        from agents.orchestrator import AgentOrchestrator
        
        trace_steps = []
        total_start = time.perf_counter()
        
        final_intent = "Fallback"
        final_response = ""
        final_components = []
        final_actions = []
        
        for step_name in PIPELINE_STEPS:
            if step_name not in self.steps:
                continue
                
            step = self.steps[step_name]
            
            t0 = time.perf_counter()
            start_timestamp = time.time()
            
            # Notify frontend that step started
            yield {"type": "step_start", "step": step_name, "start_time": start_timestamp}
            
            # Let the event loop breathe to flush the websocket message
            await asyncio.sleep(0.01)
            
            # Special case for LLM generation to use Agno Agent
            if step_name == "ResponseGenerator":
                retrieved = context.metadata.get("rag_chunks", [])
                context_str = "\n".join([c.get("payload", {}).get("content", c.get("text", "")) for c in retrieved])
                
                orchestrator = AgentOrchestrator()
                # Run the orchestrator generator (it is currently a sync generator, so we iterate)
                # In a heavy prod environment this could block, but for our scale, direct iteration is fine
                response_chunks = []
                for chunk in orchestrator.stream_response(context, context_str):
                    response_chunks.append(chunk["chunk"])
                    yield chunk
                    await asyncio.sleep(0.01)
                    
                final_response = "".join(response_chunks)
                final_intent = "Knowledge" if retrieved else "Fallback"
                
                # yield step end for ResponseGenerator
                t1 = time.perf_counter()
                yield {
                    "type": "step_end", 
                    "step": step_name,
                    "status": "success",
                    "duration": round((t1 - t0) * 1000, 3),
                    "metadata": context.metadata
                }
                break

            # Execute normal step synchronously
            try:
                # We can run step.process in a thread if it blocks, but it's fast enough
                result = await asyncio.to_thread(step.process, context)
                decision = "Stop" if result.stop else "Continue"
                
                t1 = time.perf_counter()
                
                yield {
                    "type": "step_end",
                    "step": step_name,
                    "status": "success",
                    "decision": decision,
                    "duration": round((t1 - t0) * 1000, 3),
                    "metadata": result.metadata if hasattr(result, 'metadata') else {}
                }
                
                # Context Store Automatic Update
                if hasattr(result, 'metadata') and result.metadata:
                    from services.conversation_memory_service import ConversationMemoryService
                    context_updates = {}
                    
                    if "memory_intent" in result.metadata:
                        context_updates["last_memory_operation"] = f"{result.metadata['memory_intent']}_{result.metadata.get('detected_field', 'unknown')}"
                    if "topic" in result.metadata:
                        context_updates["current_topic"] = result.metadata["topic"]
                    if "knowledge_node" in result.metadata:
                        context_updates["last_knowledge_node"] = result.metadata["knowledge_node"]
                    
                    if context_updates:
                        await asyncio.to_thread(ConversationMemoryService.update_context, context.session_id, context_updates)
                        
                if hasattr(result, 'intent') and result.intent:
                    final_intent = result.intent
                if hasattr(result, 'response') and result.response is not None:
                    final_response = result.response
                if hasattr(result, 'components') and result.components:
                    final_components = getattr(result, 'components', [])
                if hasattr(result, 'actions') and result.actions:
                    final_actions = getattr(result, 'actions', [])
                    
                if result.stop:
                    # If a non-LLM step stops the pipeline (e.g., FAQ, Greeting)
                    # we stream its response artificially
                    if final_response:
                        # Fake streaming for UX
                        for word in final_response.split(" "):
                            yield {"type": "stream", "chunk": word + " "}
                            await asyncio.sleep(0.02)
                    break
                    
            except Exception as e:
                import traceback
                logger.error(f"Error in step '{step_name}': {e}")
                yield {
                    "type": "error",
                    "step": step_name,
                    "error": str(e)
                }
                break

        total_time = (time.perf_counter() - total_start) * 1000
        
        # Handle prefixes
        if "greeting_prefix" in context.metadata and final_intent != "Greeting":
            final_response = f"{context.metadata['greeting_prefix']} {final_response}"
            
        from services.conversation_memory_service import ConversationMemoryService
        context_updates = {
            "last_intent": final_intent
        }
        if context.entities:
            context_updates["last_entities"] = list(context.entities.values())
            
        await asyncio.to_thread(ConversationMemoryService.update_context, context.session_id, context_updates)
        
        global_context = await asyncio.to_thread(ConversationMemoryService.get_context, context.session_id)
            
        yield {
            "type": "done",
            "intent": final_intent,
            "response": final_response,
            "components": final_components,
            "actions": final_actions,
            "trace": {
                "totalBackendTimeMs": round(total_time, 3),
                "global_context": global_context
            }
        }

