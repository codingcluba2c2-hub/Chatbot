# backend/steps/base_step.py
from abc import ABC, abstractmethod
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult

class PipelineStep(ABC):
    @abstractmethod
    def process(self, context: PipelineContext) -> PipelineResult:
        """Processes the context and returns a PipelineResult."""
        pass
