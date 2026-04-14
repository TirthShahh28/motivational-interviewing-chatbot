"""
Configuration settings for the chatbot system.
Centralizes all environment variables and system constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============== PATH CONFIGURATION ==============
PROJECT_ROOT = Path(__file__).parent.parent
KNOWLEDGE_BASE_DIR = PROJECT_ROOT / "knowledge_base"
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"

# ============== LLM CONFIGURATION ==============
# Ollama (Local LLM)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:4b")

# Anthropic (Claude)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", None)
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

# OpenAI (Optional fallback)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", None)
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# ============== RAG CONFIGURATION ==============
CHROMA_PERSIST_DIR = DATA_DIR / "chroma_db"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Sentence-transformers model
CHUNK_SIZE = 500  # Characters per chunk
CHUNK_OVERLAP = 50  # Overlap between chunks
TOP_K_RESULTS = 3  # Number of documents to retrieve

# ============== CONVERSATION SETTINGS ==============
CONTEXT_WINDOW_TURNS = 5  # Number of previous turns to include
MAX_RESPONSE_TOKENS = 500

# ============== STATE INFERENCE SETTINGS ==============
# Possible emotional states
EMOTION_STATES = [
    "neutral",
    "frustrated", 
    "anxious",
    "sad",
    "angry",
    "hopeful",
    "contemplative"
]

# Possible defensiveness levels  
DEFENSIVENESS_LEVELS = [
    "none",      # Open and receptive
    "low",       # Slight resistance
    "moderate",  # Clear defensive markers
    "high"       # Strong denial/rationalization
]

# ============== SAFETY CONFIGURATION ==============
# Keywords that trigger safety protocols
SAFETY_RED_FLAGS = [
    "suicide", "kill myself", "end my life", "self-harm",
    "hurt myself", "overdose", "want to die"
]

# Topics the bot should NOT provide advice on
RESTRICTED_TOPICS = [
    "medication dosage", "prescription", "diagnosis",
    "medical treatment", "detox protocol"
]

# ============== LOGGING ==============
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
