# backend/steps/fallback_step.py
from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult

class FallbackStep(PipelineStep):
    def process(self, context: PipelineContext) -> PipelineResult:
        # If the query is not meaningful, we let it fall through to GibberishStep
        if not context.metadata.get("is_meaningful", True):
            return PipelineResult(continue_pipeline=True)
            
        # If it reached here and it IS meaningful, it means FastPath, FAQ, and RAG didn't handle it.
        # It's a Fallback.
        return PipelineResult(
            stop=True,
            intent="Fallback",
            response="I don't have information about this in the current knowledge base.",
            metadata={"reason": "No match found in FastPath, FAQ, or Knowledge Base"}
        )
