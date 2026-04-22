"""
Conversation Manager
====================
Orchestrates the entire conversational pipeline:
1. Receive user input
2. Run safety check
3. Infer user state
4. Retrieve relevant knowledge
5. Generate adaptive response
6. Run output safety check
7. Log interaction
8. Return response

This is the main controller that the UI interacts with.
"""

import uuid
from typing import Optional, Generator
from dataclasses import dataclass, field
from loguru import logger

from src.config import CONTEXT_WINDOW_TURNS, LOGS_DIR
from src.state_inference import StateInferenceEngine, UserState
from src.rag_pipeline import KnowledgeRetriever
from src.response_generator import ResponseGenerator
from src.safety_layer import SafetyGuard, SafetyLevel, ConversationLogger


@dataclass
class ConversationTurn:
    """Represents a single turn in the conversation."""
    role: str  # "user" or "assistant"
    content: str
    state: Optional[UserState] = None
    safety_level: Optional[SafetyLevel] = None


@dataclass 
class ConversationSession:
    """Tracks state for a single conversation session."""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    history: list[ConversationTurn] = field(default_factory=list)
    
    def add_turn(self, role: str, content: str, **kwargs):
        """Add a turn to the conversation history."""
        self.history.append(ConversationTurn(role=role, content=content, **kwargs))
    
    def get_context_window(self, n_turns: int = None) -> list[dict]:
        """Get the last n turns as a list of dicts."""
        n = n_turns or CONTEXT_WINDOW_TURNS
        recent = self.history[-n*2:] if len(self.history) > n*2 else self.history
        return [{"role": t.role, "content": t.content} for t in recent]
    
    def clear(self):
        """Clear conversation history."""
        self.history = []


class ConversationManager:
    """
    Main orchestrator for the chatbot pipeline.
    
    Coordinates all components:
    - State inference
    - RAG retrieval
    - Response generation
    - Safety checks
    - Logging
    """
    
    def __init__(
        self,
        llm_client,
        knowledge_retriever: KnowledgeRetriever = None,
        enable_logging: bool = True,
        use_fast_state: bool = False
    ):
        """
        Initialize the conversation manager.

        Args:
            llm_client: LangChain LLM instance
            knowledge_retriever: Initialized KnowledgeRetriever
            enable_logging: Whether to log conversations
            use_fast_state: Use rule-based state inference (faster, no LLM call)
        """
        self.llm = llm_client

        # Initialize components
        self.state_engine = StateInferenceEngine(llm_client, use_rule_based=use_fast_state)
        self.response_generator = ResponseGenerator(llm_client)
        self.safety_guard = SafetyGuard()
        
        # RAG (optional - can work without knowledge base)
        self.knowledge_retriever = knowledge_retriever
        
        # Logging
        self.enable_logging = enable_logging
        if enable_logging:
            self.logger = ConversationLogger(LOGS_DIR)
        
        # Active sessions
        self.sessions: dict[str, ConversationSession] = {}
        
        logger.info("ConversationManager initialized")
    
    def get_or_create_session(self, session_id: str = None) -> ConversationSession:
        """Get existing session or create new one."""
        if session_id and session_id in self.sessions:
            return self.sessions[session_id]
        
        session = ConversationSession()
        self.sessions[session.session_id] = session
        logger.info(f"Created new session: {session.session_id}")
        return session
    
    def process_message(
        self, 
        user_message: str, 
        session_id: str = None
    ) -> dict:
        """
        Process a user message through the full pipeline.
        
        Args:
            user_message: The user's input
            session_id: Optional session ID for continuity
            
        Returns:
            Dict with response and metadata
        """
        # Get or create session
        session = self.get_or_create_session(session_id)
        
        result = {
            "session_id": session.session_id,
            "user_message": user_message,
            "response": "",
            "user_state": None,
            "safety_level": SafetyLevel.SAFE,
            "retrieved_knowledge": [],
            "intervention": False
        }
        
        # ========== STEP 1: INPUT SAFETY CHECK ==========
        input_safety = self.safety_guard.check_input(user_message)
        result["safety_level"] = input_safety.level
        
        if input_safety.should_intervene:
            result["response"] = input_safety.intervention_message
            result["intervention"] = True
            
            # Still add to history for context
            session.add_turn("user", user_message, safety_level=input_safety.level)
            session.add_turn("assistant", result["response"])
            
            self._log_interaction(session, result)
            return result
        
        # ========== STEP 2: STATE INFERENCE ==========
        conversation_context = session.get_context_window()
        user_state = self.state_engine.infer_state(user_message, conversation_context)
        result["user_state"] = user_state
        
        logger.info(
            f"State inferred - Emotion: {user_state.emotion}, "
            f"Defensiveness: {user_state.defensiveness}"
        )
        
        # ========== STEP 3: KNOWLEDGE RETRIEVAL (RAG) ==========
        retrieved_knowledge = []
        if self.knowledge_retriever:
            retrieved_knowledge = self.knowledge_retriever.retrieve_for_state(
                user_message,
                user_state.emotion,
                user_state.defensiveness
            )
            result["retrieved_knowledge"] = retrieved_knowledge
            logger.debug(f"Retrieved {len(retrieved_knowledge)} knowledge chunks")
        
        # ========== STEP 4: RESPONSE GENERATION ==========
        response = self.response_generator.generate(
            user_message=user_message,
            user_state=user_state,
            conversation_history=conversation_context,
            retrieved_knowledge=retrieved_knowledge
        )
        
        # ========== STEP 5: OUTPUT SAFETY CHECK ==========
        output_safety = self.safety_guard.check_output(response)
        
        if output_safety.level == SafetyLevel.BLOCKED:
            # Regenerate with safer prompt or use fallback
            logger.warning("Response blocked by safety filter, using fallback")
            response = "I hear what you're saying. Can you tell me more about how this is affecting you?"
        
        result["response"] = response
        
        # ========== STEP 6: UPDATE HISTORY ==========
        session.add_turn(
            "user", 
            user_message, 
            state=user_state, 
            safety_level=input_safety.level
        )
        session.add_turn("assistant", response)
        
        # ========== STEP 7: LOG INTERACTION ==========
        self._log_interaction(session, result)
        
        return result
    
    def _log_interaction(self, session: ConversationSession, result: dict):
        """Log the interaction if logging is enabled."""
        if not self.enable_logging:
            return
        
        user_state_dict = None
        if result.get("user_state"):
            user_state_dict = result["user_state"].model_dump()
        
        self.logger.log_interaction(
            session_id=session.session_id,
            user_message=result["user_message"],
            bot_response=result["response"],
            user_state=user_state_dict,
            safety_level=result["safety_level"],
            retrieved_knowledge=result.get("retrieved_knowledge")
        )
    
    def get_session_history(self, session_id: str) -> list[dict]:
        """Get conversation history for a session."""
        if session_id not in self.sessions:
            return []
        return self.sessions[session_id].get_context_window(n_turns=100)
    
    def clear_session(self, session_id: str):
        """Clear a session's history."""
        if session_id in self.sessions:
            self.sessions[session_id].clear()
            logger.info(f"Session {session_id} cleared")


def create_conversation_manager(provider: str = "ollama") -> ConversationManager:
    """
    Factory function to create a fully configured ConversationManager.

    Args:
        provider: LLM provider - "ollama", "anthropic", or "openai"

    Returns:
        Configured ConversationManager instance
    """
    from src.config import (
        OLLAMA_BASE_URL, OLLAMA_MODEL,
        ANTHROPIC_API_KEY, ANTHROPIC_MODEL,
        OPENAI_API_KEY, OPENAI_MODEL
    )

    # Initialize LLM
    if provider == "ollama":
        try:
            from langchain_ollama import ChatOllama
        except ImportError:
            from langchain_community.chat_models import ChatOllama
        llm = ChatOllama(
            base_url=OLLAMA_BASE_URL,
            model=OLLAMA_MODEL,
            temperature=0.7,
            num_predict=200,
        )
        logger.info(f"Using Ollama with model: {OLLAMA_MODEL}")
    elif provider == "anthropic":
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not set in environment")
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(
            api_key=ANTHROPIC_API_KEY,
            model=ANTHROPIC_MODEL,
            temperature=0.7,
            max_tokens=500
        )
        logger.info(f"Using Anthropic with model: {ANTHROPIC_MODEL}")
    else:
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set in environment")
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            temperature=0.7
        )
        logger.info(f"Using OpenAI with model: {OPENAI_MODEL}")
    
    # Initialize knowledge retriever (optional - can fail gracefully)
    retriever = None
    try:
        retriever = KnowledgeRetriever()
        if not retriever.load_existing_index():
            # Try to index knowledge base
            num_chunks = retriever.load_and_index_documents()
            if num_chunks == 0:
                logger.warning("No knowledge base loaded - RAG will be disabled")
                retriever = None
    except Exception as e:
        logger.warning(f"RAG initialization failed: {e}. Continuing without RAG.")
        retriever = None
    
    # Use fast rule-based state inference for local models (saves ~30s per message)
    use_fast = (provider == "ollama")

    return ConversationManager(
        llm_client=llm,
        knowledge_retriever=retriever,
        enable_logging=True,
        use_fast_state=use_fast
    )
