"""
Streamlit UI for Emotion-Aware Alcohol Dialogue Chatbot
=======================================================
MVP Web Interface

Features:
- Chat interface with message history
- Real-time state display (emotion + defensiveness)
- Session management
- Debug panel for development
"""

import streamlit as st
from loguru import logger
import sys

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")

# Page configuration
st.set_page_config(
    page_title="Supportive Conversation",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for chat styling
st.markdown("""
<style>
    .user-message {
        background-color: #e3f2fd;
        padding: 10px 15px;
        border-radius: 15px;
        margin: 5px 0;
        max-width: 80%;
        margin-left: auto;
    }
    .bot-message {
        background-color: #f5f5f5;
        padding: 10px 15px;
        border-radius: 15px;
        margin: 5px 0;
        max-width: 80%;
    }
    .state-badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 10px;
        font-size: 12px;
        margin: 2px;
    }
    .emotion-badge {
        background-color: #fff3e0;
        color: #e65100;
    }
    .defense-badge {
        background-color: #fce4ec;
        color: #c2185b;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    
    if "conversation_manager" not in st.session_state:
        st.session_state.conversation_manager = None
    
    if "show_debug" not in st.session_state:
        st.session_state.show_debug = False
    
    if "last_state" not in st.session_state:
        st.session_state.last_state = None


def load_conversation_manager():
    """Load or create the conversation manager."""
    if st.session_state.conversation_manager is None:
        with st.spinner("Initializing chatbot..."):
            try:
                from src.conversation_manager import create_conversation_manager
                st.session_state.conversation_manager = create_conversation_manager(
                    use_ollama=True  # Set to False to use OpenAI
                )
                st.success("Chatbot initialized!")
            except Exception as e:
                st.error(f"Failed to initialize: {e}")
                st.info("Make sure Ollama is running with: `ollama run llama3`")
                return None
    
    return st.session_state.conversation_manager


def render_sidebar():
    """Render the sidebar with controls and info."""
    with st.sidebar:
        st.title("💬 Support Chat")
        st.markdown("---")
        
        # Session controls
        st.subheader("Session")
        if st.button("🔄 New Conversation", use_container_width=True):
            st.session_state.messages = []
            st.session_state.session_id = None
            st.session_state.last_state = None
            st.rerun()
        
        # Current state display
        if st.session_state.last_state:
            st.markdown("---")
            st.subheader("Detected State")
            state = st.session_state.last_state
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Emotion", state.get("emotion", "—").title())
            with col2:
                st.metric("Defensiveness", state.get("defensiveness", "—").title())
            
            if state.get("reasoning"):
                st.caption(f"💭 {state.get('reasoning')}")
        
        # Debug toggle
        st.markdown("---")
        st.subheader("Developer")
        st.session_state.show_debug = st.toggle("Show Debug Info", value=st.session_state.show_debug)
        
        # Info
        st.markdown("---")
        st.caption("""
        **About this chatbot:**
        
        This is a supportive conversational companion 
        that uses Motivational Interviewing principles.
        
        It is NOT a replacement for professional help.
        
        **Crisis Resources:**
        - 988 Suicide & Crisis Lifeline
        - SAMHSA: 1-800-662-4357
        """)


def render_chat_messages():
    """Render the chat message history."""
    for message in st.session_state.messages:
        role = message["role"]
        content = message["content"]
        
        with st.chat_message(role):
            st.markdown(content)
            
            # Show state info in debug mode
            if st.session_state.show_debug and role == "user" and "state" in message:
                state = message["state"]
                if state:
                    st.caption(
                        f"🎭 {state.get('emotion', '?')} | "
                        f"🛡️ {state.get('defensiveness', '?')} | "
                        f"📚 {message.get('knowledge_count', 0)} docs"
                    )


def process_user_input(user_input: str):
    """Process user input and get bot response."""
    cm = st.session_state.conversation_manager
    
    if cm is None:
        st.error("Chatbot not initialized")
        return
    
    # Add user message to display
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })
    
    # Process through pipeline
    with st.spinner("Thinking..."):
        try:
            result = cm.process_message(
                user_input,
                session_id=st.session_state.session_id
            )
            
            # Update session ID
            st.session_state.session_id = result["session_id"]
            
            # Update last state
            if result.get("user_state"):
                st.session_state.last_state = result["user_state"].model_dump()
                st.session_state.messages[-1]["state"] = st.session_state.last_state
                st.session_state.messages[-1]["knowledge_count"] = len(
                    result.get("retrieved_knowledge", [])
                )
            
            # Add bot response
            st.session_state.messages.append({
                "role": "assistant",
                "content": result["response"]
            })
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            st.session_state.messages.append({
                "role": "assistant",
                "content": "I'm having trouble responding right now. Can you try again?"
            })


def render_debug_panel(result: dict = None):
    """Render debug information panel."""
    if not st.session_state.show_debug:
        return
    
    with st.expander("🔧 Debug Panel", expanded=False):
        if st.session_state.last_state:
            st.json(st.session_state.last_state)
        
        st.caption(f"Session ID: {st.session_state.session_id}")
        st.caption(f"Messages: {len(st.session_state.messages)}")


def main():
    """Main application entry point."""
    initialize_session_state()
    
    # Render sidebar
    render_sidebar()
    
    # Main chat area
    st.title("How are you doing today?")
    st.caption("I'm here to listen without judgment. Share what's on your mind.")
    
    # Load conversation manager
    cm = load_conversation_manager()
    
    # Render existing messages
    render_chat_messages()
    
    # Debug panel
    render_debug_panel()
    
    # Chat input
    if user_input := st.chat_input("Type your message..."):
        process_user_input(user_input)
        st.rerun()


if __name__ == "__main__":
    main()
