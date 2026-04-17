import os
import time
import json
import logging
import signal
import uuid
import redis
from fastapi import FastAPI, Depends, HTTPException, Request
from pydantic import BaseModel
from .config import settings
from .auth import verify_api_key
from .rate_limiter import check_rate_limit
from .cost_guard import check_budget
from utils.mock_llm import ask

# Configure JSON Logging
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": time.time(),
            "level": record.levelname,
            "event": record.getMessage(),
            "module": record.module,
        }
        return json.dumps(log_entry)

logger = logging.getLogger("agent")
handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger.addHandler(handler)
logger.setLevel(settings.LOG_LEVEL)

_is_ready = False
r = redis.from_url(settings.REDIS_URL, decode_responses=True)

app = FastAPI(title="Production Ready AI Agent")

class ChatRequest(BaseModel):
    question: str

@app.on_event("startup")
async def startup_event():
    global _is_ready
    logger.info("Agent starting up...")
    try:
        r.ping()
        _is_ready = True
        logger.info("✅ Agent is ready and Redis connected.")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    global _is_ready
    _is_ready = False
    logger.info("🔄 Graceful shutdown initiated...")
    time.sleep(1)  # Simulate cleaning up

def handle_sigterm(signum, frame):
    logger.info(f"Received signal {signum} (SIGTERM)")

signal.signal(signal.SIGTERM, handle_sigterm)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    logger.info(f"Request: {request.method} {request.url.path} - {response.status_code} - {duration:.4f}s")
    return response

@app.get("/health")
def health():
    return {"status": "ok", "uptime": time.time(), "instance_id": str(uuid.uuid4())[:8]}

@app.get("/ready")
def ready():
    if not _is_ready:
        raise HTTPException(status_code=503, detail="Agent not ready")
    try:
        r.ping()
    except Exception:
        raise HTTPException(status_code=503, detail="Redis connection lost")
    return {"status": "ready"}

@app.post("/ask")
def ask_endpoint(
    body: ChatRequest,
    user_id: str = Depends(check_budget) # Chained dependencies
):
    # Get history from Redis
    history_key = f"history:{user_id}"
    history = r.lrange(history_key, -10, -1)
    
    # Call LLM
    answer = ask(body.question)
    
    # Save to history
    r.rpush(history_key, json.dumps({"q": body.question, "a": answer}))
    r.ltrim(history_key, -10, -1)
    r.expire(history_key, 3600)
    
    return {
        "question": body.question,
        "answer": answer,
        "user_id": user_id
    }
