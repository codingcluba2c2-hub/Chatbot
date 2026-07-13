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
