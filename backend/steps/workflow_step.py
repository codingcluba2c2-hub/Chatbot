from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult
from workflows.engine import WorkflowEngine

class WorkflowStep(PipelineStep):
    def process(self, context: PipelineContext) -> PipelineResult:
        result = WorkflowEngine.execute(context)
        if result:
            return result
        return PipelineResult(continue_pipeline=True)
