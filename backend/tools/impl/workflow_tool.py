from typing import Optional
from tools.base import BaseTool, ToolContext, ToolResult
from components.factory import ComponentBuilder

class WorkflowTool(BaseTool):
    """
    Abstract base for workflow-based tools that manage conversational multi-step forms.
    """
    def __init__(self, name: str, description: str):
        super().__init__(name, description, tool_type="workflow")

class LeaveWorkflowTool(WorkflowTool):
    def __init__(self):
        super().__init__("LeaveTool", "Manages leave applications")

    def execute(self, context: ToolContext) -> ToolResult:
        current_state = context.parameters.get("state", "start")
        if current_state == "start":
            return ToolResult(
                status="pending",
                message="Please fill out your leave request details.",
                components=[
                    ComponentBuilder.form(
                        fields=[
                            {"name": "leave_type", "type": "dropdown", "label": "Leave Type", "options": ["Sick", "Casual", "Earned"], "required": True},
                            {"name": "start_date", "type": "date", "label": "Start Date", "required": True},
                            {"name": "end_date", "type": "date", "label": "End Date", "required": True},
                            {"name": "reason", "type": "textarea", "label": "Reason", "required": True}
                        ],
                        submit_action="wf_leave_submit"
                    )
                ],
                metadata={"workflow_state": "awaiting_form"}
            )
        elif current_state == "submit":
            return ToolResult(
                status="success",
                message="Your leave request has been submitted successfully.",
                components=[
                    ComponentBuilder.card(
                        title="Leave Request Submitted",
                        subtitle="Status: Pending Approval",
                        description="Your manager has been notified. You can track the status in your HR portal."
                    )
                ],
                metadata={"workflow_state": "completed"}
            )
        return ToolResult("error", "Invalid state")

class CareerWorkflowTool(WorkflowTool):
    def __init__(self):
        super().__init__("CareerTool", "Handles internal job applications")

    def execute(self, context: ToolContext) -> ToolResult:
        current_state = context.parameters.get("state", "start")
        msg = context.pipeline_context.original_message
        
        if current_state == "start":
            return ToolResult(
                status="pending",
                message="Please select the department you are interested in.",
                components=[ComponentBuilder.quick_replies(["Engineering", "Sales", "Marketing", "HR"])],
                metadata={"workflow_state": "awaiting_dept"}
            )
        elif current_state == "awaiting_dept":
            return ToolResult(
                status="pending",
                message=f"Great! Here are the open roles in {msg}. Select one to apply.",
                components=[
                    ComponentBuilder.action_buttons([
                        {"text": f"Senior {msg} Manager", "action": "wf_career_role"},
                        {"text": f"{msg} Analyst", "action": "wf_career_role"}
                    ])
                ],
                metadata={"workflow_state": "awaiting_role"}
            )
        elif current_state == "role":
            return ToolResult(
                status="pending",
                message="Please provide your contact details to complete the application.",
                components=[
                    ComponentBuilder.form(
                        fields=[
                            {"name": "email", "type": "email", "label": "Email Address", "required": True},
                            {"name": "phone", "type": "text", "label": "Phone Number", "required": True},
                            {"name": "resume", "type": "text", "label": "LinkedIn Profile URL", "required": True}
                        ],
                        submit_action="wf_career_submit"
                    )
                ],
                metadata={"workflow_state": "awaiting_form"}
            )
        elif current_state == "submit":
            return ToolResult(
                status="success",
                message="Your application has been received!",
                components=[
                    ComponentBuilder.card(
                        title="Application Successful",
                        subtitle="We will be in touch",
                        description="Thank you for applying. Our talent team will review your profile shortly."
                    )
                ],
                metadata={"workflow_state": "completed"}
            )
        return ToolResult("error", "Invalid state")

class TicketWorkflowTool(WorkflowTool):
    def __init__(self):
        super().__init__("TicketTool", "Helps raise IT support tickets")

    def execute(self, context: ToolContext) -> ToolResult:
        current_state = context.parameters.get("state", "start")
        msg = context.pipeline_context.original_message
        
        if current_state == "start":
            return ToolResult(
                status="pending",
                message="I can help you raise a support ticket. What category does your issue fall under?",
                components=[ComponentBuilder.quick_replies(["Hardware", "Software Access", "Network", "Other"])],
                metadata={"workflow_state": "awaiting_category"}
            )
        elif current_state == "awaiting_category":
            return ToolResult(
                status="pending",
                message=f"Got it, category: {msg}. Please describe your issue.",
                components=[
                    ComponentBuilder.form(
                        fields=[
                            {"name": "priority", "type": "dropdown", "label": "Priority", "options": ["Low", "Medium", "High"], "required": True},
                            {"name": "description", "type": "textarea", "label": "Description", "required": True}
                        ],
                        submit_action="wf_ticket_submit"
                    )
                ],
                metadata={"workflow_state": "awaiting_details"}
            )
        elif current_state == "submit":
            return ToolResult(
                status="success",
                message="Your ticket has been created.",
                components=[
                    ComponentBuilder.card(
                        title="Ticket #INC-9021",
                        subtitle="Status: Open",
                        description="IT Support has been notified and will resolve this within 24 hours."
                    )
                ],
                metadata={"workflow_state": "completed"}
            )
        return ToolResult("error", "Invalid state")
