"""
State Inference Module
======================
Analyzes user input to detect emotional state and defensiveness level.
Uses LLM-based classification with structured output.

This is the core module that makes the chatbot "aware" of user psychological state.
"""

import json
from typing import Optional
from pydantic import BaseModel, Field
from loguru import logger

from src.config import EMOTION_STATES, DEFENSIVENESS_LEVELS


class UserState(BaseModel):
    """Structured representation of inferred user state."""
    emotion: str = Field(
        default="neutral",
        description="Primary emotional state detected"
    )
    defensiveness: str = Field(
        default="none", 
        description="Level of defensiveness detected"
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0, le=1.0,
        description="Confidence score of the inference"
    )
    reasoning: str = Field(
        default="",
        description="Brief explanation for the classification"
    )
    linguistic_markers: list[str] = Field(
        default_factory=list,
        description="Specific phrases that indicated this state"
    )


# Prompt template for state inference
STATE_INFERENCE_PROMPT = """You are an expert psychologist specializing in addiction counseling and Motivational Interviewing (MI).

Analyze the following user message for emotional state and defensiveness. 

## Defensiveness Markers to Look For:
- **Denial**: "I don't have a problem", "I can stop anytime"
- **Rationalization**: "I only drink because...", "Everyone does it"  
- **Minimization**: "It's not that bad", "I only drink a little"
- **Projection**: "You don't understand", "Other people are worse"
- **Hostility**: Aggressive language, deflection, personal attacks

## Emotional Indicators:
- **Frustrated**: Exasperation, feeling misunderstood
- **Anxious**: Worry, fear, uncertainty about change
- **Sad**: Hopelessness, regret, loss
- **Angry**: Hostility, blame, irritation
- **Hopeful**: Interest in change, asking questions
- **Contemplative**: Weighing pros/cons, ambivalence

## Conversation Context (last {n_turns} turns):
{context}

## Current User Message:
"{user_message}"

## Your Task:
Classify the user's state and respond ONLY with valid JSON in this exact format:
{{
    "emotion": "<one of: neutral, frustrated, anxious, sad, angry, hopeful, contemplative>",
    "defensiveness": "<one of: none, low, moderate, high>",
    "confidence": <float between 0.0 and 1.0>,
    "reasoning": "<1-2 sentence explanation>",
    "linguistic_markers": ["<specific phrase 1>", "<specific phrase 2>"]
}}
"""


class StateInferenceEngine:
    """
    Engine for analyzing user psychological state.
    
    Uses an LLM to classify emotional state and defensiveness
    based on linguistic markers and conversation context.
    """
    
    def __init__(self, llm_client):
        """
        Initialize the state inference engine.
        
        Args:
            llm_client: LangChain LLM instance (Ollama or OpenAI)
        """
        self.llm = llm_client
        logger.info("StateInferenceEngine initialized")
    
    def infer_state(
        self, 
        user_message: str, 
        conversation_history: list[dict] = None
    ) -> UserState:
        """
        Analyze user message and infer psychological state.
        
        Args:
            user_message: The current user input
            conversation_history: List of previous turns [{"role": "user/assistant", "content": "..."}]
            
        Returns:
            UserState object with emotion, defensiveness, and reasoning
        """
        # Format conversation context
        context = self._format_context(conversation_history or [])
        
        # Build prompt
        prompt = STATE_INFERENCE_PROMPT.format(
            n_turns=len(conversation_history or []),
            context=context if context else "No previous context.",
            user_message=user_message
        )
        
        try:
            # Call LLM
            response = self.llm.invoke(prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Parse JSON response
            state = self._parse_response(response_text)
            logger.debug(f"Inferred state: {state}")
            return state
            
        except Exception as e:
            logger.error(f"State inference failed: {e}")
            # Return default neutral state on failure
            return UserState(
                reasoning=f"Inference failed: {str(e)}"
            )
    
    def _format_context(self, history: list[dict]) -> str:
        """Format conversation history for the prompt."""
        if not history:
            return ""
        
        formatted = []
        for turn in history[-5:]:  # Last 5 turns
            role = turn.get("role", "unknown").upper()
            content = turn.get("content", "")
            formatted.append(f"{role}: {content}")
        
        return "\n".join(formatted)
    
    def _parse_response(self, response: str) -> UserState:
        """Parse LLM response into UserState object."""
        # Try to extract JSON from response
        try:
            # Handle case where LLM wraps JSON in markdown
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            data = json.loads(response.strip())
            
            # Validate emotion
            if data.get("emotion") not in EMOTION_STATES:
                data["emotion"] = "neutral"
            
            # Validate defensiveness
            if data.get("defensiveness") not in DEFENSIVENESS_LEVELS:
                data["defensiveness"] = "none"
                
            return UserState(**data)
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse state JSON: {e}")
            return UserState(reasoning="Failed to parse LLM response")


# ============== RULE-BASED FALLBACK ==============
# These patterns can supplement LLM inference for speed/reliability

DEFENSIVENESS_PATTERNS = {
    "high": [
        r"i don'?t have a problem",
        r"i can (stop|quit) (whenever|anytime)",
        r"you don'?t understand",
        r"mind your own business",
        r"leave me alone",
        r"it'?s (not|none of) your (business|concern)",
    ],
    "moderate": [
        r"everyone (does it|drinks)",
        r"it'?s not that (bad|serious)",
        r"i only (drink|have) a (little|few)",
        r"compared to others",
        r"at least i'?m not",
    ],
    "low": [
        r"i (guess|suppose) (maybe|perhaps)",
        r"but (still|anyway)",
        r"yeah,? but",
    ]
}

EMOTION_PATTERNS = {
    "frustrated": [r"ugh", r"whatever", r"again\??", r"tired of"],
    "anxious": [r"worried", r"scared", r"what if", r"nervous"],
    "sad": [r"hopeless", r"can'?t (do|change)", r"given up", r"no point"],
    "angry": [r"pissed", r"angry", r"mad at", r"hate"],
    "hopeful": [r"want to (try|change)", r"maybe i (can|could)", r"help me"],
}
