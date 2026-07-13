from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult
from tools.router import ToolRouter

class ToolRouterStep(PipelineStep):
    def process(self, context: PipelineContext) -> PipelineResult:
        result = ToolRouter.route(context)
        if result and result.stop:
            return result
        return PipelineResult(continue_pipeline=True)
