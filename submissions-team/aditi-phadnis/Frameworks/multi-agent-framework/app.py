import streamlit as st
from streamlit_chat import message
from langchain_openai import ChatOpenAI
from models import UserProfile
from orchestrator import Orchestrator
import pandas as pd
from app3 import generate_exercises_tab
import logging

logging.basicConfig(level=logging.DEBUG)
logging.debug("Starting app.py execution")



# Initialize the LLM
llm = ChatOpenAI(temperature=0.2, model="gpt-4-turbo", streaming=True)

# Create the orchestrator
orchestrator = Orchestrator(llm)

# Streamlit UI
def main():
    st.title("🌍 AI Language Tutor")
    st.sidebar.header("User Settings")
    
    # User profile inputs
    target_language = st.sidebar.selectbox("Target Language", ["French", "Spanish", "German", "Italian"])
    difficulty_level = st.sidebar.selectbox("Difficulty Level", ["Beginner", "Intermediate", "Advanced"])
    learning_focus = st.sidebar.selectbox("Learning Focus", ["Vocabulary", "Grammar", "Conversation"])
    
    # Initialize user profile
    user_profile = UserProfile(
        target_language=target_language,
        difficulty_level=difficulty_level,
        learning_focus=learning_focus
    )
    
    # Tabs for Chat and Exercises
    tab1, tab2 = st.tabs(["💬 Chat", "📚 Exercises"])
    
    with tab1:
        st.subheader("Chat with AI Tutor")
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        
        # Create a container for chat messages
        chat_container = st.container()
        with chat_container:
            for idx, (role, message_text) in enumerate(st.session_state.chat_history):
                message(message_text, is_user=(role == "user"), key=f"chat_{idx}")

        
        # Add spacing to push input to the bottom
        st.write("\n" * 10)
        
        # Chat input at the bottom
        user_input = st.chat_input("🗣️ Enter your message:")
        if user_input:
            response = orchestrator.handle_conversation(user_input, user_profile)
            st.session_state.chat_history.append(("user", user_input))
            st.session_state.chat_history.append(("bot", response))
            st.rerun()
    
    with tab2:
        st.subheader("Language Exercises")
        generate_exercises_tab(user_profile)  # ✅ Uses function from app3.py
        
    try:
        logging.debug("Entering main()")
        generate_exercises_tab(user_profile)  # This might be causing the error
        logging.debug("Successfully executed generate_exercises_tab")
    except Exception as e:
        logging.exception("Error in main(): %s", e)

        
        
if __name__ == "__main__":
    main()
