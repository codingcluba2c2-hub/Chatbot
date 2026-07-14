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
            
            # Stop the pipeline and return the exact configured response
            return PipelineResult(
                continue_pipeline=False,
                stop=True,
                intent=INTENT_FASTPATH,
                response=response,
                metadata={"matched_key": fastpath_key, "phrase": phrase, "confidence": conf}
            )
            
        return PipelineResult(continue_pipeline=True)
