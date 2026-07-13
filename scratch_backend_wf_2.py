import os

with open('backend/workflows/leave_workflow.py', 'w') as f:
    f.write('''\
from typing import Optional
from workflows.base import BaseWorkflow
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult
from components.factory import ComponentBuilder

class LeaveWorkflow(BaseWorkflow):
    def __init__(self):
        super().__init__("leave")

    def handle(self, context: PipelineContext, current_state: Optional[str] = None) -> PipelineResult:
        if current_state == "start":
            return PipelineResult(
                continue_pipeline=False,
                stop=True,
                intent="LeaveWorkflow",
                response="Please fill out your leave request details.",
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
            # In a real system, we'd extract form data from context and save to DB
            return PipelineResult(
                continue_pipeline=False,
                stop=True,
                intent="LeaveWorkflow",
                response="Your leave request has been submitted successfully.",
                components=[
                    ComponentBuilder.card(
                        title="Leave Request Submitted",
                        subtitle="Status: Pending Approval",
                        description="Your manager has been notified. You can track the status in your HR portal."
                    )
                ],
                metadata={"workflow_state": "completed"}
            )
            
        return PipelineResult(continue_pipeline=True)
''')

with open('backend/workflows/career_workflow.py', 'w') as f:
    f.write('''\
from typing import Optional
from workflows.base import BaseWorkflow
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult
from components.factory import ComponentBuilder

class CareerWorkflow(BaseWorkflow):
    def __init__(self):
        super().__init__("career")

    def handle(self, context: PipelineContext, current_state: Optional[str] = None) -> PipelineResult:
        if current_state == "start":
            return PipelineResult(
                continue_pipeline=False,
                stop=True,
                intent="CareerWorkflow",
                response="Please select the department you are interested in.",
                components=[
                    ComponentBuilder.quick_replies(["Engineering", "Sales", "Marketing", "HR"])
                ],
                metadata={"workflow_state": "awaiting_dept"}
            )
            
        elif current_state == "awaiting_dept":
            dept = context.original_message
            return PipelineResult(
                continue_pipeline=False,
                stop=True,
                intent="CareerWorkflow",
                response=f"Great! Here are the open roles in {dept}. Select one to apply.",
                components=[
                    ComponentBuilder.action_buttons([
                        {"text": f"Senior {dept} Manager", "action": "wf_career_role"},
                        {"text": f"{dept} Analyst", "action": "wf_career_role"}
                    ])
                ],
                metadata={"workflow_state": "awaiting_role"}
            )
            
        elif current_state == "role":
            return PipelineResult(
                continue_pipeline=False,
                stop=True,
                intent="CareerWorkflow",
                response="Please provide your contact details to complete the application.",
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
            return PipelineResult(
                continue_pipeline=False,
                stop=True,
                intent="CareerWorkflow",
                response="Your application has been received!",
                components=[
                    ComponentBuilder.card(
                        title="Application Successful",
                        subtitle="We will be in touch",
                        description="Thank you for applying. Our talent team will review your profile shortly."
                    )
                ],
                metadata={"workflow_state": "completed"}
            )
            
        return PipelineResult(continue_pipeline=True)
''')

with open('backend/workflows/ticket_workflow.py', 'w') as f:
    f.write('''\
from typing import Optional
from workflows.base import BaseWorkflow
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult
from components.factory import ComponentBuilder

class TicketWorkflow(BaseWorkflow):
    def __init__(self):
        super().__init__("ticket")

    def handle(self, context: PipelineContext, current_state: Optional[str] = None) -> PipelineResult:
        if current_state == "start":
            return PipelineResult(
                continue_pipeline=False,
                stop=True,
                intent="TicketWorkflow",
                response="I can help you raise a support ticket. What category does your issue fall under?",
                components=[
                    ComponentBuilder.quick_replies(["Hardware", "Software Access", "Network", "Other"])
                ],
                metadata={"workflow_state": "awaiting_category"}
            )
            
        elif current_state == "awaiting_category":
            category = context.original_message
            return PipelineResult(
                continue_pipeline=False,
                stop=True,
                intent="TicketWorkflow",
                response=f"Got it, category: {category}. Please describe your issue.",
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
            return PipelineResult(
                continue_pipeline=False,
                stop=True,
                intent="TicketWorkflow",
                response="Your ticket has been created.",
                components=[
                    ComponentBuilder.card(
                        title="Ticket #INC-9021",
                        subtitle="Status: Open",
                        description="IT Support has been notified and will resolve this within 24 hours."
                    )
                ],
                metadata={"workflow_state": "completed"}
            )
            
        return PipelineResult(continue_pipeline=True)
''')

with open('backend/steps/workflow_step.py', 'w') as f:
    f.write('''\
from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult
from workflows.engine import WorkflowEngine

class WorkflowStep(PipelineStep):
    def process(self, context: PipelineContext) -> PipelineResult:
        result = WorkflowEngine.execute(context)
        if result:
            return result
        return PipelineResult(continue_pipeline=True)
''')

