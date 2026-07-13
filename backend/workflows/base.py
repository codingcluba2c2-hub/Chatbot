from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult

class BaseWorkflow(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def handle(self, context: PipelineContext, current_state: Optional[str] = None) -> PipelineResult:
        """
        Process the workflow based on the current state.
        Returns a PipelineResult which might contain SDUI components.
        """
        pass
