from openai import OpenAI

from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

client = OpenAI()

# model = 'mistralai/Mistral-7B-Instruct-v0.3'
model = 'gpt-4o-mini'

system_message = """" You are a helpful AI assisstant whose job is to help the user to learn a new 
language. 
You will begin by using the user the following: 
1. Which language the user wants to learn. 
2. What is their current level of proficiency in the language. 
3. What is the level of proficiency they want to achieve.
4. What is their intent of learning the language. 

Using all the information provided by the user, you will guide 
the use to learn basics of their preferred language. 

Please handle specific types of queries:
1. How do you say s specific [word/phrase] in the [target language]
2. Teach me a simple sentence in target language. 
3. What is the translation of [word/phrase] in [target language].
4. Help me understand Greetings in a [target language]
When providing translations, make sure to explain pronunciation tips when relevant.

Here is an example conversation:
Assistant: Hello, welcome to your personal learning companinion. 
Which language you would like to learn?
User: I would like to learn French.
Assistant: Great! What is your current level of proficiency.

And then you will proceed with the conversation based on the user's proficiency. 
"""

#Initialize the conversation history: 

messages = [{"role": "system", "content": system_message}] 
# messages = []
def chat(user_input):
    """Generate a response to the user input.
    Args: 
        user_input (str): The input from the user.
    Returns:
        string containing the AI response.
  
    """

    global messages
    #Add user messages to the conversation history
    messages.append({"role": "user", "content": user_input})

    #Get response from the model 
    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.2,
    )

    response =completion.choices[0].message.content

    #Add AI response to the conversation history
    messages.append({"role": "assistant", "content": response})

    return response

def main():
    """ Main function to run a language learning assistant in a terminal. """
    print("Welcome to your personal learning companion!")
    print("Type 'quit', 'exit' or 'bye' to end the conversation.")

    #Initial Greeting:
    print("AI: Welcome to your personal learning companion. Which language would you like to learn.")

    #Main conversation loop:
    while True:
        user_input = input("User: ")

        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("AI: Goodbye! Have a great day.")
            break

        response = chat(user_input)
        print(f"AI: {response}")

if __name__ == "__main__":
    main()
