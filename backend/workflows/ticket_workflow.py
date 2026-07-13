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
