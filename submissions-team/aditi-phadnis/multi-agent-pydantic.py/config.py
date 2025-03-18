import os
from dotenv import load_dotenv
from openai import OpenAI


# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
model = 'gpt-4o-mini'
client = OpenAI(api_key= OPENAI_API_KEY,
                model = model,
                temperature=0)


# Constants
DEFAULT_LANGUAGE = "Spanish"
DIFFICULTY_LEVELS = ["Beginner", "Intermediate", "Advanced"]

