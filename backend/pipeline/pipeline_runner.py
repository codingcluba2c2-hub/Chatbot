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
        final_response = "I'm sorry, I didn't understand that."
        
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
            if hasattr(result, 'response') and result.response:
                final_response = result.response
                
            # If the step returned components or actions, we capture them
            # For simplicity, we just take the last step's components/actions if they exist
            if hasattr(result, 'components') and result.components:
                final_components = getattr(result, 'components', [])
            if hasattr(result, 'actions') and result.actions:
                final_actions = getattr(result, 'actions', [])
                
            if hasattr(result, 'stop') and result.stop:
                break
                
        total_time = (time.perf_counter() - total_start) * 1000
        
        trace = None
        if DEVELOPER_MODE:
            trace = {
                "steps": trace_steps,
                "totalBackendTimeMs": round(total_time, 3),
                "metadata": dict(context.metadata)
            }
        
        # Handle greeting prefix if it was a multi-intent query
        if "greeting_prefix" in context.metadata and final_intent != "Greeting":
            final_response = f"{context.metadata['greeting_prefix']} {final_response}"
        
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
