import os
import random
import json
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional, Type
from utils import function_to_schema, execute_tool_call

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set")

client = OpenAI()


################ Classes ################

class Agent(BaseModel):
    name: str = "Agent"
    model: str = "gpt-4o-mini"
    instructions: str = "You are a helpful agent"
    tools: Optional[list] = None
    response_format: Optional[Type[BaseModel]] = None

class User(BaseModel):
    language: str = "English"
    experience_level: str = "beginner"
    learning_goal: str = "learn the basics"



############ Tools ################
def call_information_extraction_agent():
    return information_extraction_agent

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


def execute_tool_call(tool_call, tools, agent_name):
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)

    print(f"{agent_name}:", f"{name}({args})")

    return tools[name](**args)


def chat_completions(agent, messages):
    tool_schemas = [function_to_schema(tool) for tool in agent.tools]
    tool_map = {tool.__name__: tool for tool in agent.tools}

    response = client.chat.completions.create(
        model = agent.model,
        messages = [{"role": "system", "content": agent.instructions}] + messages,
        tools = tool_schemas
    )

    return response.choices[0].message, tool_schemas, tool_map

def chat_parse(agent, messages):
    # tool_schemas = [function_to_schema(tool) for tool in agent.tools]
    # tool_map = {tool.__name__: tool for tool in agent.tools}

    response = client.beta.chat.completions.parse(
        model = agent.model,
        messages = [{"role": "system", "content": agent.instructions}] + messages,
        # tools = tool_schemas,
        response_format = agent.response_format
    )

    return response.choices[0].message
################ Agents ################

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
        pass the user's information to the Information Extraction Agent.
    """,
    tools = [call_information_extraction_agent]
)

information_extraction_agent = Agent(
    name = "Information Extraction Agent",
    instructions = """
        You are a helpful assistant that can extract information about the user's language learning goals
        from a conversation with the user.

        You will be given a conversation between a user and a conversation agent.
        Your job is to extract the information about the user's language learning goals from the conversation.
    """,
    response_format = User
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
    """
)


#########################################



def run_turn(agent, messages):
    current_agent = agent

    print("Assitant: Hello, I am your language learning assistant. Can you tell me what language you want to learn?")
    user_input = input("\nYou: ")

    while user_input != "exit":
        
        messages.append({"role": "user", "content": user_input})

        print("Current agent: ", current_agent.name)

        # Get response from the model
        message, tool_schemas, tool_map = chat_completions(current_agent, messages)
        messages.append(message)

        if message.content:
            print("\nAssitant: ", message.content)

        if message.tool_calls:
            print("\nMessage: ", message)
            print("\nTool calls: ", message.tool_calls)
            for tool_call in message.tool_calls:
                result = execute_tool_call(tool_call, tool_map, current_agent.name)
                print("\nTool call result: ", result)
                print("\nTool result is Agent? ", type(result) is Agent)

                if type(result) is Agent:
                    current_agent = result

                    print("\nConversation has been passed on to: ", current_agent.name)

            result_message = {
                "role":"tool",
                "tool_call_id": tool_call.id,
                "content": str(result)
            }
            messages.append(result_message)

            message = chat_parse(current_agent, messages)
            messages.append(message)
            print("Message from agent: ", message)

        
        user_input = input("\nYou: ")
            
    return messages


run_turn(conversation_agent, [])