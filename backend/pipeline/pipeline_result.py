# backend/pipeline/pipeline_result.py
from typing import Dict, Any, Optional, List

class PipelineResult:
    def __init__(
        self,
        continue_pipeline: bool = True,
        stop: bool = False,
        intent: Optional[str] = None,
        response: Optional[str] = None,
        components: Optional[List[Dict[str, Any]]] = None,
        actions: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.continue_pipeline = continue_pipeline
        self.stop = stop
        self.intent = intent
        self.response = response
        self.components = components or []
        self.actions = actions or []
        self.metadata = metadata or {}
