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
