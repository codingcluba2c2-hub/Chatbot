from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult
from utils.detectors import detect_fastpath
from core.constants import INTENT_FASTPATH

class FastPathRouterStep(PipelineStep):
    def process(self, context: PipelineContext) -> PipelineResult:
        fastpath_key, phrase, conf, response = detect_fastpath(context.normalized_message)
        
        if fastpath_key:
            context.entities["intent"] = INTENT_FASTPATH
            context.entities["routed_topic"] = fastpath_key
            context.metadata["fastpath_routed"] = True
            context.metadata["fastpath_key"] = fastpath_key
            
            if fastpath_key.lower() == "who are you":
                memory = context.metadata.get("memory", {})
                assistant_name = memory.get("assistant_name")
                
                if assistant_name:
                    response = f"I'm {assistant_name}, your Enterprise AI Assistant for Mobiloitte."
                else:
                    response = "I am your Enterprise AI Assistant for Mobiloitte."
            
            # Check if query is significantly longer than the fastpath phrase (multi-intent)
            is_long_query = len(context.normalized_message.split()) > len(phrase.split()) + 3
            
            if is_long_query:
                context.metadata["fastpath_prefix"] = response
                return PipelineResult(
                    continue_pipeline=True,
                    stop=False,
                    metadata={"matched_key": fastpath_key, "phrase": phrase, "confidence": conf, "multi_intent": True}
                )
            else:
                greeting_prefix = context.metadata.get("greeting_prefix", "")
                if greeting_prefix:
                    response = f"{greeting_prefix}\n\n{response}"
                    
                # Stop the pipeline and return the exact configured response
                return PipelineResult(
                    continue_pipeline=False,
                    stop=True,
                    intent=INTENT_FASTPATH,
                    response=response,
                    metadata={"matched_key": fastpath_key, "phrase": phrase, "confidence": conf}
                )
            
        return PipelineResult(continue_pipeline=True)
