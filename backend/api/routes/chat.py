# backend/api/routes/chat.py
from fastapi import APIRouter
from schemas.request import ChatRequest
from schemas.response import ChatResponse
from pipeline.pipeline_runner import PipelineRunner
from pipeline.pipeline_context import PipelineContext

from steps.normalize_step import NormalizeStep
from steps.followup_resolver_step import FollowUpResolverStep
from steps.greeting_step import GreetingFarewellStep
from steps.fastpath_router_step import FastPathRouterStep
from steps.faq_step import FAQStep
from steps.memory_step import MemoryDetectorStep
from steps.gibberish_step import GibberishStep
from steps.meaningful_validator_step import MeaningfulValidatorStep
from steps.spell_correction_step import SpellCorrectionStep
from steps.knowledge_search_step import KnowledgeSearchStep
from steps.knowledge_tree_step import KnowledgeTreeStep
from steps.response_generator_step import ResponseGeneratorStep

pipeline_runner = PipelineRunner()
pipeline_runner.register_step("Normalize", NormalizeStep())
pipeline_runner.register_step("FollowUpResolver", FollowUpResolverStep())
pipeline_runner.register_step("GreetingFarewell", GreetingFarewellStep())
pipeline_runner.register_step("KnowledgeTree", KnowledgeTreeStep())
pipeline_runner.register_step("FastPath", FastPathRouterStep())
pipeline_runner.register_step("FAQ", FAQStep())
pipeline_runner.register_step("Memory", MemoryDetectorStep())
pipeline_runner.register_step("Gibberish", GibberishStep())
pipeline_runner.register_step("MeaningfulValidator", MeaningfulValidatorStep())
pipeline_runner.register_step("SpellCorrection", SpellCorrectionStep())
pipeline_runner.register_step("KnowledgeSearch", KnowledgeSearchStep())
pipeline_runner.register_step("ResponseGenerator", ResponseGeneratorStep())

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
    
    if result.get("success") is False:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=500, content=result)
        
    return ChatResponse(
        intent=result["intent"],
        response=result["response"],
        components=result.get("components", []),
        actions=result.get("actions", []),
        trace=result.get("trace")
    )
