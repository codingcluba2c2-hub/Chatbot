# backend/app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.chat import router as chat_router
from api.routes.health import router as health_router
from api.routes.session import router as session_router
from api.routes.admin import router as admin_router
from api.routes.knowledge import router as knowledge_router
from core.logger import get_logger
from core.database import Base, engine
from repositories.seed import seed_data

logger = get_logger("app")

# Create database tables
Base.metadata.create_all(bind=engine)

# Seed initial data
seed_data()

app = FastAPI(title="Enterprise AI Pipeline API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
)

app.include_router(chat_router)
app.include_router(health_router)
app.include_router(session_router)
app.include_router(admin_router)
app.include_router(knowledge_router)

logger.info("FastAPI application initialized with modular AI pipeline")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
