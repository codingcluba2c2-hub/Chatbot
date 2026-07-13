# backend/steps/spell_correction_step.py
from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult

class SpellCorrectionStep(PipelineStep):
    def process(self, context: PipelineContext) -> PipelineResult:
        return PipelineResult(continue_pipeline=True)
