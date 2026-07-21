# backend/api/routes/chat_ws.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pipeline.pipeline_runner import PipelineRunner
from pipeline.pipeline_context import PipelineContext
from core.logger import get_logger
import json
from .chat import pipeline_runner  # Use the same pre-configured runner instance

logger = get_logger(__name__)
router = APIRouter()

@router.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection established.")
    try:
        while True:
            data = await websocket.receive_text()
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
                
                # Iterate through the async generator
                async for event in pipeline_runner.process_stream(context):
                    await websocket.send_json(event)
                    
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "error": "Invalid JSON payload."})
            except Exception as e:
                logger.error(f"Error processing websocket message: {e}")
                await websocket.send_json({"type": "error", "error": str(e)})
                
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected.")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
