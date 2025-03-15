import streamlit as st
from langchain_openai import ChatOpenAI
from models import UserProfile
from orchestrator import Orchestrator

# Initialize LLM and orchestrator
llm = ChatOpenAI(temperature=0.2, model="gpt-4-turbo", streaming=True)
orchestrator = Orchestrator(llm)
# st.title("🌍 AI Language Tutor")
# st.sidebar.header("User Settings")
    
# # User profile inputs
# target_language = st.sidebar.selectbox("Target Language", ["French", "Spanish", "German", "Italian"])
# difficulty_level = st.sidebar.selectbox("Difficulty Level", ["Beginner", "Intermediate", "Advanced"])
# learning_focus = st.sidebar.selectbox("Learning Focus", ["Vocabulary", "Grammar", "Conversation"])

# user_profile = UserProfile(
#         target_language=target_language,
#         difficulty_level=difficulty_level,
#         learning_focus=learning_focus
#     )
def generate_exercises_tab(user_profile):

    # Ensure session state variables exist
    if "exercises" not in st.session_state:
        st.session_state.exercises = []
    if "user_answers" not in st.session_state:
        st.session_state.user_answers = {}
    if "correct_answers" not in st.session_state:
        st.session_state.correct_answers = {}
    if "feedback" not in st.session_state:
        st.session_state.feedback = {}


    # Generate exercises
    if st.button("Generate Exercises", key="generate_exercise_1"):
        st.session_state.exercises = orchestrator.generate_exercises(user_profile)
        st.session_state.user_answers = {}
        st.session_state.correct_answers = {} # Clear previous correct answers
        st.session_state.feedback = None # Clear previous feedback


    exercises = st.session_state.exercises

    if not exercises:
        st.warning("No exercises generated yet.")
        return

    # Display exercises interactively
    for i, exercise in enumerate(exercises):
        if not isinstance(exercise, dict):
            st.warning(f"Skipping invalid exercise {i}: Not a dictionary - {exercise}")
            continue  # Skip non-dictionary entries

        if "type" not in exercise:
            st.warning(f"Skipping exercise {i}: Missing 'type' key - {exercise}")
            continue  # Skip exercises missing 'type'

        st.subheader(f"Exercise {i+1}")

        if exercise["type"] == "single_choice":
            question = exercise["question"]
            st.write(f"**Question:** {question}")
            options = exercise["options"]
            user_answer = st.radio(
                "Select the correct answer:", options, key=f"single_choice_{i}"
            )


        elif exercise["type"] == "fill_in_the_blank":
            question = exercise["question"]
            st.write(options = exercise["options"])
            user_answer = st.text_input(question, key=f"fib_{i}")

        elif exercise["type"] == "matching":
            question = exercise["question"]
            pairs = exercise["pairs"]
            # Ensure pairs is a dictionary before using .items()
            if isinstance(pairs, dict):
                user_answer = {
                    key: st.selectbox(f"Match {key} to:", list(pairs.values()), key=f"match_{i}_{key}") 
                    for key, value in pairs.items()  # ✅ Safe because we checked it's a dictionary
                }
            else:
                st.error("Error: 'pairs' is not a dictionary. Check the data structure.")

        # Store user answer in session state
        st.session_state.user_answers[i] = user_answer
        st.session_state.correct_answers[i] = {
            "correct_answer": exercise.get("correctAnswer") or exercise.get("correct_answer"),
            "explanation": exercise.get("explanation", "No explanation provided")
        }
        # print("DEBUG: Stored correct_answers =", st.session_state.correct_answers)

        



        # # Get Correct answers
        # correct_answers = st.session_state.get("correct_answers")
        # print("DEBUG: correct_answers before providing feedback =", correct_answers)
        if "exercises" not in st.session_state or st.session_state.exercises is None:
            st.warning("No exercises found. Try generating them again.")
            return

        # Extract correct answers properly
        if "correct_answers" not in st.session_state or not st.session_state.correct_answers:
            st.session_state.correct_answers = {
                idx: {
                    "correct_answer": ex["correct_answer"] if "correct_answer" in ex else "No correct answer available",
                    "explanation": ex["explanation"] if "explanation" in ex else "No explanation provided"
                }
                for idx, ex in enumerate(st.session_state.exercises) if isinstance(ex, dict)
            }



    # Submit answers
    if st.button("Submit Answers", key="Submit_Answers1"):
        if "exercises" in st.session_state and st.session_state.exercises:
            st.write("DEBUG: Exercises Data =", st.session_state.exercises)
            # Ensure correct_answers exist in session state
            if "correct_answers" not in st.session_state or not st.session_state.correct_answers:
                st.session_state.correct_answers = {
                    idx: {
                        "correctAnswer": ex.get("correctAnswer") or ex.get("correct_answer") or "No correct answer available",
                        "explanation": ex.get("explanation", "No explanation provided")
                    }
                    for idx, ex in enumerate(st.session_state.exercises)
                    if isinstance(ex, dict)
                }
            # Debugging: Check if user answers exist
            st.write("Debugging: User Answers:", st.session_state.user_answers)
            user_answers = st.session_state.user_answers

            # Ensure `user_answers` exist before sending for feedback
            if st.session_state.user_answers:
                feedback = orchestrator.provide_feedback(st.session_state.user_answers, st.session_state.correct_answers)
                st.session_state.feedback = feedback
            else:
                st.warning("No answers detected. Please provide your answers before submitting.")

        else:
            st.warning("No exercises found. Please generate exercises first.")

        # Show feedback
        if "feedback" in st.session_state and st.session_state.feedback:
            st.write("Debugging: Correct Answers:", st.session_state.correct_answers)


            # Extract feedback and format as Markdown
            feedback_data = st.session_state.feedback
            if isinstance(feedback_data, dict):
                feedback_md = "### Feedback\n"
                for i, feedback in feedback_data.items():
                    # str_i = str(i)  # Convert index to string for correct matching
                    # user_answer = st.session_state.user_answers.get(str(i), 'N/A')

                    feedback_md += f"**Exercise {i+1}:**\n"
                    feedback_md += f"- **Your Answer:** {st.session_state.user_answers.get(i, 'N/A')}\n"
                    feedback_md += f"- **Correct Answer:** {st.session_state.correct_answers.get(i, {}).get('correct_answer', 'No correct answer available')}\n"
                    feedback_md += f"- **Explanation:** {st.session_state.correct_answers.get(i, {}).get('explanation', 'No explanation provided')}\n\n"
                
                st.markdown(feedback_md)

            else:
                st.warning("Invalid feedback format.")


        

    
# generate_exercises_tab(user_profile)
# print("Checkpoint")
# print("Running app3.py")



