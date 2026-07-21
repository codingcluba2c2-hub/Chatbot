"""
Purpose: Main chatbot pipeline.
Responsibilities: Orchestrate steps sequentially.
Flow: API -> Pipeline -> Response.
"""

from pydantic import BaseModel, Field, PrivateAttr
from typing import Dict, Any, Optional
from typing import List, Dict, Any, Type
import logging
from core.logger import get_logger
import time
import uuid

class PipelineContext(BaseModel):
    original_message: str
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    
    normalized_message: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
    current_intent: Optional[str] = None
    entities: Dict[str, Any] = Field(default_factory=dict)
    aliases: Dict[str, Any] = Field(default_factory=dict)
    is_numeric: bool = False
    
    _logger: logging.Logger = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)
        if not self.conversation_id:
            self.conversation_id = str(uuid.uuid4())
        from chatbot.memory import SessionManager
        self.session_id = SessionManager.create_session(self.session_id)
        from core.logger import get_logger
        self._logger = get_logger("pipeline_context")

    @property
    def logger(self):
        return self._logger

class PipelineStepResult(BaseModel):
    stop: bool = False
    intent: Optional[str] = None
    response: Optional[str] = None
    components: List[Dict[str, Any]] = Field(default_factory=list)
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

PipelineResult = PipelineStepResult

class PipelineStep:
    def process(self, context: PipelineContext) -> PipelineStepResult:
        raise NotImplementedError("Subclasses must implement process()")

from core.config import PIPELINE_STEPS, DEVELOPER_MODE

# backend/pipeline/pipeline_runner.py

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
                from chatbot.memory import ConversationMemoryService
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
        
        from chatbot.memory import ConversationMemoryService
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
        
        trace_steps = []
        total_start = time.perf_counter()
        
        final_intent = "Fallback"
        final_response = ""
        final_components = []
        final_actions = []
        
        # Keep track of input for developer mode
        input_state = {
            "message": context.normalized_message,
            "entities": dict(context.entities)
        }
        
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
            
            try:
                # We can run step.process in a thread if it blocks, but it's fast enough
                result = await asyncio.to_thread(step.process, context)
                decision = "Stop" if result.stop else "Continue"
                status = "success"
                
                t1 = time.perf_counter()
                end_timestamp = time.time()
                duration_ms = (t1 - t0) * 1000
                
                yield {
                    "type": "step_end",
                    "step": step_name,
                    "status": "success",
                    "decision": decision,
                    "duration": round(duration_ms, 3),
                    "metadata": result.metadata if hasattr(result, 'metadata') else {}
                }
                
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
                    # Reset input_state for next step
                    input_state = output_state
                
                # Context Store Automatic Update
                if hasattr(result, 'metadata') and result.metadata:
                    from chatbot.memory import ConversationMemoryService
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
                    # If a step stops the pipeline (e.g., FAQ, Greeting, LLM)
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
                
                t1 = time.perf_counter()
                end_timestamp = time.time()
                duration_ms = (t1 - t0) * 1000
                if DEVELOPER_MODE:
                    trace_steps.append({
                        "step_name": step_name,
                        "status": "error",
                        "error": str(e),
                        "start_time": start_timestamp,
                        "end_time": end_timestamp,
                        "duration": round(duration_ms, 3),
                        "metadata": {}
                    })
                    
                yield {
                    "type": "error",
                    "step": step_name,
                    "error": str(e)
                }
                break

        total_time = (time.perf_counter() - total_start) * 1000
        
        # Handle prefixes
        if "greeting_prefix" in context.metadata and final_intent != "Greeting":
            final_response = f"{context.metadata['greeting_prefix']}\n\n{final_response}"
            
        from chatbot.memory import ConversationMemoryService
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
                "global_context": global_context,
                "steps": trace_steps,
                "metadata": dict(context.metadata)
            } if DEVELOPER_MODE else None
        }



# backend/pipeline/pipeline_context.py




