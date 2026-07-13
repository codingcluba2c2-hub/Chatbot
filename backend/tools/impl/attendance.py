from tools.base import BaseTool, ToolContext, ToolResult
from components.factory import ComponentBuilder
from datetime import datetime

class AttendanceTool(BaseTool):
    def __init__(self):
        super().__init__("AttendanceTool", "Checks the user's attendance records", tool_type="api")

    def execute(self, context: ToolContext) -> ToolResult:
        date = datetime.now().strftime("%Y-%m-%d")
        return ToolResult(
            status="success",
            message=f"Here is your attendance record for {date}.",
            components=[
                ComponentBuilder.table(
                    columns=["Date", "Status", "Check In", "Check Out"],
                    rows=[
                        [date, "Present", "09:00 AM", "06:00 PM"],
                        ["Yesterday", "Present", "09:15 AM", "06:05 PM"]
                    ]
                )
            ],
            metadata={"workflow_state": "completed"}
        )
