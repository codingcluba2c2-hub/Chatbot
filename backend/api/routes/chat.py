# backend/api/routes/chat.py
from fastapi import APIRouter
from schemas.request import ChatRequest
from schemas.response import ChatResponse
from pipeline.pipeline_runner import PipelineRunner
from pipeline.pipeline_context import PipelineContext
from tools.registry import ToolRegistry
from tools.impl.workflow_tool import LeaveWorkflowTool, CareerWorkflowTool, TicketWorkflowTool
from tools.impl.employee_search import EmployeeSearchTool
from tools.impl.attendance import AttendanceTool

# Initialize and register tools
ToolRegistry.register(LeaveWorkflowTool(), intents=["leave", "slash_leave"])
ToolRegistry.register(CareerWorkflowTool(), intents=["career", "slash_career"])
ToolRegistry.register(TicketWorkflowTool(), intents=["ticket", "slash_ticket"])
ToolRegistry.register(EmployeeSearchTool(), intents=["employee_search", "slash_employee"])
ToolRegistry.register(AttendanceTool(), intents=["attendance", "slash_attendance"])

# Initialize pipeline steps
from steps.normalize_step import NormalizeStep
from steps.gibberish_step import GibberishStep
from steps.spell_correction_step import SpellCorrectionStep
from steps.greeting_step import GreetingStep
from steps.farewell_step import FarewellStep
from steps.fastpath_step import FastPathStep
from steps.faq_step import FAQStep
from steps.tool_step import ToolRouterStep
from steps.rag_step import RAGStep
from steps.memory_step import MemoryStep
from steps.response_step import ResponseStep

pipeline_runner = PipelineRunner()
pipeline_runner.register_step("Normalize", NormalizeStep())
pipeline_runner.register_step("Gibberish", GibberishStep())
pipeline_runner.register_step("SpellCorrection", SpellCorrectionStep())
pipeline_runner.register_step("Greeting", GreetingStep())
pipeline_runner.register_step("Farewell", FarewellStep())
pipeline_runner.register_step("FastPath", FastPathStep())
pipeline_runner.register_step("FAQ", FAQStep())
pipeline_runner.register_step("ToolRouter", ToolRouterStep())
pipeline_runner.register_step("RAG", RAGStep())
pipeline_runner.register_step("Memory", MemoryStep())
pipeline_runner.register_step("Response", ResponseStep())

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    context = PipelineContext(
        original_message=request.message,
        session_id=request.session_id,
        conversation_id=request.conversation_id
    )
    # Propagate metadata payload to context so workflows can read action/form data
    context.metadata.update(request.metadata)
    
    result = pipeline_runner.process(context)
    
    return ChatResponse(
        intent=result["intent"],
        response=result["response"],
        components=result.get("components", []),
        actions=result.get("actions", []),
        trace=result.get("trace")
    )
