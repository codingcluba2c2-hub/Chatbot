from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult
from utils.detectors import detect_farewell
from services.greeting_engine import GreetingEngine

class GreetingFarewellStep(PipelineStep):
    def __init__(self):
        super().__init__()
        self.greeting_engine = GreetingEngine()
        
    def process(self, context: PipelineContext) -> PipelineResult:
        # Check Greeting
        engine_result = self.greeting_engine.process(
            context.normalized_message, 
            context.session_id, 
            context.metadata.get("memory", {}).get("preferred_name") or context.metadata.get("memory", {}).get("user_name")
        )
        
        if engine_result.get("is_greeting"):
            context.metadata.update(engine_result["metadata"])
            context.metadata["greeting_detected"] = True
            context.metadata["greeting_prefix"] = engine_result["response"]
            
            remaining_query = engine_result["remaining_query"]
            
            if not remaining_query.strip():
                context.metadata["routing"] = "Greeting -> STOP"
                context.current_intent = "Greeting"
                return PipelineResult(
                    continue_pipeline=False, 
                    stop=True, 
                    intent="Greeting", 
                    response=engine_result["response"]
                )
            else:
                context.metadata["routing"] = "Greeting -> CONTINUE"
                context.metadata["remaining_query"] = remaining_query
                context.normalized_message = remaining_query
                # We do NOT stop. Let the pipeline continue.
                
        # Check Farewell
        is_farewell, matched_pattern, confidence, response, remaining_query = detect_farewell(context.normalized_message)
        
        if is_farewell:
            context.metadata["farewell_detected"] = True
            context.metadata["farewell_token"] = matched_pattern
            context.metadata["farewell_prefix"] = response
            
            if not remaining_query.strip():
                context.metadata["routing"] = "Farewell -> STOP"
                context.current_intent = "Farewell"
                return PipelineResult(
                    continue_pipeline=False, 
                    stop=True, 
                    intent="Farewell", 
                    response=response
                )
            else:
                context.metadata["routing"] = "Farewell -> CONTINUE"
                context.metadata["remaining_query"] = remaining_query
                context.normalized_message = remaining_query
        
        return PipelineResult(continue_pipeline=True)
