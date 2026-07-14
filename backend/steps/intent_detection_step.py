from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult
from utils.detectors import detect_fastpath, detect_greeting, detect_farewell

class IntentDetectionStep(PipelineStep):
    def process(self, context: PipelineContext) -> PipelineResult:
        text = context.normalized_message
        
        # We classify intents explicitly here without stopping the pipeline
        if getattr(context, 'current_intent', None):
            return PipelineResult(continue_pipeline=True)
            
        is_greet, _, _, _ = detect_greeting(text)
        if is_greet:
            context.current_intent = "greeting"
            return PipelineResult(continue_pipeline=True)
            
        is_fw, _, _, _ = detect_farewell(text)
        if is_fw:
            context.current_intent = "farewell"
            return PipelineResult(continue_pipeline=True)
            
        fastpath_key, _, _, _ = detect_fastpath(text)
        if fastpath_key:
            context.current_intent = "fastpath"
            return PipelineResult(continue_pipeline=True)
            
        context.current_intent = "knowledge_search"
        return PipelineResult(continue_pipeline=True)
