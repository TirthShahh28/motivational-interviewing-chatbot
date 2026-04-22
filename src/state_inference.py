"""
State Inference Module
======================
Analyzes user input to detect emotional state and defensiveness level.
Uses LLM-based classification with structured output.

This is the core module that makes the chatbot "aware" of user psychological state.
"""

import json
import re
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
    
    def __init__(self, llm_client, use_rule_based: bool = False):
        """
        Initialize the state inference engine.

        Args:
            llm_client: LangChain LLM instance (Ollama or OpenAI)
            use_rule_based: If True, skip LLM and use fast rule-based inference
        """
        self.llm = llm_client
        self.use_rule_based = use_rule_based
        mode = "rule-based (fast)" if use_rule_based else "LLM-based"
        logger.info(f"StateInferenceEngine initialized ({mode})")

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
        
        # Fast path: rule-based inference (no LLM call, ~0ms)
        if self.use_rule_based:
            return self._infer_state_rule_based(user_message)

        try:
            # Call LLM
            response = self.llm.invoke(prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)

            # Parse JSON response
            state = self._parse_response(response_text)
            logger.debug(f"Inferred state: {state}")
            return state

        except Exception as e:
            logger.error(f"LLM state inference failed: {e}. Using rule-based fallback.")
            return self._infer_state_rule_based(user_message)
    
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
        import re
        try:
            # Robust JSON extraction: try markdown code block first
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find raw JSON object in response
                brace_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
                if brace_match:
                    json_str = brace_match.group(0)
                else:
                    json_str = response.strip()

            data = json.loads(json_str)

            # Validate and clamp fields
            emotion = data.get("emotion", "neutral")
            if emotion not in EMOTION_STATES:
                emotion = "neutral"

            defensiveness = data.get("defensiveness", "none")
            if defensiveness not in DEFENSIVENESS_LEVELS:
                defensiveness = "none"

            confidence = data.get("confidence", 0.5)
            try:
                confidence = max(0.0, min(1.0, float(confidence)))
            except (TypeError, ValueError):
                confidence = 0.5

            return UserState(
                emotion=emotion,
                defensiveness=defensiveness,
                confidence=confidence,
                reasoning=data.get("reasoning", ""),
                linguistic_markers=data.get("linguistic_markers", [])
            )

        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.warning(f"Failed to parse state JSON: {e}. Response: {response[:200]}")
            return UserState(reasoning="Failed to parse LLM response")


    def _infer_state_rule_based(self, user_message: str) -> UserState:
        """Powerful rule-based inference using weighted pattern scoring."""
        # Normalize: smart quotes → straight, strip extra whitespace
        message_lower = user_message.lower()
        message_lower = message_lower.replace('\u2018', "'").replace('\u2019', "'")
        message_lower = message_lower.replace('\u201c', '"').replace('\u201d', '"')
        markers = []

        # --- DEFENSIVENESS: score-based, highest wins ---
        defense_scores = {"none": 0, "low": 0, "moderate": 0, "high": 0}
        for level, patterns in DEFENSIVENESS_PATTERNS.items():
            for pattern, weight in patterns:
                if re.search(pattern, message_lower):
                    defense_scores[level] += weight
                    markers.append(re.search(pattern, message_lower).group())

        # Pick highest scoring level (tie-break: higher severity wins)
        severity_order = ["high", "moderate", "low", "none"]
        defensiveness = max(severity_order, key=lambda l: (defense_scores[l], severity_order.index(l) * -1))
        if defense_scores[defensiveness] == 0:
            defensiveness = "none"

        # --- EMOTION: score-based, highest wins ---
        emotion_scores = {e: 0 for e in EMOTION_PATTERNS}
        for emo, patterns in EMOTION_PATTERNS.items():
            for pattern, weight in patterns:
                if re.search(pattern, message_lower):
                    emotion_scores[emo] += weight
                    markers.append(re.search(pattern, message_lower).group())

        # Pick highest scoring emotion
        best_emotion = max(emotion_scores, key=emotion_scores.get)
        emotion = best_emotion if emotion_scores[best_emotion] > 0 else "neutral"

        # --- CONTEXTUAL BOOSTERS ---
        # Drinking + negative context = likely coping
        drinking_words = re.search(r'\b(drink|drinking|drunk|beer|wine|vodka|alcohol|booze|wasted|hammered|shots?)\b', message_lower)
        coping_context = re.search(r'\b(because|coz|cuz|since|after|due to|cope|deal with|forget|numb|escape|not think|block out|drown)\b', message_lower)
        negative_event = re.search(r'\b(fail|failed|failing|exams?|grades?|poor|bad|lost|fired|broke|lonely|alone|fight|argued|divorce|breakup|stress)\b', message_lower)

        if drinking_words and coping_context:
            # Drinking to cope → boost sad if no stronger emotion
            if emotion == "neutral":
                emotion = "sad"
                markers.append("drinking-to-cope pattern")
            if defensiveness == "none":
                defensiveness = "low"

        if drinking_words and negative_event:
            if emotion == "neutral":
                emotion = "sad"
                markers.append("drinking + negative event")

        # Forced/coerced to be here → angry
        if re.search(r"(made|forced|dragged) me (come|be here|do this)", message_lower):
            if emotion == "neutral":
                emotion = "angry"
                markers.append("coerced attendance")

        # "it's my life" + judging/telling = high defensiveness
        if re.search(r"(my life|my choice|my decision)", message_lower) and defensiveness in ("none", "low", "moderate"):
            defense_scores["high"] += 2
            defensiveness = "high"
            markers.append("autonomy assertion")

        # Exclamation marks / ALL CAPS → anger/frustration boost
        if user_message.count('!') >= 2 or (len(user_message) > 10 and user_message.upper() == user_message):
            if emotion == "neutral":
                emotion = "frustrated"
                markers.append("high intensity punctuation/caps")
            elif emotion in ("frustrated", "angry"):
                if defensiveness in ("none", "low"):
                    defensiveness = "moderate"

        # Question marks about self → contemplative
        if re.search(r"\b(why do i|what('?s| is) wrong with me|am i|should i)\b", message_lower):
            if emotion in ("neutral", "sad"):
                emotion = "contemplative"
                markers.append("self-questioning")

        # Confidence based on how many markers matched
        total_matches = len(markers)
        confidence = min(0.9, 0.4 + (total_matches * 0.15))

        reasoning_parts = []
        if emotion != "neutral":
            reasoning_parts.append(f"Detected {emotion} emotion")
        if defensiveness != "none":
            reasoning_parts.append(f"{defensiveness} defensiveness")
        if markers:
            reasoning_parts.append(f"markers: {', '.join(markers[:3])}")
        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "No strong signals detected"

        return UserState(
            emotion=emotion,
            defensiveness=defensiveness,
            confidence=confidence,
            reasoning=reasoning,
            linguistic_markers=markers[:5]
        )


# ============== WEIGHTED RULE-BASED PATTERNS ==============
# Format: (regex_pattern, weight) — higher weight = stronger signal

DEFENSIVENESS_PATTERNS = {
    "high": [
        (r"i don'?t have (a |an? \w+ )?problem", 3),
        (r"(not|no) a problem", 2),
        (r"i (can|could) (stop|quit) (whenever|anytime|if i wanted)", 3),
        (r"you don'?t (understand|know|get it)", 2),
        (r"mind your own business", 3),
        (r"leave me alone", 2),
        (r"it'?s (not|none of) your (business|concern)", 3),
        (r"who are you to (judge|tell|say)", 3),
        (r"there'?s nothing wrong", 2),
        (r"i'?m (perfectly |totally )?fine", 2),
        (r"i don'?t (need|want) (any )?(help|this|therapy|counseling)", 3),
        (r"you'?re (making|blowing) .* (up|deal)", 2),
        (r"so what if i drink", 2),
        (r"it'?s my (life|choice|body|decision)", 2),
        (r"back off", 3),
        (r"stop (telling|asking|pushing|nagging)", 2),
        (r"i know what i'?m doing", 2),
        (r"(made|forced) me (come|be here|do this)", 2),
        (r"(don'?t|didn'?t) (want|need|ask) to (be here|come|do this)", 2),
        (r"why (am i|do i have to be) here", 2),
        (r"this is (stupid|pointless|waste|dumb|useless)", 2),
    ],
    "moderate": [
        (r"everyone (does it|drinks|parties)", 2),
        (r"it'?s not that (bad|serious|much|big)", 2),
        (r"i only (drink|have) a (little|few|couple)", 2),
        (r"compared to (others|most|my friends)", 2),
        (r"at least i'?m not", 2),
        (r"i (just|only) drink (socially|on weekends|sometimes)", 2),
        (r"it'?s (just|only) (beer|wine|a drink|a couple)", 2),
        (r"i (can|do) handle (it|my|myself)", 1),
        (r"it helps me (relax|unwind|sleep|cope|deal)", 2),
        (r"i'?ve (got|have) it under control", 2),
        (r"it'?s not like i (drink|do it) every day", 2),
        (r"plenty of people drink more than me", 2),
        (r"i (barely|hardly) drink", 1),
        (r"what'?s the (big )?deal", 2),
        (r"you'?re over ?react", 1),
        (r"(don'?t|didn'?t even) know why .*(here|came|coming)", 2),
        (r"(judging|judge) me", 2),
        (r"telling me what to do", 2),
    ],
    "low": [
        (r"i (guess|suppose) (maybe|perhaps)?", 1),
        (r"\bbut (still|anyway|like)\b", 1),
        (r"\byeah,? but\b", 1),
        (r"i (mean|know),? but", 1),
        (r"i (don'?t|didn'?t) (think|mean|realize)", 1),
        (r"it'?s (complicated|not that simple|hard to explain)", 1),
        (r"i'?m not (sure|ready|convinced)", 1),
    ]
}

EMOTION_PATTERNS = {
    "frustrated": [
        (r"\bugh+\b", 2), (r"\bwhatever\b", 2),
        (r"tired of", 2), (r"sick (of|and tired)", 2), (r"fed up", 2),
        (r"nothing (works|helps|changes)", 2), (r"i (keep|always) (doing|failing|messing)", 2),
        (r"what'?s the (point|use)", 2), (r"same (thing|crap|stuff) (over|again)", 2),
        (r"no matter what i (do|try)", 2), (r"i can'?t (win|get ahead)", 1),
        (r"(this|it) (sucks|is bs|is stupid)", 2), (r"every ?time", 1),
    ],
    "anxious": [
        (r"\bworried\b", 2), (r"\bscared\b", 2), (r"\bwhat if\b", 2),
        (r"\bnervous\b", 2), (r"\bpanic", 2), (r"\bafraid\b", 2),
        (r"i (can'?t|couldn'?t) (sleep|stop thinking|relax)", 2),
        (r"keeps? me (up|awake)", 1), (r"racing (thoughts|mind)", 2),
        (r"something (bad|terrible|awful) (will|might|could)", 2),
        (r"i don'?t know what (to do|will happen)", 1),
        (r"freaking out", 2), (r"on edge", 2), (r"overwhelming", 2),
        (r"(stress|anxiet)", 2), (r"can'?t (breathe|calm down)", 2),
    ],
    "sad": [
        (r"\bhopeless\b", 3), (r"can'?t (do|change|go on|take)", 2),
        (r"given up", 2), (r"no point", 2), (r"\bdepressed\b", 3),
        (r"\blonely\b", 2), (r"\bempty\b", 2), (r"\bmiserable\b", 2),
        (r"(feel|feeling) (down|low|bad|terrible|awful|horrible)", 2),
        (r"i (hate|don'?t like) my(self| life)", 3),
        (r"(cry|crying|cried|tears)", 2), (r"i (miss|lost|losing)", 2),
        (r"(nobody|no ?one) (cares|loves|understands)", 2),
        (r"(everything|life|it) (is|feels) (pointless|meaningless|empty)", 3),
        (r"i'?m (a )?(failure|loser|mess|wreck|disaster)", 2),
        (r"(poor|bad|failing|failed) (grades?|marks?|scores?|exam|test|results?)", 2),
        (r"(don'?t|didn'?t) (pass|make it|get in|succeed)", 2),
        (r"let (everyone|them|myself|my family|my parents) down", 2),
        (r"disappointed (in|with) my ?self", 2),
        (r"\bregret\b", 1), (r"\bashamed\b", 2), (r"\bguilty\b", 2),
        (r"not good enough", 2), (r"worthless", 3),
    ],
    "angry": [
        (r"\bpissed\b", 3), (r"\bangry\b", 2), (r"\bmad at\b", 2),
        (r"\bhate\b", 2), (r"\bfurious\b", 3), (r"\brage\b", 3),
        (r"(piss|tick|freak) me off", 2), (r"\bscrew (this|that|it|you)\b", 3),
        (r"\bf+u+c+k+", 3), (r"\bbs\b", 1), (r"\bdamn\b", 1),
        (r"(want|wanna|going) to (hit|punch|break|smash|scream)", 2),
        (r"i'?m (so |really )?(sick|tired) of (this|them|everything)", 2),
        (r"(they|he|she|you) (made|forced|pushed|drove) me", 2),
        (r"it'?s (their|his|her|your) fault", 2),
        (r"(unfair|unjust|wrong|bull)", 2),
        (r"(telling|judging|pushing|nagging|lecturing) me", 2),
        (r"(everyone|people|they) keep", 2),
        (r"(why does|why do) everyone", 2),
        (r"(sick of|tired of) people", 2),
        (r"it'?s my life", 2),
        (r"who (asked|cares)", 2),
    ],
    "hopeful": [
        (r"want to (try|change|quit|stop|cut back|do better)", 2),
        (r"maybe i (can|could|should)", 2), (r"help me", 2),
        (r"i'?m (ready|willing|open) (to|for)", 2),
        (r"i (want|need) to (change|do something|get better)", 2),
        (r"(things|it) (can|could|will|might) get better", 2),
        (r"i (believe|think|hope) i can", 2),
        (r"what (can|should) i do", 2), (r"how (can|do) i (change|stop|quit|improve)", 2),
        (r"i'?ve been thinking about (stopping|cutting|changing|quitting)", 2),
        (r"i (don'?t want|refuse) to (keep|continue|live) (like this|this way)", 2),
        (r"first step", 2), (r"new start", 1), (r"turning point", 2),
    ],
    "contemplative": [
        (r"i'?ve been (thinking|wondering|considering)", 2),
        (r"(on one hand|on the other|part of me)", 2),
        (r"i (don'?t|do) know (if|whether|what)", 1),
        (r"(pros? and cons?|weighing|trade.?off)", 2),
        (r"(sometimes|some days) i (think|feel|wonder)", 2),
        (r"i'?m (torn|conflicted|ambivalent|unsure)", 2),
        (r"is (it|this) (worth|even)", 1),
        (r"i wonder (if|what|whether|how)", 2),
        (r"what (if|would happen|else) .*(supposed|do)", 2),
        (r"(would be|be) different (if|without)", 2),
        (r"then again", 2),
        (r"but (then|what|how)", 1),
    ],
}
