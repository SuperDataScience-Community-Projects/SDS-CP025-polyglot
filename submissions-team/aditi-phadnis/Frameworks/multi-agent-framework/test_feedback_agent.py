from langchain_openai import ChatOpenAI
from feedback_agent import FeedbackAgent

# Initialize the LLM
llm = ChatOpenAI(temperature=0.2, model="gpt-4-turbo", streaming=True)

# Create a FeedbackAgent instance
feedback_agent = FeedbackAgent(llm)

# Sample user answers and correct answers
user_answers = {
    "Ayer yo (comer) __________ una pizza deliciosa.": "comó",
    "Nosotros (ir) __________ al cine la semana pasada.": "fuimos",
    "Ellos (ver) __________ una película muy interesante.": "vieron",
    "Tú (escribir) __________ una carta a tu abuela.": "escribiste",
    "Ella (resolver) __________ todos los problemas.": "resolvió"
}

correct_answers = {
    "Ayer yo (comer) __________ una pizza deliciosa.": "comí",
    "Nosotros (ir) __________ al cine la semana pasada.": "fuimos",
    "Ellos (ver) __________ una película muy interesante.": "vieron",
    "Tú (escribir) __________ una carta a tu abuela.": "escribiste",
    "Ella (resolver) __________ todos los problemas.": "resolvió"
}

# Get feedback
feedback = feedback_agent.provide_feedback(user_answers, correct_answers)

# Print the feedback in markdown format
print(feedback)
