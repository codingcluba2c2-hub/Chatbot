from tools.base import BaseTool, ToolContext, ToolResult
from core.logger import get_logger

logger = get_logger(__name__)

class ToolExecutor:
    @staticmethod
    def execute(tool: BaseTool, context: ToolContext) -> ToolResult:
        logger.info(f"Executing tool: {tool.name}")
        try:
            # Here we could add parameter validation, timeout, or permissions checks.
            result = tool.execute(context)
            return result
        except Exception as e:
            logger.error(f"Error executing tool {tool.name}: {str(e)}")
            return ToolResult(
                status="error",
                message=f"Failed to execute tool {tool.name}: {str(e)}"
            )
