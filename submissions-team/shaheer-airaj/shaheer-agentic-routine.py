import os
import random
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from utils import helper_functions, execute_tool_call

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set")

client = OpenAI()


class Agent(BaseModel):
    name: str = "Agent"
    model: str = "gpt-4o-mini"
    instructions: str = "You are a helpful agent"
    tools: list = None

def call_exercise_agent():
    return True

def phrase_generator(language: str = "french"):
    phrases = {
        "french": [
            "Bonjour, comment allez-vous?",
            "Je m'appelle...",
            "S'il vous plaît",
            "Merci beaucoup",
            "Au revoir"
        ],
        "spanish": [
            "¡Hola! ¿Cómo estás?", 
            "Me llamo...",
            "Por favor",
            "Muchas gracias",
            "Adiós"
        ]
    }
    
    if language.lower() not in phrases:
        raise ValueError("Language must be 'french' or 'spanish'")
        
    return random.choice(phrases[language.lower()])

conversation_agent = Agent(
    name = "Conversation Agent",
    instructions = """
        You are a smooth conversationalist who responds in one or two sentences
        and your role is to chat with the user and gain an understanding of their language learning goals.
        Begin the conversation by asking the user some basic questions like the following:
        1. Ask them what language they want to learn
        2. Gauge how well they currently understand that language
        3. What proficiency level they want to reach

        The point is to gain a deep understanding of the user's language learning goals.

        Once you have a deep understanding of the user's language learning goals, you are to
        pass the user's information to the Exercise Agent.
    """,
    tools = [call_exercise_agent]
)

exercise_agent = Agent(
    name = "Exercise Agent",
    instructions = """
        You are a helpful assistant that can help the user with their language learning goals.
        You can help the user with their language learning goals by providing them with exercises.

        You can use the phrase_generator tool to generate a phrase in the user's language and then ask them
        what the appropriate response would be.

        Eg.

        Phrase: "Bonjour, comment allez-vous?"
        Response: "I am doing well, thank you for asking!"

        If the user answers the phrase correctly, you can then ask them to generate a response to a different phrase.
        If they do not answer correctly, you can ask them to try again and maybe give them a hint.
    """,
    tools = [phrase_generator]
)


def run_turn(agent, messages):
    print("Assitant: Hello, how can I help you today?")
    user_input = ""

    while user_input != "exit":

        tool_schemas = [helper_functions.function_to_schema(tool) for tool in agent.tools]
        tool_map = {tool.__name__: tool for tool in agent.tools}
        
        user_input = input("\nYou: ")
        messages.append({"role": "user", "content": user_input})

        # Get response from the model
        response = client.chat.completions.create(
        model = agent.model,
        messages = [{"role": "system", "content": agent.instructions}] + messages,
        tools = tool_schemas,
        )

        message = response.choices[0].message
        messages.append(message)

        if message.content:
            print("\nAssitant: ", message.content)

        if message.tool_calls:
            print("\nMessage: ", message)
            print("\nTool calls: ", message.tool_calls)
            for tool_call in message.tool_calls:
                result = execute_tool_call(tool_call, tool_map, agent.name)
                print("\nTool call result: ", result)

            result_message = {
                "role":"tool",
                "tool_call_id": tool_call.id,
                "content": str(result)
            }
            messages.append(result_message)
            
    return messages

def execute_tool_call(tool_call, tools, agent_name):
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)

    print(f"{agent_name}:", f"{name}({args})")

    return tools[name](**args)


run_turn(conversation_agent, [])