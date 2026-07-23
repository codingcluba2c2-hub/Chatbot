import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from chatbot.utils import limiter
import traceback
import time
from contextlib import asynccontextmanager

from api.routes import router as api_router
from api.admin import router as admin_router
from api.knowledge import router as knowledge_router

from core.logger import get_logger

logger = get_logger("app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    t0 = time.time()
    print("\n----------------------------------------")
    print("Starting UltraFastEngine (API Port 8001)...")
    
    # Cache Warmup - MUST be completely synchronous and RAM-only
    print("Pre-loading Greeting, FAQ, Regex into RAM...")
    from chatbot.in_memory_engine import engine
    s = time.time()
    engine.load_all()
    cache_time = int((time.time() - s) * 1000)
    
    total_time = int((time.time() - t0) * 1000)
    
    print("\n==============================")
    print("UltraFastEngine Startup Report")
    print("==============================\n")
    print(f"RAM Cache Preload: {cache_time} ms")
    print(f"Total Startup: {total_time} ms")
    print("Status: READY (Dependency-Free Fast Path)")
    print("\n==============================\n")
    
    # Initialize Local Retriever for Ultrafast Engine
    print("Loading Embeddings and Vector Store into RAM for Local Retrieval...")
    from services.embeddings import initialize_embedding_provider
    from services.vectorstore import initialize_vector_store
    from chatbot.rag import initialize_retriever
    
    t_ret = time.time()
    initialize_embedding_provider()
    initialize_vector_store()
    initialize_retriever()
    ret_time = int((time.time() - t_ret) * 1000)
    
    # We do NOT initialize LLM here. That is handled entirely by EnterpriseAIEngine (Port 8002).
    total_time = int((time.time() - t0) * 1000)
    
    # Detect IP
    import socket
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
    except Exception:
        ip = "127.0.0.1"

    print("\n======================================")
    print("Enterprise Chatbot Ready")
    print(f"Host IP:\n{ip}\n")
    print(f"Frontend:\nhttp://{ip}:3000\n")
    print(f"Backend:\nhttp://{ip}:8001\n")
    print(f"AI Engine:\nhttp://{ip}:8002\n")
    print("Status:\nREADY\n")
    print("WARNING: Windows Firewall may block incoming connections.")
    print("Allow TCP Ports: 3000, 8001, 8002")
    print("======================================\n")
    
    yield
    print("Shutting down UltraFastEngine...")
    try:
        from core.database import engine
        from api.routes import manager
        
        for client_id in list(manager.active_connections.keys()):
            try:
                manager.disconnect(client_id)
            except Exception:
                pass
                
        engine.dispose()
        print("Database connections closed gracefully.")
    except Exception as e:
        print(f"Error during shutdown: {e}")

app = FastAPI(title="Enterprise UltraFastEngine API", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Use regex for LAN IPs and explicitly allowed origins
# Allow localhost, 127.0.0.1, 192.168.*.*, 10.*.*.*, 172.16.*.*
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2[0-9]|3[0-1])\.\d+\.\d+)(:\d+)?$",
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
)

# TIMING MIDDLEWARE PROFILER
@app.middleware("http")
async def add_timing_profiler(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Only print for chat requests to avoid noise
    if "/chat" in request.url.path:
        print("\n-----------------------------------")
        print(f"FastAPI Receive -> Render: {int(process_time * 1000)}ms")
        print("-----------------------------------\n")
    return response

app.include_router(api_router)
app.include_router(admin_router)
app.include_router(knowledge_router)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception on {request.method} {request.url.path}")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": f"Error: {str(exc)}\n{traceback.format_exc()}"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8001, reload=True)
