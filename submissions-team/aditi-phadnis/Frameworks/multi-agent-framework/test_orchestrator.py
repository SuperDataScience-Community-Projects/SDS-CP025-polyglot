from langchain_openai import ChatOpenAI
from models import UserProfile
from orchestrator import Orchestrator

# Initialize the LLM
llm = ChatOpenAI(temperature=0.2, model="gpt-4-turbo", streaming=True)

# Create an Orchestrator instance
orchestrator = Orchestrator(llm)

# Create a test user profile
user_profile = UserProfile(
    target_language="French",
    difficulty_level="Beginner",
    learning_focus=["Vocabulary", "Grammar"]
)

# Step 1: Simulate a conversation
user_input = "How do I say 'Good morning' in French?"
conversation_response = orchestrator.handle_conversation(user_input, user_profile)
print("\n🔹 AI Conversation Response:")
print(conversation_response)

# Step 2: Generate exercises
exercises = orchestrator.generate_exercises(user_profile)
print("\n🔹 Generated Exercises:")
print(exercises)

# Step 3: Simulate user responses for feedback
user_answers = {
    "Bonjour": "Bonjour",
    "Je m'appelle Pierre.": "Je m'appelle Pierre.",
    "Merci beaucoup.": "Merci beaucoup."
}
correct_answers = {
    "Bonjour": "Bonjour",
    "Je m'appelle Pierre.": "Je m'appelle Pierre.",
    "Merci beaucoup.": "Merci beaucoup."
}

# Step 4: Get feedback
feedback = orchestrator.provide_feedback(user_answers, correct_answers)
print("\n🔹 Feedback on Exercises:")
print(feedback)
