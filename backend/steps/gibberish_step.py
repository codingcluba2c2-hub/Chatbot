# backend/steps/gibberish_step.py
from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult
from services.gibberish_service import GibberishService
from core.constants import INTENT_GIBBERISH

class GibberishStep(PipelineStep):
    def process(self, context: PipelineContext) -> PipelineResult:
        if not context.metadata.get("is_meaningful", True):
            return PipelineResult(
                stop=True,
                intent=INTENT_GIBBERISH,
                response=GibberishService.get_response(),
                metadata={"reason": "Caught by GibberishStep at the end of pipeline"}
            )
            
        return PipelineResult(continue_pipeline=True)
