# backend/steps/normalize_step.py
from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult
from utils.normalizer import normalize_text

class NormalizeStep(PipelineStep):
    def process(self, context: PipelineContext) -> PipelineResult:
        original = context.original_message.strip()
        
        # Check for slash commands
        if original.startswith("/"):
            command = original[1:].strip().split()[0].lower() # e.g. "/leave me" -> "leave"
            context.entities["intent"] = f"slash_{command}"
            
        normalized_text = normalize_text(original)
        context.normalized_message = normalized_text
        
        is_numeric = normalized_text.replace(" ", "").isdigit()
        context.is_numeric = is_numeric
        
        return PipelineResult(
            continue_pipeline=True,
            metadata={"normalized_text": normalized_text, "is_numeric": is_numeric}
        )
