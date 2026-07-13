from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult

class ToolContext:
    def __init__(self, pipeline_context: PipelineContext, parameters: Dict[str, Any] = None):
        self.pipeline_context = pipeline_context
        self.parameters = parameters or {}
        
class ToolResult:
    def __init__(self, 
                 status: str, 
                 message: str, 
                 components: Optional[List[Dict[str, Any]]] = None,
                 actions: Optional[List[Dict[str, Any]]] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        self.status = status
        self.message = message
        self.components = components or []
        self.actions = actions or []
        self.metadata = metadata or {}

class BaseTool(ABC):
    def __init__(self, name: str, description: str, tool_type: str = "generic"):
        self.name = name
        self.description = description
        self.tool_type = tool_type

    @abstractmethod
    def execute(self, context: ToolContext) -> ToolResult:
        """
        Execute the tool with the given context.
        """
        pass
