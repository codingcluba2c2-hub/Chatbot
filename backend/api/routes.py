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

from chatbot.detector import FastPathRouterStep, GibberishStep, NormalizeStep
from chatbot.followup import FollowUpResolverStep
from chatbot.context_resolver import ConversationContextResolverStep
from chatbot.abuse import AbuseDetectionStep
from chatbot.greeting import GreetingFarewellStep
from chatbot.faq import FAQStep
from chatbot.rag import KnowledgeSearchStep, ResponseGeneratorStep
from services.knowledge import KnowledgeTreeStep
from chatbot.memory import MemoryDetectorStep
from core.schemas import ChatResponse, ChatRequest


# backend/api/routes/chat.py


pipeline_runner = PipelineRunner()
pipeline_runner.register_step("Normalize", NormalizeStep())
pipeline_runner.register_step("GreetingFarewell", GreetingFarewellStep())
pipeline_runner.register_step("FollowUpResolver", FollowUpResolverStep())
pipeline_runner.register_step("ConversationContextResolver", ConversationContextResolverStep())
pipeline_runner.register_step("Memory", MemoryDetectorStep())
pipeline_runner.register_step("KnowledgeTree", KnowledgeTreeStep())
pipeline_runner.register_step("Gibberish", GibberishStep())
pipeline_runner.register_step("AbuseDetection", AbuseDetectionStep())
pipeline_runner.register_step("FastPath", FastPathRouterStep())
pipeline_runner.register_step("FAQ", FAQStep())
pipeline_runner.register_step("KnowledgeSearch", KnowledgeSearchStep())
pipeline_runner.register_step("ResponseGenerator", ResponseGeneratorStep())


router = APIRouter()

@router.on_event("startup")
async def startup_event():
    logger.info("Application Startup: Initializing Singletons...")
    from services.embeddings import get_embedding_provider
    from services.vectorstore import get_vector_store
    from chatbot.llm import get_llm_provider
    from chatbot.rag import Retriever
    
    get_embedding_provider()
    get_vector_store()
    get_llm_provider()
    
    try:
        # Pre-initialize retriever to ensure models are hot
        Retriever()
        logger.info("Singletons Initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize singletons: {e}")

@router.post("/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
async def chat_endpoint(request: Request, chat_request: ChatRequest):
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
                
                context = PipelineContext(
                    original_message=message,
                    session_id=session_id,
                    conversation_id=conversation_id
                )
                context.metadata.update(metadata)
                
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
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Database not ready")


