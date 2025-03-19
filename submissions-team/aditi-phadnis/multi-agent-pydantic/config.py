import os
from dotenv import load_dotenv
from openai import OpenAI
import uuid
from typing import Dict, Any, List, Tuple
from pydantic import BaseModel, Field
import random

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
model = 'gpt-4o-mini'
temperature = 0
client = OpenAI(api_key= OPENAI_API_KEY,)


# Constants
DEFAULT_LANGUAGE = "Spanish"
DIFFICULTY_LEVELS = ["Beginner", "Intermediate", "Advanced"]


class UserProfile(BaseModel):
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    target_language: str = "Spanish"
    difficulty_level: str = "Beginner"
    learning_focus: str = "Vocabulary"
    strengths: List[str] = []
    weaknesses: List[str] = []
    conversation_history: List[Dict] = []
    exercise_history: List[Dict] = []
    feedback_history: List[Dict] = []


# Define Themes for Different Difficulty Levels
themes = {
    "Beginner": ["Greetings", "Family", "Food", "Colors", "Numbers"],
    "Intermediate": ["Travel", "Work", "Hobbies", "Weather", "Shopping"],
    "Advanced": ["Politics", "Environment", "Technology", "Literature", "Philosophy"]
}

# Create a test user profile
user_profile = UserProfile(
    target_language="French",
    difficulty_level="Beginner",
    learning_focus= "Vocabulary"
)



# Select a random theme based on the user's difficulty level
if user_profile.difficulty_level in themes:
    theme = random.choice(themes[user_profile.difficulty_level])
else:
    theme = "General"

