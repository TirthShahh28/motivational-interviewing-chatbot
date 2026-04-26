"""
FastAPI backend for the end-user web interface.
===============================================

Wraps the existing src.conversation_manager pipeline (state inference + RAG +
response generation + safety layer) behind a single /api/chat endpoint, and
serves the Claude Design frontend (capstone-chatbot-design/) as static files
from the same origin so there are no CORS issues.

Run:
    uvicorn backend_server:app --host 0.0.0.0 --port 8000 --reload

Then open http://localhost:8000 in a browser.

The original Streamlit dev/eval interface (app.py) is untouched.
"""

from __future__ import annotations

import socket
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from pydantic import BaseModel, Field

from src.config import OLLAMA_BASE_URL, ANTHROPIC_API_KEY
from src.conversation_manager import create_conversation_manager
from src.safety_layer import SafetyLevel


PROJECT_ROOT = Path(__file__).parent
FRONTEND_DIR = PROJECT_ROOT / "capstone-chatbot-design"
INDEX_FILE = FRONTEND_DIR / "Aside.html"

CRISIS_CARD_MESSAGE = (
    "I want to slow down for a second. What you just shared sounds really heavy, "
    "and I want to make sure you have the right kind of support — not just me. "
    "The people above are trained for exactly this, and you can reach them right now."
)

app = FastAPI(title="Aside — supportive conversation companion")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


_conversation_manager = None


def _ollama_reachable(timeout: float = 0.6) -> bool:
    """Quick TCP probe so we don't pick Ollama as the provider when its server
    isn't running. The factory creates a lazy LangChain client either way, so
    without this probe the failure only surfaces on the first chat call."""
    try:
        parsed = urlparse(OLLAMA_BASE_URL)
        host = parsed.hostname or "localhost"
        port = parsed.port or 11434
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _candidate_providers() -> list[str]:
    order: list[str] = []
    if _ollama_reachable():
        order.append("ollama")
    else:
        logger.info(f"Ollama not reachable at {OLLAMA_BASE_URL} — skipping")
    if ANTHROPIC_API_KEY:
        order.append("anthropic")
    return order


def _load_manager():
    global _conversation_manager
    if _conversation_manager is not None:
        return _conversation_manager

    providers = _candidate_providers()
    if not providers:
        raise RuntimeError(
            "No LLM provider available. Either start Ollama (`ollama serve`) "
            "or set ANTHROPIC_API_KEY in .env."
        )

    last_err: Optional[Exception] = None
    for provider in providers:
        try:
            logger.info(f"Initializing conversation manager (provider={provider})")
            _conversation_manager = create_conversation_manager(provider=provider)
            logger.info(f"Conversation manager ready (provider={provider})")
            return _conversation_manager
        except Exception as e:
            last_err = e
            logger.warning(f"Provider {provider} unavailable: {e}")

    raise RuntimeError(
        f"All providers failed: {[p for p in providers]}"
    ) from last_err


@app.on_event("startup")
def _startup():
    try:
        _load_manager()
    except Exception as e:
        logger.error(f"Startup model load failed: {e}")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    role: str = "assistant"
    content: str
    session_id: str
    crisis: bool = False
    crisisPayload: Optional[dict] = None


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    try:
        cm = _load_manager()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    try:
        result = cm.process_message(req.message, session_id=req.session_id)
    except Exception as e:
        logger.exception("process_message failed")
        raise HTTPException(status_code=500, detail=f"Pipeline error: {e}")

    safety_level = result.get("safety_level", SafetyLevel.SAFE)
    is_crisis = safety_level == SafetyLevel.CRISIS

    if is_crisis:
        content = CRISIS_CARD_MESSAGE
    else:
        content = result.get("response") or "I hear you. Can you tell me more about what's on your mind?"

    return ChatResponse(
        role="assistant",
        content=content,
        session_id=result["session_id"],
        crisis=is_crisis,
        crisisPayload={"reason": "self-harm language detected"} if is_crisis else None,
    )


class NewSessionResponse(BaseModel):
    session_id: str
    cleared: bool


@app.post("/api/new", response_model=NewSessionResponse)
def new_session(session_id: Optional[str] = None):
    cm = _load_manager()
    if session_id:
        cm.clear_session(session_id)
        return NewSessionResponse(session_id=session_id, cleared=True)
    return NewSessionResponse(session_id="", cleared=False)


@app.get("/api/health")
def health():
    return {"status": "ok", "model_loaded": _conversation_manager is not None}


# ── Static frontend ───────────────────────────────────────────────────────────
# Serve the Claude Design export. Aside.html references files at relative paths
# (src/*.jsx, tweaks-panel.jsx), so we mount the directory at root.

@app.get("/")
def index():
    if not INDEX_FILE.exists():
        raise HTTPException(status_code=500, detail="Frontend not found")
    return FileResponse(INDEX_FILE)


app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=False), name="frontend")
