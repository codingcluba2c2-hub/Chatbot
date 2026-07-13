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
