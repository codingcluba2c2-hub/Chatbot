# backend/api/routes/chat_ws.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pipeline.pipeline_runner import PipelineRunner
from pipeline.pipeline_context import PipelineContext
from core.logger import get_logger
import json
import asyncio
from typing import Dict, List
from .chat import pipeline_runner

logger = get_logger(__name__)
router = APIRouter()

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
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)

manager = ConnectionManager()

@router.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    # Using client host+port as a temporary ID if no session provided yet
    client_id = f"{websocket.client.host}:{websocket.client.port}"
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
                    await manager.send_personal_message(event, client_id)
                    
            except json.JSONDecodeError:
                await manager.send_personal_message({"type": "error", "error": "Invalid JSON payload."}, client_id)
            except Exception as e:
                logger.error(f"Error processing websocket message: {e}")
                await manager.send_personal_message({"type": "error", "error": str(e)}, client_id)
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(client_id)

