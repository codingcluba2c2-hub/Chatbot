import os
import shutil

os.makedirs('backend/tools', exist_ok=True)
os.makedirs('backend/tools/impl', exist_ok=True)

with open('backend/tools/base.py', 'w') as f:
    f.write('''\
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult

class ToolContext:
    def __init__(self, pipeline_context: PipelineContext, parameters: Dict[str, Any] = None):
        self.pipeline_context = pipeline_context
        self.parameters = parameters or {}
        
class ToolResult:
    def __init__(self, 
                 status: str, 
                 message: str, 
                 components: Optional[List[Dict[str, Any]]] = None,
                 actions: Optional[List[Dict[str, Any]]] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        self.status = status
        self.message = message
        self.components = components or []
        self.actions = actions or []
        self.metadata = metadata or {}

class BaseTool(ABC):
    def __init__(self, name: str, description: str, tool_type: str = "generic"):
        self.name = name
        self.description = description
        self.tool_type = tool_type

    @abstractmethod
    def execute(self, context: ToolContext) -> ToolResult:
        """
        Execute the tool with the given context.
        """
        pass
''')

with open('backend/tools/registry.py', 'w') as f:
    f.write('''\
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
''')

with open('backend/tools/executor.py', 'w') as f:
    f.write('''\
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
''')

with open('backend/tools/router.py', 'w') as f:
    f.write('''\
from typing import Optional
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult
from tools.registry import ToolRegistry
from tools.executor import ToolExecutor
from tools.base import ToolContext
from services.conversation_memory_service import ConversationMemoryService
from core.logger import get_logger

logger = get_logger(__name__)

class ToolRouter:
    @classmethod
    def get_active_tool(cls, session_id: str) -> Optional[str]:
        memory = ConversationMemoryService.get_memory(session_id)
        if memory and 'active_tool' in memory.facts:
            return memory.facts['active_tool']
        return None

    @classmethod
    def set_active_tool(cls, session_id: str, tool_name: str, state: str):
        ConversationMemoryService.add_fact(session_id, 'active_tool', tool_name)
        ConversationMemoryService.add_fact(session_id, 'tool_state', state)
        
    @classmethod
    def clear_active_tool(cls, session_id: str):
        ConversationMemoryService.add_fact(session_id, 'active_tool', None)
        ConversationMemoryService.add_fact(session_id, 'tool_state', None)

    @classmethod
    def route(cls, context: PipelineContext) -> PipelineResult:
        active_tool_name = cls.get_active_tool(context.session_id)
        intent = context.entities.get('intent')
        action = context.metadata.get('action') # E.g., wf_leave_start -> handled below
        
        # Determine which tool to run
        tool = None
        current_state = None
        
        if active_tool_name:
            tool = ToolRegistry.get_tool(active_tool_name)
            memory = ConversationMemoryService.get_memory(context.session_id)
            current_state = memory.facts.get('tool_state') if memory else None
            
            # Allow user to cancel
            msg = context.normalized_message.lower()
            if msg in ['cancel', 'stop', 'quit', 'exit']:
                cls.clear_active_tool(context.session_id)
                return PipelineResult(
                    continue_pipeline=False,
                    stop=True,
                    intent="Tool_Cancel",
                    response="Action cancelled. How else can I help?"
                )
                
        elif action and action.startswith('wf_'):
            # e.g., action: wf_leave_start
            parts = action.split('_')
            tool_name = parts[1]
            # Convert workflow action to tool intent mapped logic
            tool = ToolRegistry.get_tool_by_intent(tool_name)
            current_state = "start" if len(parts) == 2 else parts[2]
            
        elif intent:
            # Maybe intent maps directly to a tool (including slash commands)
            tool = ToolRegistry.get_tool_by_intent(intent)
            current_state = 'start'
            
            # Specifically handle slash command mappings from normalize step
            if not tool and intent.startswith("slash_"):
                tool = ToolRegistry.get_tool_by_intent(intent.replace("slash_", ""))
                current_state = 'start'

        if tool:
            tool_context = ToolContext(
                pipeline_context=context, 
                parameters={"state": current_state}
            )
            
            result = ToolExecutor.execute(tool, tool_context)
            
            # Manage state
            new_state = result.metadata.get('workflow_state')
            if new_state == 'completed':
                cls.clear_active_tool(context.session_id)
            elif new_state:
                cls.set_active_tool(context.session_id, tool.name, new_state)
                
            return PipelineResult(
                continue_pipeline=False,
                stop=True,
                intent=tool.name,
                response=result.message,
                components=result.components,
                actions=result.actions,
                metadata=result.metadata
            )
            
        return PipelineResult(continue_pipeline=True)
''')

with open('backend/tools/impl/workflow_tool.py', 'w') as f:
    f.write('''\
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
''')

with open('backend/tools/impl/employee_search.py', 'w') as f:
    f.write('''\
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
''')

with open('backend/tools/impl/attendance.py', 'w') as f:
    f.write('''\
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
''')

with open('backend/steps/tool_step.py', 'w') as f:
    f.write('''\
from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult
from tools.router import ToolRouter

class ToolRouterStep(PipelineStep):
    def process(self, context: PipelineContext) -> PipelineResult:
        result = ToolRouter.route(context)
        if result and result.stop:
            return result
        return PipelineResult(continue_pipeline=True)
''')
