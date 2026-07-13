from typing import Dict, Optional, List
from tools.base import BaseTool
from core.logger import get_logger

logger = get_logger(__name__)

class ToolRegistry:
    _tools: Dict[str, BaseTool] = {}
    _intent_mappings: Dict[str, str] = {}
    
    @classmethod
    def register(cls, tool: BaseTool, intents: List[str]):
        cls._tools[tool.name] = tool
        for intent in intents:
            cls._intent_mappings[intent.lower()] = tool.name
        logger.info(f"Registered tool: {tool.name}")

    @classmethod
    def get_tool(cls, name: str) -> Optional[BaseTool]:
        return cls._tools.get(name)

    @classmethod
    def get_tool_by_intent(cls, intent: str) -> Optional[BaseTool]:
        tool_name = cls._intent_mappings.get(intent.lower())
        if tool_name:
            return cls._tools.get(tool_name)
        return None
        
    @classmethod
    def list_tools(cls) -> List[BaseTool]:
        return list(cls._tools.values())
