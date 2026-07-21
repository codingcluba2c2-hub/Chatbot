import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from core.rate_limit import limiter
import traceback
from api.routes.chat import router as chat_router
from api.routes.health import router as health_router
from api.routes.session import router as session_router
from api.routes.admin import router as admin_router
from api.routes.knowledge import router as knowledge_router
from api.routes.dashboard import router as dashboard_router
from core.logger import get_logger

logger = get_logger("app")

import time
from contextlib import asynccontextmanager
@asynccontextmanager
async def lifespan(app: FastAPI):
    t0 = time.time()
    print("\n----------------------------------------")
    print("Starting Chatbot Backend...")
    print("[OK] Config Loaded")
    print("[OK] API Routes Registered")
    print("[OK] Server Ready")
    print("Backend running at:")
    print("http://127.0.0.1:8001")
    print(f"Startup Time: {time.time() - t0:.2f} sec")
    print("----------------------------------------\n")
    yield
    print("Shutting down...")
    try:
        from core.database import engine
        from api.routes.chat_ws import manager
        
        for client_id in list(manager.active_connections.keys()):
            try:
                manager.disconnect(client_id)
            except Exception:
                pass
                
        engine.dispose()
        print("Database connections closed gracefully.")
    except Exception as e:
        print(f"Error during shutdown: {e}")

app = FastAPI(title="Enterprise AI Pipeline API", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

cors_origins = os.getenv("CORS_ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
)

from api.routes.chat_ws import router as chat_ws_router

app.include_router(chat_ws_router)
app.include_router(chat_router)
app.include_router(health_router)
app.include_router(session_router)
app.include_router(admin_router)
app.include_router(knowledge_router)
app.include_router(dashboard_router)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception on {request.method} {request.url.path}")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Something went wrong."
        }
    )

logger.info("FastAPI application initialized with modular AI pipeline")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8001, reload=True)
