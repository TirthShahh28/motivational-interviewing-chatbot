"""
Adaptive Response Generator
===========================
Generates empathetic, state-aware responses using:
1. Conversation context
2. Inferred user state (emotion + defensiveness)
3. Retrieved expert knowledge from RAG

Implements Motivational Interviewing principles:
- Express empathy
- Develop discrepancy
- Roll with resistance
- Support self-efficacy
"""

from typing import Optional
from loguru import logger

from src.state_inference import UserState


# ============== RESPONSE GENERATION PROMPTS ==============

SYSTEM_PROMPT = """You are a compassionate, non-judgmental conversational companion trained in Motivational Interviewing (MI) principles for alcohol-related discussions.

## Your Core Principles:
1. **Express Empathy**: Use reflective listening to show understanding
2. **Avoid Argumentation**: Never confront or lecture; roll with resistance
3. **Support Autonomy**: The person has the right to make their own choices
4. **Develop Discrepancy**: Gently help them see gaps between values and behavior
5. **Evoke Change Talk**: Encourage them to voice their own reasons for change

## What You MUST NOT Do:
- Provide medical advice or diagnoses
- Recommend specific medications or dosages
- Tell them what to do or issue ultimatums
- Judge their behavior or lifestyle
- Minimize their experiences
- Make promises about outcomes

## Your Communication Style:
- Warm, genuine, and conversational
- Use open-ended questions
- Offer reflections (simple and complex)
- Provide affirmations when appropriate
- Summarize periodically

Remember: Your goal is to be a supportive presence, not to "fix" them."""


RESPONSE_PROMPT_TEMPLATE = """## Current Conversation Context:
{conversation_history}

## User's Current State (detected):
- Emotion: {emotion}
- Defensiveness: {defensiveness}
- Reasoning: {state_reasoning}

## Relevant Expert Guidelines:
{retrieved_knowledge}

## Adaptive Response Instructions:
{state_instructions}

## User's Message:
"{user_message}"

## Your Task:
Generate a single, thoughtful response (2-4 sentences) that:
1. Acknowledges their emotional state appropriately
2. Uses MI techniques suitable for their defensiveness level
3. Incorporates relevant knowledge naturally (without quoting it directly)
4. Ends with either a reflection or open-ended question when appropriate

Response:"""


# State-specific instructions for response generation
STATE_INSTRUCTIONS = {
    "high_defensiveness": """
The user is showing HIGH DEFENSIVENESS. Critical guidelines:
- DO NOT challenge or confront their statements
- Use simple reflections (repeat/rephrase what they said)
- Emphasize their autonomy ("It's your choice...")
- Express understanding of their perspective
- Avoid questions that feel interrogating
- Example: "It sounds like you feel in control of your drinking."
""",
    
    "moderate_defensiveness": """
The user is showing MODERATE DEFENSIVENESS. Guidelines:
- Use double-sided reflections ("On one hand... on the other...")
- Acknowledge their point before exploring further
- Ask permission before sharing information
- Gently explore ambivalence
- Example: "You mentioned it helps you relax, and also that your partner worries..."
""",
    
    "low_defensiveness": """
The user is showing LOW DEFENSIVENESS. They may be more open. Guidelines:
- Use complex reflections that add meaning
- Explore their values and goals
- Look for and reinforce "change talk"
- Can ask more exploratory questions
- Example: "It sounds like being present for your kids is really important to you."
""",
    
    "no_defensiveness": """
The user appears OPEN and receptive. Guidelines:
- Support and affirm their openness
- Explore what change might look like
- Discuss strategies if they're interested
- Reinforce their self-efficacy
- Example: "You've clearly been thinking about this. What do you think would be a good first step?"
""",
    
    "frustrated_emotion": "- Validate their frustration first before anything else",
    "anxious_emotion": "- Provide reassurance and normalize their concerns",
    "sad_emotion": "- Sit with them emotionally; don't rush to solutions",
    "angry_emotion": "- Do not match their energy; stay calm and validating",
    "hopeful_emotion": "- Support and elaborate on their hope; explore it further",
}


class ResponseGenerator:
    """
    Generates contextually appropriate responses based on user state.
    
    Combines conversation history, inferred state, and retrieved
    knowledge to produce empathetic, MI-aligned responses.
    """
    
    def __init__(self, llm_client):
        """
        Initialize the response generator.
        
        Args:
            llm_client: LangChain LLM instance
        """
        self.llm = llm_client
        logger.info("ResponseGenerator initialized")
    
    def generate(
        self,
        user_message: str,
        user_state: UserState,
        conversation_history: list[dict],
        retrieved_knowledge: list[dict]
    ) -> str:
        """
        Generate an adaptive response.
        
        Args:
            user_message: Current user input
            user_state: Inferred emotional/defensive state
            conversation_history: Previous conversation turns
            retrieved_knowledge: Relevant knowledge from RAG
            
        Returns:
            Generated response string
        """
        # Format conversation history
        history_str = self._format_history(conversation_history)
        
        # Format retrieved knowledge
        knowledge_str = self._format_knowledge(retrieved_knowledge)
        
        # Get state-specific instructions
        instructions = self._get_state_instructions(user_state)
        
        # Build the full prompt
        prompt = RESPONSE_PROMPT_TEMPLATE.format(
            conversation_history=history_str,
            emotion=user_state.emotion,
            defensiveness=user_state.defensiveness,
            state_reasoning=user_state.reasoning,
            retrieved_knowledge=knowledge_str,
            state_instructions=instructions,
            user_message=user_message
        )
        
        try:
            # Generate with system prompt
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            
            response = self.llm.invoke(messages)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Clean up response
            response_text = response_text.strip()
            
            logger.debug(f"Generated response: {response_text[:100]}...")
            return response_text
            
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return "I hear you. Tell me more about what's on your mind."
    
    def _format_history(self, history: list[dict]) -> str:
        """Format conversation history for the prompt."""
        if not history:
            return "This is the start of the conversation."
        
        formatted = []
        for turn in history[-6:]:  # Last 6 turns (3 exchanges)
            role = "User" if turn.get("role") == "user" else "Assistant"
            content = turn.get("content", "")
            formatted.append(f"{role}: {content}")
        
        return "\n".join(formatted)
    
    def _format_knowledge(self, knowledge: list[dict]) -> str:
        """Format retrieved knowledge chunks."""
        if not knowledge:
            return "No specific guidelines retrieved. Use general MI principles."
        
        formatted = []
        for i, chunk in enumerate(knowledge, 1):
            content = chunk.get("content", "")
            source = chunk.get("source", "Expert Guidelines")
            formatted.append(f"[{i}] {content}")
        
        return "\n\n".join(formatted)
    
    def _get_state_instructions(self, state: UserState) -> str:
        """Get tailored instructions based on user state."""
        instructions = []
        
        # Defensiveness instructions
        if state.defensiveness == "high":
            instructions.append(STATE_INSTRUCTIONS["high_defensiveness"])
        elif state.defensiveness == "moderate":
            instructions.append(STATE_INSTRUCTIONS["moderate_defensiveness"])
        elif state.defensiveness == "low":
            instructions.append(STATE_INSTRUCTIONS["low_defensiveness"])
        else:
            instructions.append(STATE_INSTRUCTIONS["no_defensiveness"])
        
        # Emotion instructions
        emotion_key = f"{state.emotion}_emotion"
        if emotion_key in STATE_INSTRUCTIONS:
            instructions.append(STATE_INSTRUCTIONS[emotion_key])
        
        return "\n".join(instructions)
