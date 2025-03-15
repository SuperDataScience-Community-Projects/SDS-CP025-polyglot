import os
from langchain.agents import AgentType, initialize_agent
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.tools import Tool
from langchain.memory import ConversationBufferMemory
from dotenv import find_dotenv, load_dotenv
from langchain.llms import OpenAI
from langchain.prompts import MessagesPlaceholder
from langchain.schema import SystemMessage
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAI
from langchain.tools import Tool
from typing import Dict, Any
from pydantic import BaseModel
from langchain_community.llms import OpenAI






load_dotenv()

# Set OpenAI API Key (make sure it's set in your environment variables)
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]  # Replace with your actual key

# Initialize LLM (OpenAI)
llm = ChatOpenAI(temperature=0, model_name="gpt-4-turbo")

# 1. Grammar Correction Tool
def correct_grammar(text: str) -> str:
    """Corrects grammatical errors in the given text using LLM."""
    prompt_template = PromptTemplate.from_template(
        "Correct the following text: {text}\n\nCorrected Text:"
    )
    grammar_chain = prompt_template | llm # using chain instead of LLMChain
    return grammar_chain.invoke({"text": text})

grammar_tool = Tool(
    name="Grammar Correction",
    func=correct_grammar,
    description="""Useful for correcting grammatical errors in user input. 
                    Use this tool if the user's input might contain grammatical errors. 
                    Input should be the potentially incorrect text.""",
)


# 2. Translation Tool
def translate_to_english(text: str) -> str:
    """Translates the given text to English using LLM."""
    prompt_template = PromptTemplate.from_template(
        "Translate the following text to English: {text}\n\nEnglish Translation:"
    )
    translation_chain = prompt_template | llm 
    return translation_chain.invoke({"text": text})

translation_tool = Tool(
    name="Translation",
    func=translate_to_english,
    description=""" Useful for translating text to English.  Use this tool *after* 
                    grammar correction if necessary. Input should be the text to translate 
                    (either the original or corrected text).""",
)

# 3. Explanation Tool
class ExplanationInput(BaseModel):
    original_text: str
    corrected_text: str
    translated_text: str

def run_explanation_chain(inputs: Dict[str, Any]) -> str:
    """
    Runs the explanation chain with proper input validation and error handling
    
    Args:
        inputs: Dictionary containing original_text, corrected_text, and translated_text
    Returns:
        str: Detailed explanation of the text transformations
    """
    try:
        # Validate inputs
        input_data = ExplanationInput(
            original_text=inputs.get('original_text', ''),
            corrected_text=inputs.get('corrected_text', ''),
            translated_text=inputs.get('translated_text', '')
        )
        
        # Create a structured explanation
        explanation = f"""
        Analysis of Text Transformations:
        
        1. Original Text:
        "{input_data.original_text}"
        
        2. Grammar Corrections:
        "{input_data.corrected_text}"
        
        3. English Translation:
        "{input_data.translated_text}"
        
        Changes Explained:
        - Grammar Changes: {_analyze_differences(input_data.original_text, input_data.corrected_text)}
        - Translation Details: {_analyze_translation(input_data.corrected_text, input_data.translated_text)}
        """
        
        return explanation.strip()
        
    except Exception as e:
        return f"Error in explanation chain: {str(e)}"

def _analyze_differences(original: str, corrected: str) -> str:
    """Helper function to analyze grammar differences"""
    if original == corrected:
        return "No grammar corrections were necessary."
    return "Text was corrected for grammar and structure."

def _analyze_translation(corrected: str, translated: str) -> str:
    """Helper function to analyze translation"""
    return "Text was translated to English maintaining the original meaning."

# Define the explanation tool with improved structure
explanation_tool = Tool(
    name="Explanation",
    func=run_explanation_chain,
    description="""
    Analyzes and explains text transformations including:
    - Original text analysis
    - Grammar corrections
    - English translation
    
    Input should be a dictionary with:
    - original_text: The initial input text
    - corrected_text: The grammar-corrected version
    - translated_text: The English translation
    
    Use this tool AFTER both Grammar Correction and Translation tools.
    """,
    return_direct=True
)




# 4. Phrase Suggestion Tool
def suggest_phrase(topic: str, language: str) -> str:
    """Suggests a common phrase in the target language (e.g., Spanish) related to the topic and provides its English translation."""
    prompt_template = PromptTemplate.from_template(
        """Suggest a common phrase in {language} related to {topic}. Provide the phrase and its English translation. Format your response clearly.

        {language} Phrase and English Translation:
        """
    )
    phrase_chain = prompt_template | llm # using chain instead of LLMChain
    return phrase_chain.invoke(topic=topic, language=language)

phrase_suggestion_tool = Tool(
    name="Phrase Suggestion",
    func=suggest_phrase,
    description="Useful for suggesting common phrases in a language related to a topic. Input should be the topic and the language.",
)


# 5. Define the agent
tools = [grammar_tool, translation_tool, explanation_tool, phrase_suggestion_tool]

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

system_message = SystemMessage(
        content="""You are a helpful AI language tutor. Your goal is to assist the user 
        in learning languages by correcting their grammar, 
        translating text, and explaining the nuances of the translation. 
        You also provide common phrases upon request. After your thought is done, 
        and you have decided on using a tool, mention which tool will be used 
        before taking action"""
    )


agent_kwargs = {
    "extra_prompt_messages": [MessagesPlaceholder(variable_name="chat_history"), system_message],
}

agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    verbose=True,
    memory=memory,
    agent_kwargs=agent_kwargs
)


# 6. Interaction Loop
while True:
    user_input = input("Enter your text (or 'quit'): ")
    if user_input.lower() == "quit":
        break

    try:
        # Use agent.invoke instead of agent.run
        result = agent.invoke({"input": user_input})
        print(result['output'])  # Access the output from the dictionary
    except Exception as e:
        print(f"An error occurred: {e}")

