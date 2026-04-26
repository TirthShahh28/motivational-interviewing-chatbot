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
# Ollama (Local LLM — fine-tuned MI therapist model)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mi-therapist")

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
# Keywords/patterns that trigger safety protocols.
# Patterns allow for an optional intensifier word (even/really/just/actually/still)
# between auxiliaries and verbs, since real users phrase passive ideation that way
# more often than the textbook form.
SAFETY_RED_FLAGS = [
    # Active suicidal ideation
    r"suicid\w*", r"kill\s*(my)?self", r"end\s+my\s+life", r"take\s+my\s+(own\s+)?life",
    r"(end|kill)\s+it\s+all",
    # Self-harm
    r"self[- ]?harm", r"hurt\s*(my)?self", r"cut\s*(my)?self",
    # Overdose
    r"\bover\s*dose\b", r"\bod['.]?(?:ing|ed)?\b",
    # Death wish / passive ideation
    r"want(\s+\w+)?\s+to\s+die", r"wish\s+i\s+w(as|ere)\s+dead",
    r"better\s+off\s+(dead|without\s+me|gone|if\s+i\s+(was|were)\s+gone)",
    r"rather\s+be\s+dead",
    r"no\s+reason\s+to\s+(live|keep\s+going|go\s+on|continue|exist|wake\s+up)",
    r"no\s+point\s+(in\s+)?(living|keep\s+going|going\s+on|continuing|exist)",
    r"don'?t\s+see\s+(a\s+|any\s+)?(reason|point|way)\s+to\s+(keep\s+going|go\s+on|live|continue)",
    r"can'?t\s+(take|do|handle)\s+(it|this)\s+(anymore|any\s+longer)",
    # The (?:\w+\s+)? group catches "don't even want", "don't really want", "don't just want", etc.
    r"don'?t\s+(?:\w+\s+)?want\s+to\s+(be\s+here|live|keep\s+going|wake\s+up|go\s+on|exist|be\s+alive)",
    r"won'?t\s+be\s+around\s+(much\s+)?longer",
    r"want\s+it\s+(all\s+)?to\s+end",
    r"nothing\s+left\s+(for\s+me|to\s+live\s+for)",
    r"thinking\s+about\s+(ending|killing)",
]

# Topics the bot should NOT provide advice on
RESTRICTED_TOPICS = [
    "medication dosage", "prescription", "diagnosis",
    "medical treatment", "detox protocol"
]

# ============== LOGGING ==============
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
