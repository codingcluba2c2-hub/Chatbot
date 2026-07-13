# backend/steps/fastpath_step.py
from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult
from utils.detectors import detect_fastpath
from services.fastpath_service import FastPathService
from services.response_service import ResponseService
from core.constants import INTENT_FASTPATH

class FastPathStep(PipelineStep):
    def process(self, context: PipelineContext) -> PipelineResult:
        fastpath_key, phrase, conf = detect_fastpath(context.normalized_message)
        
        if fastpath_key:
            raw_response = FastPathService.get_response(fastpath_key)
            final_response = ResponseService.get_sequential_response(
                context.session_id,
                f"fastpath_{fastpath_key}",
                raw_response
            )
            return PipelineResult(
                stop=True,
                intent=INTENT_FASTPATH,
                response=final_response,
                metadata={"matched_key": fastpath_key, "phrase": phrase, "confidence": conf}
            )
            
        return PipelineResult(continue_pipeline=True)
