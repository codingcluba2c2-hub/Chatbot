import re
from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult

class SpellCorrectionStep(PipelineStep):
    def __init__(self):
        # A simple dictionary for common typos/normalized forms
        self.corrections = {
            r"\bprefered\b": "preferred",
            r"\byou name\b": "your name",
            r"\bhiii+\b": "hi",
            r"\bhelo\b": "hello",
            r"\bhelloo+\b": "hello",
            r"\bheyy+\b": "hey"
        }

    def process(self, context: PipelineContext) -> PipelineResult:
        text = context.normalized_message
        
        for pattern, replacement in self.corrections.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
            
        context.normalized_message = text
        return PipelineResult(continue_pipeline=True)
