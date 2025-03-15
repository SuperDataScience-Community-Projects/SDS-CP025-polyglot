import streamlit as st
import json
import time
from typing import Dict, Any, List
import pandas as pd
import random

def render_exercise_ui(exercises: Dict[str, Any]):
    """Render interactive exercise UI based on exercise data"""
    if not exercises:
        st.warning("Please generate exercises first.")
        return
    
    # Create tabs for different exercise types
    primary_type = exercises.get("primary", {}).get("type", "")
    secondary_type = exercises.get("secondary", {}).get("type", "")
    
    exercise_tabs = st.tabs([f"📝 {primary_type}", f"🔄 {secondary_type}", "📊 Progress"])
    
    with exercise_tabs[0]:
        render_exercise_section(exercises["primary"])
        
    with exercise_tabs[1]:
        render_exercise_section(exercises["secondary"])
        
    with exercise_tabs[2]:
        render_progress_tracker()

def render_exercise_section(section: Dict[str, Any]):
    """Render a specific exercise section"""
    exercise_type = section.get("type", "")
    exercises = section.get("exercises", [])
    
    if not exercises:
        st.write("No exercises available.")
        return
    
    st.subheader(f"{exercise_type} Exercises")
    
    # Render based on exercise type
    if exercise_type == "Vocabulary":
        render_vocabulary_exercise(exercises)
    elif exercise_type == "Grammar":
        render_grammar_exercise(exercises)
    elif exercise_type == "Conversation":
        render_conversation_exercise(exercises[0] if exercises else {})
    elif exercise_type == "Reading":
        render_reading_exercise(exercises[0] if exercises else {})
    elif exercise_type == "Listening":
        render_listening_exercise(exercises)
    elif exercise_type == "Multiple Choice":
        render_multiple_choice(exercises)
    else:
        st.write(f"Exercise type '{exercise_type}' not supported yet.")

def render_vocabulary_exercise(exercises: List[Dict]):
    """Render interactive vocabulary exercises"""
    word_container = st.container()
    
    # Initialize session state for vocabulary
    if "vocab_index" not in st.session_state:
        st.session_state.vocab_index = 0
        st.session_state.vocab_revealed = False
        st.session_state.vocab_score = 0
        st.session_state.vocab_attempts = 0
    
    # Control buttons for navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("← Previous", disabled=st.session_state.vocab_index <= 0):
            st.session_state.vocab_index -= 1
            st.session_state.vocab_revealed = False
            st.rerun()
    
    with col3:
        if st.button("Next →", disabled=st.session_state.vocab_index >= len(exercises) - 1):
            st.session_state.vocab_index += 1
            st.session_state.vocab_revealed = False
            st.rerun()
    
    # Display current word
    with word_container:
        if exercises and 0 <= st.session_state.vocab_index < len(exercises):
            word = exercises[st.session_state.vocab_index]
            
            st.markdown(f"### {st.session_state.vocab_index + 1}/{len(exercises)}: {word['word']}")
            
            # User guess section
            user_translation = st.text_input("Translation:", key=f"vocab_{st.session_state.vocab_index}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Check Answer", key=f"check_{st.session_state.vocab_index}"):
                    st.session_state.vocab_attempts += 1
                    if user_translation.lower().strip() == word['translation'].lower().strip():
                        st.success("Correct! 🎉")
                        st.session_state.vocab_score += 1
                    else:
                        st.error("Not quite. Try again or reveal the answer.")
            
            with col2:
                if st.button("Reveal Answer", key=f"reveal_{st.session_state.vocab_index}"):
                    st.session_state.vocab_revealed = True
            
            # Show answer details
            if st.session_state.vocab_revealed:
                st.info(f"Translation: {word['translation']}")
                st.markdown(f"**Example:** {word['example']}")
                st.markdown(f"**Translation:** {word['exampleTranslation']}")
    
    # Progress indicator
    st.progress((st.session_state.vocab_index + 1) / len(exercises))
    st.markdown(f"Score: {st.session_state.vocab_score}/{st.session_state.vocab_attempts}")

def render_grammar_exercise(exercises: List[Dict]):
    """Render interactive grammar exercises"""
    # Initialize session state for grammar exercises
    if "grammar_answers" not in st.session_state:
        st.session_state.grammar_answers = [""] * len(exercises)
        st.session_state.grammar_checked = [False] * len(exercises)
        st.session_state.grammar_correct = [False] * len(exercises)
    
    for i, exercise in enumerate(exercises):
        st.markdown(f"### Question {i+1}/{len(exercises)}")
        
        # Display the sentence with blank
        st.markdown(f"**{exercise['sentence']}**")
        st.markdown(f"*Translation: {exercise['translation']}*")
        
        # Radio buttons for options
        answer = st.radio(
            "Select the correct option:",
            exercise['options'],
            key=f"grammar_{i}"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Check", key=f"check_grammar_{i}"):
                st.session_state.grammar_answers[i] = answer
                st.session_state.grammar_checked[i] = True
                st.session_state.grammar_correct[i] = (answer == exercise['correctAnswer'])
                st.rerun()
        
        # Show feedback
        if st.session_state.grammar_checked[i]:
            if st.session_state.grammar_correct[i]:
                st.success("Correct! 🎉")
            else:
                st.error(f"Not quite. The correct answer is: {exercise['correctAnswer']}")
            
            st.info(f"Explanation: {exercise['explanation']}")
        
        st.divider()
    
    # Show score
    correct_count = sum(st.session_state.grammar_correct)
    total_checked = sum(st.session_state.grammar_checked)
    if total_checked > 0:
        st.markdown(f"**Current Score:** {correct_count}/{total_checked}")

def render_conversation_exercise(conversation: Dict):
    """Render interactive conversation exercises"""
    if not conversation:
        st.write("No conversation exercise available.")
        return
    
    st.markdown(f"### {conversation.get('scenario', 'Conversation Practice')}")
    st.markdown(conversation.get('context', ''))
    
    # Display the dialogue
    dialogue = conversation.get('dialogue', [])
    for i, line in enumerate(dialogue):
        speaker = line.get('speaker', '')
        text = line.get('text', '')
        translation = line.get('translation', '')
        
        if speaker == "You":
            st.text_input(
                f"{speaker}:",
                key=f"dialogue_{i}",
                placeholder="Type your response here..."
            )
            st.markdown(f"*Suggested response: {text}*")
            st.markdown(f"*Translation: {translation}*")
        else:
            st.markdown(f"**{speaker}:** {text}")
            st.markdown(f"*Translation: {translation}*")
    
    # Questions about the dialogue
    st.markdown("### Practice Questions")
    questions = conversation.get('questions', [])
    
    if "conversation_answers" not in st.session_state:
        st.session_state.conversation_answers = [""] * len(questions)
        st.session_state.conversation_checked = [False] * len(questions)
    
    for i, question in enumerate(questions):
        prompt = question.get('prompt', '')
        answer = question.get('answer', '')
        
        st.markdown(f"**{prompt}**")
        user_answer = st.text_area(
            "Your answer:",
            key=f"conv_answer_{i}",
            height=100
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Check", key=f"check_conv_{i}"):
                st.session_state.conversation_answers[i] = user_answer
                st.session_state.conversation_checked[i] = True
                st.rerun()
        
        if st.session_state.conversation_checked[i]:
            st.markdown("**Suggested answer:**")
            st.info(answer)

def render_reading_exercise(reading: Dict):
    """Render reading comprehension exercise"""
    if not reading:
        st.write("No reading exercise available.")
        return
    
    st.markdown(f"### {reading.get('title', 'Reading Comprehension')}")
    
    # Tabs for reading and translation
    tab1, tab2 = st.tabs(["Reading", "Translation"])
    
    with tab1:
        st.markdown(reading.get('passage', ''))
    
    with tab2:
        st.markdown(reading.get('translation', ''))
    
    # Questions section
    st.markdown("### Comprehension Questions")
    questions = reading.get('questions', [])
    
    if "reading_answers" not in st.session_state:
        st.session_state.reading_answers = [""] * len(questions)
        st.session_state.reading_checked = [False] * len(questions)
        st.session_state.reading_correct = [False] * len(questions)
    
    for i, question in enumerate(questions):
        st.markdown(f"**{i+1}. {question.get('question', '')}**")
        
        answer = st.radio(
            "Select your answer:",
            question.get('options', []),
            key=f"reading_{i}"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Check", key=f"check_reading_{i}"):
                st.session_state.reading_answers[i] = answer
                st.session_state.reading_checked[i] = True
                st.session_state.reading_correct[i] = (answer == question.get('correctAnswer', ''))
                st.rerun()
        
        if st.session_state.reading_checked[i]:
            if st.session_state.reading_correct[i]:
                st.success("Correct! 🎉")
            else:
                st.error(f"Not quite. The correct answer is: {question.get('correctAnswer', '')}")
        
        st.divider()
    
    # Vocabulary section
    st.markdown("### Key Vocabulary")
    vocab = reading.get('vocabulary', [])
    for word in vocab:
        with st.expander(f"{word.get('word', '')} - {word.get('translation', '')}"):
            st.markdown(word.get('definition', ''))

def render_listening_exercise(exercises: List[Dict]):
    """Render listening exercises (simulated with text for now)"""
    # Initialize session state for listening exercises
    if "listening_index" not in st.session_state:
        st.session_state.listening_index = 0
        st.session_state.listening_checked = False
        st.session_state.listening_score = 0
        st.session_state.listening_attempts = 0
    
    # Control buttons for navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("← Previous", key="prev_listen", disabled=st.session_state.listening_index <= 0):
            st.session_state.listening_index -= 1
            st.session_state.listening_checked = False
            st.rerun()
    
    with col3:
        if st.button("Next →", key="next_listen", disabled=st.session_state.listening_index >= len(exercises) - 1):
            st.session_state.listening_index += 1
            st.session_state.listening_checked = False
            st.rerun()
    
    # Display current listening exercise
    if exercises and 0 <= st.session_state.listening_index < len(exercises):
        exercise = exercises[st.session_state.listening_index]
        
        st.markdown(f"### Listening Exercise {st.session_state.listening_index + 1}/{len(exercises)}")
        
        # Play buttons (simulated)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔊 Play Audio", key=f"play_{st.session_state.listening_index}"):
                st.info(f"Simulated audio playing: '{exercise['audio_text']}'")
        
        with col2:
            if st.button("🐢 Play Slowly", key=f"play_slow_{st.session_state.listening_index}"):
                st.info(f"Simulated slow audio: '{exercise['audio_text_slow']}'")
        
        # Question
        st.markdown(f"**{exercise['question']}**")
        
        # Answer options
        answer = st.radio(
            "Your answer:",
            exercise['options'],
            key=f"listening_{st.session_state.listening_index}"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Check Answer", key=f"check_listen_{st.session_state.listening_index}"):
                st.session_state.listening_checked = True
                st.session_state.listening_attempts += 1
                if answer == exercise['correctAnswer']:
                    st.session_state.listening_score += 1
                st.rerun()
        
        # Show result
        if st.session_state.listening_checked:
            if answer == exercise['correctAnswer']:
                st.success("Correct! 🎉")
            else:
                st.error(f"Not quite. The correct answer is: {exercise['correctAnswer']}")
            
            st.info(f"Audio text: {exercise['audio_text']}")
            st.info(f"Translation: {exercise['translation']}")
    
    # Progress indicator
    st.progress((st.session_state.listening_index + 1) / len(exercises))
    st.markdown(f"Score: {st.session_state.listening_score}/{st.session_state.listening_attempts}")

def render_multiple_choice(exercises: List[Dict]):
    """Render multiple choice quiz"""
    # Initialize session state for quiz
    if "quiz_answers" not in st.session_state:
        st.session_state.quiz_answers = [""] * len(exercises)
        st.session_state.quiz_checked = [False] * len(exercises)
        st.session_state.quiz_correct = [False] * len(exercises)
    
    for i, question in enumerate(exercises):
        st.markdown(f"### Question {i+1}/{len(exercises)}")
        st.markdown(f"**{question['question']}**")
        
        answer = st.radio(
            "Select your answer:",
            question['options'],
            key=f"quiz_{i}"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Check", key=f"