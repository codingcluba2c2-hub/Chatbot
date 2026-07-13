# backend/steps/gibberish_step.py
from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult
from utils.detectors import is_gibberish
from services.gibberish_service import GibberishService
from core.constants import INTENT_GIBBERISH

class GibberishStep(PipelineStep):
    def process(self, context: PipelineContext) -> PipelineResult:
        if context.is_numeric:
            from utils.responses import NUMERIC_ONLY_MESSAGE
            return PipelineResult(
                stop=True,
                intent="Fallback",
                response=NUMERIC_ONLY_MESSAGE,
                metadata={"reason": "numeric_only"}
            )
            
        is_gib, rule, conf = is_gibberish(context.normalized_message)
        if is_gib:
            return PipelineResult(
                stop=True,
                intent=INTENT_GIBBERISH,
                response=GibberishService.get_response(),
                metadata={"rule": rule, "confidence": conf}
            )
            
        return PipelineResult(continue_pipeline=True)
