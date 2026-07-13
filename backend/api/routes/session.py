# backend/api/routes/session.py
from fastapi import APIRouter
from services.session_manager import SessionManager
from services.conversation_memory_service import ConversationMemoryService

router = APIRouter(prefix="/api/session", tags=["Session"])

@router.get("/current")
def get_current_session(session_id: str):
    session = SessionManager.get_session(session_id)
    return {"session": session}
    
@router.get("/history")
def get_session_history(session_id: str):
    memory = ConversationMemoryService.get_memory(session_id)
    return {"messages": memory.get("messages", [])}
    
@router.get("/memory")
def get_session_memory(session_id: str):
    memory = ConversationMemoryService.get_memory(session_id)
    return {
        "facts": memory.get("facts", {}),
        "entities": memory.get("entities", {})
    }
    
@router.delete("/clear")
def clear_session(session_id: str):
    SessionManager.clear_session_data(session_id)
    ConversationMemoryService.clear_memory(session_id)
    return {"status": "cleared"}
    
@router.get("/summary")
def get_session_summary(session_id: str):
    memory = ConversationMemoryService.get_memory(session_id)
    return {"summary": memory.get("summary", [])}
