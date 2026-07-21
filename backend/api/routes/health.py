# backend/api/routes/health.py
from fastapi import APIRouter
from core.database import engine
from sqlalchemy import text

router = APIRouter()

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
