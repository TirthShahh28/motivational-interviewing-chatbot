"""
Safety Layer
============
Implements safety guardrails to ensure the chatbot:
1. Never provides medical advice
2. Detects crisis situations (self-harm, suicidal ideation)
3. Provides appropriate resources when needed
4. Logs safety-flagged interactions for review

This is a CRITICAL component - safety must be non-negotiable.
"""

import re
from typing import Tuple, Optional
from enum import Enum
from loguru import logger

from src.config import SAFETY_RED_FLAGS, RESTRICTED_TOPICS


class SafetyLevel(Enum):
    """Safety classification levels."""
    SAFE = "safe"
    CAUTION = "caution"  # Needs monitoring but can continue
    CRISIS = "crisis"    # Requires immediate intervention/resources
    BLOCKED = "blocked"  # Response should not be generated


class SafetyCheckResult:
    """Result of a safety check."""
    
    def __init__(
        self,
        level: SafetyLevel,
        triggered_flags: list[str] = None,
        should_intervene: bool = False,
        intervention_message: str = None,
        should_log: bool = False
    ):
        self.level = level
        self.triggered_flags = triggered_flags or []
        self.should_intervene = should_intervene
        self.intervention_message = intervention_message
        self.should_log = should_log


# Crisis intervention message
CRISIS_RESPONSE = """I'm concerned about what you've shared. Your safety is important.

If you're having thoughts of hurting yourself, please reach out:
- **National Suicide Prevention Lifeline**: 988 (call or text)
- **Crisis Text Line**: Text HOME to 741741
- **SAMHSA National Helpline**: 1-800-662-4357

I'm here to talk, but please also consider reaching out to one of these resources where trained professionals can provide immediate support.

Would you like to tell me more about what you're going through?"""


# Message when bot detects it's being asked for medical advice
MEDICAL_BOUNDARY_RESPONSE = """I appreciate you trusting me with this question, but I'm not able to provide medical advice or recommendations about medications, dosages, or treatments.

For medical questions, please consult with:
- Your doctor or healthcare provider
- A pharmacist
- SAMHSA's National Helpline: 1-800-662-4357 (free, confidential, 24/7)

I'm happy to continue talking about how you're feeling and what you're going through."""


class SafetyGuard:
    """
    Implements safety checks on both input and output.
    
    Two-stage safety:
    1. Input screening: Check user message for crisis indicators
    2. Output screening: Ensure bot response doesn't violate boundaries
    """
    
    def __init__(self):
        """Initialize safety patterns."""
        # Compile regex patterns for efficiency
        self.crisis_patterns = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in SAFETY_RED_FLAGS
        ]
        
        self.medical_patterns = [
            re.compile(rf'\b{topic}\b', re.IGNORECASE)
            for topic in RESTRICTED_TOPICS
        ]
        
        # Patterns for detecting requests for medical advice
        self.advice_request_patterns = [
            re.compile(r'(should i|can i) (take|stop|reduce|increase)', re.IGNORECASE),
            re.compile(r'how (much|many|often) (should|can) i', re.IGNORECASE),
            re.compile(r'what (medication|medicine|drug) (should|can|would)', re.IGNORECASE),
            re.compile(r'(prescribe|prescription)', re.IGNORECASE),
            re.compile(r'is it (safe|okay|dangerous) to', re.IGNORECASE),
        ]
        
        logger.info("SafetyGuard initialized")
    
    def check_input(self, user_message: str) -> SafetyCheckResult:
        """
        Screen user input for safety concerns.
        
        Args:
            user_message: The user's message
            
        Returns:
            SafetyCheckResult with appropriate level and intervention
        """
        message_lower = user_message.lower()
        triggered = []
        
        # Check for crisis indicators
        for pattern in self.crisis_patterns:
            if pattern.search(message_lower):
                triggered.append(pattern.pattern)
        
        if triggered:
            logger.warning(f"CRISIS DETECTED: {triggered}")
            return SafetyCheckResult(
                level=SafetyLevel.CRISIS,
                triggered_flags=triggered,
                should_intervene=True,
                intervention_message=CRISIS_RESPONSE,
                should_log=True
            )
        
        # Check for medical advice requests
        for pattern in self.advice_request_patterns:
            if pattern.search(message_lower):
                triggered.append(pattern.pattern)
        
        for pattern in self.medical_patterns:
            if pattern.search(message_lower):
                triggered.append(pattern.pattern)
        
        if triggered:
            logger.info(f"Medical boundary triggered: {triggered}")
            return SafetyCheckResult(
                level=SafetyLevel.CAUTION,
                triggered_flags=triggered,
                should_intervene=True,
                intervention_message=MEDICAL_BOUNDARY_RESPONSE,
                should_log=True
            )
        
        return SafetyCheckResult(level=SafetyLevel.SAFE)
    
    def check_output(self, response: str) -> SafetyCheckResult:
        """
        Screen bot output before sending to user.
        
        Ensures the bot hasn't generated:
        - Medical advice
        - Harmful content
        - Inappropriate recommendations
        
        Args:
            response: The generated bot response
            
        Returns:
            SafetyCheckResult indicating if response is safe to send
        """
        response_lower = response.lower()
        triggered = []
        
        # Check for medical advice patterns in response
        medical_advice_indicators = [
            r'you should (take|stop|reduce)',
            r'i (recommend|suggest|advise) (taking|stopping)',
            r'(mg|milligram|dose|dosage)',
            r'(prescription|medication) for',
        ]
        
        for pattern in medical_advice_indicators:
            if re.search(pattern, response_lower):
                triggered.append(pattern)
        
        if triggered:
            logger.warning(f"Output blocked - medical advice detected: {triggered}")
            return SafetyCheckResult(
                level=SafetyLevel.BLOCKED,
                triggered_flags=triggered,
                should_log=True
            )
        
        return SafetyCheckResult(level=SafetyLevel.SAFE)
    
    def get_safe_response(self, check_result: SafetyCheckResult) -> str:
        """
        Get an appropriate response based on safety check result.
        
        Args:
            check_result: Result from safety check
            
        Returns:
            Safe response string
        """
        if check_result.should_intervene and check_result.intervention_message:
            return check_result.intervention_message
        
        # Default fallback
        return "I hear you. Can you tell me more about how you're feeling?"


class ConversationLogger:
    """
    Logs conversations for expert review.
    
    Especially important for:
    - Safety-flagged interactions
    - Quality assurance
    - Training data collection (with consent)
    """
    
    def __init__(self, log_dir):
        """Initialize logger with output directory."""
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
    def log_interaction(
        self,
        session_id: str,
        user_message: str,
        bot_response: str,
        user_state: dict,
        safety_level: SafetyLevel,
        retrieved_knowledge: list = None
    ):
        """
        Log a single interaction.
        
        Args:
            session_id: Unique session identifier
            user_message: What the user said
            bot_response: What the bot responded
            user_state: Inferred state dict
            safety_level: Safety classification
            retrieved_knowledge: RAG results used
        """
        import json
        from datetime import datetime
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "user_message": user_message,
            "bot_response": bot_response,
            "inferred_state": user_state,
            "safety_level": safety_level.value,
            "retrieved_knowledge": retrieved_knowledge or []
        }
        
        # Write to session log file
        log_file = self.log_dir / f"{session_id}.jsonl"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        # If safety flagged, also write to separate review file
        if safety_level in [SafetyLevel.CRISIS, SafetyLevel.CAUTION]:
            review_file = self.log_dir / "flagged_for_review.jsonl"
            with open(review_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
            logger.warning(f"Interaction flagged for review: {session_id}")
