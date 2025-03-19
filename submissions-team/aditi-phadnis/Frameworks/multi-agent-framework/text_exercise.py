from langchain_openai import ChatOpenAI
from models import UserProfile
from exercise_agent import ExerciseGeneratorAgent
import json

# Initialize the LLM
llm = ChatOpenAI(temperature=0.2, model="gpt-4-turbo", streaming=True)

# Create an ExerciseGeneratorAgent instance
exercise_agent = ExerciseGeneratorAgent(llm)

# Create a test user profile
user_profile = UserProfile(
    target_language="Spanish",
    difficulty_level="Intermediate",
    learning_focus="Vocabulary"
)

# # Define test cases
# print("🔹 Testing Vocabulary Exercise:")
# print(json.dumps(exercise_agent.generate_vocabulary_exercise(target_language= user_profile.target_language, 
#                                                              difficulty=user_profile.difficulty_level, 
#                                                              theme="Travel", 
#                                                              count=3), 
#                                                              indent=2))

# print("\n🔹 Testing Grammar Exercise:")
# print(exercise_agent.generate_grammar_exercise(target_language= user_profile.target_language,
#                                                           difficulty=user_profile.difficulty_level, 
#                                                           grammar_point="Past Tense", 
#                                                           count=3))

print("\n🔹 Testing Conversation Exercise:")
print(exercise_agent.generate_conversation_exercise(target_language= user_profile.target_language,
                                                               difficulty=user_profile.difficulty_level, 
                                                               scenario="Ordering food at a restaurant"))

# print("\n🔹 Testing General Exercise Generation:")
# print(exercise_agent.generate_exercise(exercise_type="grammar", user_profile=user_profile))
