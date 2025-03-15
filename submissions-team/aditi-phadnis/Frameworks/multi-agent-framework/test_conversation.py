from langchain_openai import ChatOpenAI
from models import UserProfile
from conversational_agent import ConversationAgent

# Initialize the LLM
llm = ChatOpenAI(temperature=0.2, model="gpt-4-turbo", streaming=True)

# Create a ConversationAgent instance
conversation_agent = ConversationAgent(llm)

# Create a test user profile
user_profile = UserProfile(
    target_language="French",
    difficulty_level="Beginner",
    learning_focus=["Vocabulary", "Conversation"]
)

# Define a test input
test_input = "How do I Reply when someone says say Bonjour?"

# Get a response
response = conversation_agent.respond(test_input, user_profile)

# Print the response
print("Agent Response:", response)
