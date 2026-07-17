import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
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
    print("http://127.0.0.1:8000")
    print(f"Startup Time: {time.time() - t0:.2f} sec")
    print("----------------------------------------\n")
    yield
    print("Shutting down...")

app = FastAPI(title="Enterprise AI Pipeline API", lifespan=lifespan)

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
app.include_router(dashboard_router)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception on {request.method} {request.url.path}")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "step": "GlobalMiddleware",
            "error": str(exc),
            "traceback": traceback.format_exc(),
            "developer_message": "An unhandled exception crashed the request.",
            "user_message": "Internal server error."
        }
    )

logger.info("FastAPI application initialized with modular AI pipeline")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
