from tools.base import BaseTool, ToolContext, ToolResult
from components.factory import ComponentBuilder

class EmployeeSearchTool(BaseTool):
    def __init__(self):
        super().__init__("EmployeeSearchTool", "Searches for an employee in the directory", tool_type="database")

    def execute(self, context: ToolContext) -> ToolResult:
        current_state = context.parameters.get("state", "start")
        msg = context.pipeline_context.original_message
        
        if current_state == "start":
            # Very naive extraction for demo: If "search employee Rahul"
            if "search employee " in msg.lower():
                name = msg.lower().split("search employee ")[1].strip()
                return self._search(name)
            else:
                return ToolResult(
                    status="pending",
                    message="Which employee do you want to search for?",
                    metadata={"workflow_state": "awaiting_name"}
                )
                
        elif current_state == "awaiting_name":
            return self._search(msg)
            
        return ToolResult("error", "Invalid state")
        
    def _search(self, name: str) -> ToolResult:
        # Mock database search
        return ToolResult(
            status="success",
            message=f"Here is the profile for {name.title()}:",
            components=[
                ComponentBuilder.card(
                    title=name.title(),
                    subtitle="Software Engineer",
                    description=f"{name.title()} works in the Engineering department."
                )
            ],
            metadata={"workflow_state": "completed"}
        )
