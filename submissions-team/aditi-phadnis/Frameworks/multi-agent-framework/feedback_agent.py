from langchain.prompts import ChatPromptTemplate
from langchain.tools import Tool
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from models import UserProfile

class FeedbackAgent:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        
        # Define tools
        self.tools = [
            Tool(name="ProvideFeedback", func=self.provide_feedback, description="Evaluates user answers and provides feedback")
        ]
        
        # Define prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful language tutor providing feedback on exercises.
            Analyze user responses based on accuracy and grammar, and provide constructive feedback."""),
            ("user", "{input}"),
            ("assistant", "{agent_scratchpad}")
        ])
        
        # Create agent
        self.agent = create_openai_functions_agent(llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)
    
    def format_markdown(self, title: str, content: str) -> str:
        """Formats feedback content into Markdown format."""
        return f"## {title}\n\n{content}\n"
    
    def provide_feedback(self, user_answers: dict, correct_answers: dict) -> dict:
        """Compares user answers with correct answers and provides feedback with explanations."""

        feedback = {}

        print("DEBUG: correct_answers =", correct_answers)  # Check structure
        print("DEBUG: user_answers =", user_answers)
        print("DEBUG: correct_answers =", correct_answers)  # Debug output

        if not correct_answers or not isinstance(correct_answers, dict):
            print("ERROR: correct_answers is None or not a dictionary!")
            return {q: {
                "correct": False,
                "message": "❌ Incorrect. No correct answer available.",
                "explanation": "An error occurred while retrieving the correct answer."
            } for q in user_answers}



        for question, correct_info in correct_answers.items():
            user_answer = user_answers.get(question, "").strip().lower()

            # Ensure correct_info is a valid dictionary
            if not correct_info or not isinstance(correct_info, dict):
                feedback[question] = {
                    "correct": False,
                    "message": "❌ Incorrect. No correct answer available.",
                    "explanation": "An error occurred while retrieving the correct answer."
                }
                continue

            # Extract values safely
            correct_answer = correct_info.get("correctAnswer")
            explanation = correct_info.get("explanation", "No explanation available.")

            if not correct_answer:
                feedback[question] = {
                    "correct": False,
                    "message": "❌ Incorrect. No correct answer provided.",
                    "explanation": "The answer key is missing."
                }
                continue

            if user_answer == correct_answer.strip().lower():
                feedback[question] = {
                    "correct": True,
                    "message": "✅ Correct!",
                    "explanation": explanation
                }
            else:
                feedback[question] = {
                    "correct": False,
                    "message": f"❌ Incorrect. Correct answer: {correct_answer}",
                    "explanation": explanation
                }

        return feedback


