# backend/steps/response_step.py
from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult
from services.response_service import ResponseService
from core.constants import INTENT_FALLBACK

class ResponseStep(PipelineStep):
    def process(self, context: PipelineContext) -> PipelineResult:
        # If we reach here, no previous step matched or stopped
        return PipelineResult(
            stop=True,
            intent=INTENT_FALLBACK,
            response=ResponseService.get_fallback(),
            metadata={"reason": "fallback"}
        )
