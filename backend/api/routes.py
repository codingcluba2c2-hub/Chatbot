"""
Purpose: Main API routes.
Responsibilities: Chat and health endpoints.
Flow: Entrypoint.
"""

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from chatbot.pipeline import PipelineContext
from chatbot.pipeline import PipelineRunner
from sqlalchemy import text
from typing import Dict, List
import asyncio
import json
from core.logger import get_logger
from chatbot.utils import limiter

from chatbot.detector import GibberishStep, NormalizeStep
from chatbot.followup import FollowUpResolverStep
from chatbot.context_resolver import ConversationContextResolverStep
from chatbot.abuse import AbuseDetectionStep
from chatbot.greeting import GreetingStep
from chatbot.faq import FAQStep
from core.schemas import ChatResponse
from chatbot.fast_pipeline import run_fast_pipeline

# backend/api/routes/chat.py


pipeline_runner = PipelineRunner()
pipeline_runner.register_step("Normalize", NormalizeStep())
from chatbot.nlp_steps import SpellCorrectionStep, AliasExpansionStep, QueryRewriteStep
pipeline_runner.register_step("SpellCorrectionStep", SpellCorrectionStep())
pipeline_runner.register_step("AliasExpansionStep", AliasExpansionStep())
pipeline_runner.register_step("QueryRewriteStep", QueryRewriteStep())
from chatbot.pipeline import ResponseCacheStep
pipeline_runner.register_step("ResponseCacheStep", ResponseCacheStep())
from chatbot.memory import ConversationMemoryStep
pipeline_runner.register_step("ConversationMemoryStep", ConversationMemoryStep())
pipeline_runner.register_step("FollowUpResolverStep", FollowUpResolverStep())
from chatbot.router import IntentRouterStep
pipeline_runner.register_step("IntentRouterStep", IntentRouterStep())
pipeline_runner.register_step("Greeting", GreetingStep())
pipeline_runner.register_step("Gibberish", GibberishStep())
pipeline_runner.register_step("AbuseDetection", AbuseDetectionStep())
pipeline_runner.register_step("FAQ", FAQStep())
from chatbot.rag import KnowledgeSearchStep, ResponseGeneratorStep
pipeline_runner.register_step("KnowledgeSearchStep", KnowledgeSearchStep())
pipeline_runner.register_step("ResponseGeneratorStep", ResponseGeneratorStep())


router = APIRouter()

@router.on_event("startup")
async def startup_event():
    logger.info("UltraFastEngine API routes initialized.")

@router.post("/chat")
# @limiter.limit("10/minute")
async def chat_endpoint(request: Request):
    req_data = await request.json()
    message = req_data.get("message", "")
    session_id = req_data.get("session_id", "default")
    metadata = req_data.get("metadata", {})
    
    fast_result = run_fast_pipeline(message, session_id, metadata)
    if fast_result.get("success"):
        from fastapi.responses import JSONResponse
        return JSONResponse(content=fast_result)
        
    context = PipelineContext(
        original_message=message,
        session_id=session_id,
        conversation_id=req_data.get("conversation_id", "default")
    )
    context.metadata.update(metadata)
    context.metadata["route"] = fast_result.get("forward_to", "RAG")
    context.normalized_message = fast_result.get("normalized", message)
    if fast_result.get("alias_intent"):
        context.current_intent = fast_result.get("alias_intent")
    if fast_result.get("entities"):
        context.entities.update(fast_result.get("entities"))
    if fast_result.get("trace"):
        context.metadata["fast_trace"] = fast_result.get("trace")
    
    result = pipeline_runner.process(context)
    
    from fastapi.responses import JSONResponse
    if result.get("success") is False:
        return JSONResponse(status_code=500, content=result)
        
    return JSONResponse(content={
        "intent": result["intent"],
        "response": result["response"],
        "components": result.get("components", []),
        "actions": result.get("actions", []),
        "trace": result.get("trace")
    })


# backend/api/routes/chat_ws.py

logger = get_logger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket client {client_id} connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"WebSocket client {client_id} disconnected. Active connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
            except RuntimeError as e:
                # Expected when a client disconnects while a message is being generated/sent
                logger.info(f"Client {client_id} disconnected during message send.")
                self.disconnect(client_id)
            except WebSocketDisconnect:
                logger.info(f"Client {client_id} disconnected.")
                self.disconnect(client_id)
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)

manager = ConnectionManager()

@router.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    # Using client host+port as a temporary ID if no session provided yet
    if websocket.client:
        client_id = f"{websocket.client.host}:{websocket.client.port}"
    else:
        import uuid
        client_id = str(uuid.uuid4())
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
                continue
                
            try:
                request_data = json.loads(data)
                message = request_data.get("message", "")
                session_id = request_data.get("session_id", "default")
                conversation_id = request_data.get("conversation_id", "default")
                metadata = request_data.get("metadata", {})
                
                fast_result = run_fast_pipeline(message, session_id, metadata)
                if fast_result.get("success"):
                    await manager.send_personal_message({"type": "done", **fast_result}, client_id)
                    continue
                    
                context = PipelineContext(
                    original_message=message,
                    session_id=session_id,
                    conversation_id=conversation_id
                )
                context.metadata.update(metadata)
                context.metadata["route"] = fast_result.get("forward_to", "RAG")
                context.normalized_message = fast_result.get("normalized", message)
                if fast_result.get("alias_intent"):
                    context.current_intent = fast_result.get("alias_intent")
                if fast_result.get("entities"):
                    context.entities.update(fast_result.get("entities"))
                if fast_result.get("trace"):
                    context.metadata["fast_trace"] = fast_result.get("trace")
                
                async for event in pipeline_runner.process_stream(context):
                    if client_id not in manager.active_connections:
                        break # Client disconnected, stop yielding events
                    await manager.send_personal_message(event, client_id)
                    
            except json.JSONDecodeError:
                await manager.send_personal_message({"type": "error", "error": "Invalid JSON payload."}, client_id)
            except Exception as e:
                logger.error(f"Error processing websocket message: {e}")
                await manager.send_personal_message({"type": "error", "error": str(e)}, client_id)
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except RuntimeError as e:
        if "Unexpected ASGI message" in str(e):
            manager.disconnect(client_id) # Client abruptly disconnected
        else:
            logger.error(f"WebSocket error: {e}")
            manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(client_id)



# backend/api/routes/health.py

@router.get("/")
def default_health():
    return {"status": "ok", "message": "Backend is online"}

@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.get("/liveness")
def liveness_check():
    return {"status": "alive"}

@router.get("/readiness")
def readiness_check():
    from core.database import engine
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Database not ready")


