import os
import streamlit as st
from langchain.agents import AgentType
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.tools import Tool
from langchain.schema import SystemMessage
from langchain.prompts import MessagesPlaceholder, ChatPromptTemplate
import time
import openai
import re

import pygame
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from typing import Dict, Any
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI Model
llm = ChatOpenAI(temperature=0, 
                 model="gpt-4-turbo", 
                 streaming=True
                 )

# Define the prompt template correctly
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an AI language tutor that helps users learn languages through grammar corrections, translations, and phrase suggestions.
    Always translate non-English text to English before responding. After translation, provide a natural follow-up response to keep the conversation going."""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("user", "{input}"),  # User input placeholder
    ("assistant", "{agent_scratchpad}")  # Required for function calling
])



# 1️⃣ Grammar Correction Tool
def correct_grammar(text: str) -> str:
    prompt_template = PromptTemplate.from_template("Correct the following text: {text}\n\nCorrected:")
    grammar_chain = prompt_template | llm
    return grammar_chain.invoke({"text": text})

grammar_tool = Tool(
    name="Grammar Correction",
    func=correct_grammar,
    description="Fixes grammar errors in text."
)

# 2️⃣ Auto-Translation Tool (Detects & Translates)
def translate_to_english(text: str) -> str:
    """Detects if text is not in English and translates it automatically."""
    detection_prompt = PromptTemplate.from_template("Is the following text in English? Answer with 'yes' or 'no': {text}")
    detection_chain = detection_prompt | llm 
    is_english_response = detection_chain.invoke({"text": text})

    is_english = is_english_response.content.strip().lower() if hasattr(is_english_response, "content") else str(is_english_response).strip().lower()


    if is_english == "yes":
        return text  # Return original text if already English

    translation_prompt = PromptTemplate.from_template("Translate the following text to English: {text}\n\nEnglish:")
    translation_chain = translation_prompt | llm
    translated_response = translation_chain.invoke({"text": text})
    return translated_response.content if hasattr(translated_response, "content") else str(translated_response)


translation_tool = Tool(
    name="Translation",
    func=translate_to_english,
    description="Automatically detects and translates non-English text into English."
)

# 3️⃣ Follow-Up Response Generator

def detect_language(text: str) -> str:
    """Detects the language of the given text."""
    detection_prompt = PromptTemplate.from_template(
        "Identify the language of the following text. Respond with only the language name (e.g., French, Spanish, German): {text}"
    )
    detection_chain = detection_prompt | llm
    detected_response = detection_chain.invoke({"text": text})

    # ✅ Extract clean text
    detected_lang = detected_response.content if hasattr(detected_response, "content") else str(detected_response)
    return detected_lang.strip()

def generate_follow_up_response(translated_text: str, original_text: str) -> tuple:
    """Generates a natural follow-up response in both the detected language and English."""

    # ✅ Fix: Detect the original language inside this function
    detected_lang = detect_language(original_text)

    # Step 1: Generate follow-up in English
    response_prompt = PromptTemplate.from_template(
        "Given the following English text, suggest a natural follow-up response that continues the conversation:\n\n{text}"
    )
    response_chain = response_prompt | llm
    follow_up_response = response_chain.invoke({"text": translated_text})

    # ✅ Extract clean text from AIMessage
    follow_up_english = follow_up_response.content if hasattr(follow_up_response, "content") else str(follow_up_response)

    # Step 2: Translate follow-up back to original language
    back_translation_prompt = PromptTemplate.from_template(
    "Translate this English text back into {language}: {text}"
    )
    back_translation_chain = back_translation_prompt | llm
    follow_up_original_lang = back_translation_chain.invoke({"language": detected_lang, "text": follow_up_english})

    # Step 1: Generate follow-up in English
    follow_up_original = follow_up_original_lang.content if hasattr(follow_up_original_lang, "content") else str(follow_up_original_lang)

    return follow_up_english, follow_up_original, detected_lang


follow_up_tool = Tool(
    name="Follow-Up Generator",
    func=generate_follow_up_response,
    description="Suggests a natural response to continue the conversation."
)

# 4️⃣ Phrase Suggestion Tool
def suggest_phrase(topic: str, language: str) -> str:
    """Suggests a common phrase in the given language related to the topic."""
    prompt_template = PromptTemplate.from_template("Suggest a common phrase in {language} about {topic}.")
    phrase_chain = prompt_template | llm
    return phrase_chain.invoke({"topic": topic, "language": language})

phrase_suggestion_tool = Tool(
    name="Phrase Suggestion",
    func=suggest_phrase,
    description="Suggests common phrases in a specified language."
)

# Define Tools
tools = [grammar_tool, translation_tool, follow_up_tool, phrase_suggestion_tool]

# Set up conversation memory
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# System Message to Guide AI Behavior
system_message = SystemMessage(
    content="""You are an AI language tutor that helps users learn languages through grammar corrections, translations, 
    and phrase suggestions. 
    Always translate non-English text to English before responding. 
    After translation, provide a natural follow-up response to keep the conversation going."""
)

# Create Agent with OpenAI Functions
agent = create_openai_functions_agent(llm, tools, prompt )

agent_executor = AgentExecutor(agent=agent, tools=tools, memory=memory, verbose=True)

# 6️⃣ Text to speech using TTS from open AI 
def text_to_speech(text: str, filename: str):
    """Converts text to speech using OpenAI's TTS API and plays the audio."""
    try:
        response = openai.audio.speech.create(
            model="tts-1",
            voice="alloy",  # Natural-sounding voice
            input=text,
            speed=0.75  # Slower playback speed
        )

        # Save the TTS output
        with open(filename, "wb") as f:
            f.write(response.content)

        # Play the generated audio
        pygame.mixer.init()
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()
        time.sleep(3)  # Ensure audio plays before script exits

    except Exception as e:
        print(f"Error generating TTS: {e}")

# 🎵 Function to display an audio player
def play_audio(audio_file, label):
    """Creates an audio player in Streamlit for a given audio file (User-Triggered Playback)"""
    with open(audio_file, "rb") as audio:
        st.audio(audio, format="audio/mp3", start_time=0)


def clean_user_input(text: str) -> str:
    """Removes bracketed translations from user input."""
    return re.sub(r'\(.*?\)', '', text).strip()  # Removes anything in brackets


# 6️⃣ Streamlit UI
st.title("🌍 AI Polyglot") 
st.markdown("🌐 **A Language Tutor & Translator. Learn new languages with me!**")

user_input = st.text_area("Enter your text:", height=150)

if st.button("Process"):
    if user_input:
        try:
            st.write("### Translation & Response")

            user_input_cleaned = clean_user_input(user_input)  # ✅ Apply fix

            # Step 1: Process Input (Auto-Translate)
            translated_text = translate_to_english(user_input)
            st.markdown(f"**🔹 Translated:** {translated_text}")

            # Step 2: Suggest Follow-Up in both English & original language
            follow_up_english, follow_up_original, detected_lang = generate_follow_up_response(translated_text, user_input)

            # ✅ Generate TTS audio for all outputs
            text_to_speech(user_input_cleaned, "user_input.mp3")
            text_to_speech(translated_text, "translated_text.mp3")
            text_to_speech(follow_up_english, "follow_up_english.mp3")
            text_to_speech(follow_up_original, "follow_up_original.mp3")

            # ✅ Display text + 🎵 Audio Buttons
            st.markdown("**🗣️ User Input:**")
            st.markdown(f"📝 {user_input_cleaned}")
            play_audio("user_input.mp3", "User Input")  # ✅ Correct filename

            st.markdown("**🔹 Translated:**")
            st.markdown(f"📝 {translated_text}")
            play_audio("translated_text.mp3", "Translated Text")  # ✅ Correct filename

            st.markdown("**🗨️ Follow-Up Suggestion:**")
            st.markdown(f"🇬🇧 **English:** {follow_up_english}")
            play_audio("follow_up_english.mp3", "English Follow-Up")  # ✅ Correct filename

            st.markdown(f"🌍 **({detected_lang}) {follow_up_original}**")
            play_audio("follow_up_original.mp3", f"{detected_lang} Follow-Up")  # ✅ Correct filename

        except Exception as e:
            st.error(f"❌ An error occurred: {e}")
    else:
        st.warning("⚠️ Please enter some text to process.")


