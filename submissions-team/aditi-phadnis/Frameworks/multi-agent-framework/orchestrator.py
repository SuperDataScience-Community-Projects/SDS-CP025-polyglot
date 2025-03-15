from langchain_openai import ChatOpenAI
from models import UserProfile
from exercise_agent import ExerciseGeneratorAgent
from feedback_agent import FeedbackAgent
from conversational_agent import ConversationAgent

class Orchestrator:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.conversational_agent = ConversationAgent(llm)
        self.exercise_agent = ExerciseGeneratorAgent(llm)
        self.feedback_agent = FeedbackAgent(llm)
    
    def handle_conversation(self, user_input: str, user_profile: UserProfile) -> str:
        """Handles user conversation and returns AI response."""
        return self.conversational_agent.respond(user_input, user_profile)
    
    def generate_exercises(self, user_profile: UserProfile) -> str:
        """Generates a set of 3 exercises for the user."""
        return self.exercise_agent.generate_exercises(user_profile)
    
    def provide_feedback(self, user_answers: dict, correct_answers: dict) -> str:
        """Provides feedback based on user responses."""
        if correct_answers is None or all(v is None for v in correct_answers.values()):
            print("ERROR: correct_answers is missing or empty before providing feedback")
            return {}

        return self.feedback_agent.provide_feedback(user_answers, correct_answers)
    
    def run(self, user_input: str, user_profile: UserProfile) -> str:
        """Orchestrates the workflow: conversation → exercises → feedback."""
        conversation_response = self.handle_conversation(user_input, user_profile)
        exercises = self.generate_exercises(user_profile)
        
        return f"### AI Response:\n{conversation_response}\n\n### Exercises:\n{exercises}\n\n(Submit your answers for feedback!)"
