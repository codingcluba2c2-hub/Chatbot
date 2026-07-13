import os

os.makedirs('backend/components', exist_ok=True)
os.makedirs('backend/workflows', exist_ok=True)
os.makedirs('frontend/src/components/sdui', exist_ok=True)

with open('backend/components/factory.py', 'w') as f:
    f.write('''\
from typing import List, Dict, Any

class ComponentBuilder:
    @staticmethod
    def quick_replies(items: List[str]) -> Dict[str, Any]:
        return {
            "type": "quickReplies",
            "items": items
        }

    @staticmethod
    def action_buttons(buttons: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        buttons = [{"text": "Apply Leave", "action": "leave_start"}]
        """
        return {
            "type": "buttons",
            "buttons": buttons
        }

    @staticmethod
    def form(fields: List[Dict[str, Any]], submit_action: str = "form_submit") -> Dict[str, Any]:
        """
        fields = [{"name": "leave_type", "type": "dropdown", "options": ["Sick", "Casual", "Earned"], "required": True}]
        """
        return {
            "type": "form",
            "fields": fields,
            "submit_action": submit_action
        }

    @staticmethod
    def card(title: str, description: str, subtitle: str = None, image_url: str = None, buttons: List[Dict[str, str]] = None) -> Dict[str, Any]:
        return {
            "type": "card",
            "title": title,
            "subtitle": subtitle,
            "description": description,
            "image_url": image_url,
            "buttons": buttons or []
        }
    
    @staticmethod
    def table(columns: List[str], rows: List[List[Any]]) -> Dict[str, Any]:
        return {
            "type": "table",
            "columns": columns,
            "rows": rows
        }

    @staticmethod
    def carousel(cards: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "type": "carousel",
            "items": cards
        }
''')

with open('backend/workflows/base.py', 'w') as f:
    f.write('''\
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult

class BaseWorkflow(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def handle(self, context: PipelineContext, current_state: Optional[str] = None) -> PipelineResult:
        """
        Process the workflow based on the current state.
        Returns a PipelineResult which might contain SDUI components.
        """
        pass
''')

with open('backend/workflows/engine.py', 'w') as f:
    f.write('''\
from typing import Dict, Optional, Any
from workflows.base import BaseWorkflow
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult
from services.conversation_memory_service import ConversationMemoryService
from core.logger import get_logger

logger = get_logger(__name__)

class WorkflowEngine:
    _workflows: Dict[str, BaseWorkflow] = {}

    @classmethod
    def register(cls, workflow: BaseWorkflow):
        cls._workflows[workflow.name] = workflow
        logger.info(f"Registered workflow: {workflow.name}")

    @classmethod
    def get_active_workflow(cls, session_id: str) -> Optional[Dict[str, Any]]:
        memory = ConversationMemoryService.get_memory(session_id)
        if memory and 'workflow' in memory.facts:
            return memory.facts['workflow']
        return None

    @classmethod
    def set_active_workflow(cls, session_id: str, workflow_name: str, state: str):
        ConversationMemoryService.add_fact(session_id, 'workflow', {
            'name': workflow_name,
            'state': state
        })
        
    @classmethod
    def clear_active_workflow(cls, session_id: str):
        ConversationMemoryService.add_fact(session_id, 'workflow', None)

    @classmethod
    def execute(cls, context: PipelineContext) -> Optional[PipelineResult]:
        active = cls.get_active_workflow(context.session_id)
        
        # Check if we should start a new workflow based on intent or fastpath
        intent = context.entities.get('intent')
        action = context.metadata.get('action') # passed if user clicked a button
        
        workflow_to_run = None
        current_state = None
        
        if active and active.get('name') in cls._workflows:
            workflow_to_run = active['name']
            current_state = active['state']
            
            # Allow user to cancel workflow
            msg = context.normalized_message.lower()
            if msg in ['cancel', 'stop', 'quit', 'exit']:
                cls.clear_active_workflow(context.session_id)
                return PipelineResult(
                    continue_pipeline=False,
                    stop=True,
                    intent="Workflow_Cancel",
                    response="Workflow cancelled. How else can I help?"
                )
                
        elif action and action.startswith('wf_'):
            # e.g., action: wf_leave_start
            parts = action.split('_')
            workflow_to_run = parts[1]
            current_state = "start" if len(parts) == 2 else parts[2]
            
        elif intent:
            # Maybe intent maps directly to a workflow
            mapping = {
                'leave': 'leave',
                'career': 'career',
                'ticket': 'ticket'
            }
            if intent.lower() in mapping:
                workflow_to_run = mapping[intent.lower()]
                current_state = 'start'

        if workflow_to_run and workflow_to_run in cls._workflows:
            workflow = cls._workflows[workflow_to_run]
            result = workflow.handle(context, current_state)
            
            # If the workflow finished, clear it. Otherwise, result.metadata should contain new state
            new_state = result.metadata.get('workflow_state')
            if new_state == 'completed':
                cls.clear_active_workflow(context.session_id)
            elif new_state:
                cls.set_active_workflow(context.session_id, workflow_to_run, new_state)
                
            return result
            
        return None
''')

