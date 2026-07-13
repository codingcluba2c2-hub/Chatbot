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
        if memory and 'active_tool' in memory.get('facts', {}):
            return memory['facts']['active_tool']
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
            current_state = memory.get('facts', {}).get('tool_state') if memory else None
            
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
