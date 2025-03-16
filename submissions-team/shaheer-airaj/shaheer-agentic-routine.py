import os
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set")

client = OpenAI()


class Agent(BaseModel):
    name: str = "Agent"
    model: str = "gpt-4o-mini"
    instructions: str = "You are a helpful agent"
    tools: list = []

conversation_agent = Agent(
    name = "Conversation Agent",
    instructions = (
        "You are a smooth conversationalist and your role is to chat with the user\n"
        "about how to learn a new language. Begin the conversation by asking the user\n"
        "some basic questions like the following:"
        "1. Ask them what language they want to learn"
        "2. Gauge how well they currently understand that language"
        "3. What proficiency level they want to reach"
    ),
    tools = None
)