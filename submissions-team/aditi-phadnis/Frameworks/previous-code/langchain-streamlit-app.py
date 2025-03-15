import os
import streamlit as st
from langchain.agents import AgentType, initialize_agent
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.tools import Tool
from langchain.memory import ConversationBufferMemory
from dotenv import find_dotenv, load_dotenv
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAI
from langchain.tools import Tool
from typing import Dict, Any
from pydantic import BaseModel
from langchain_community.llms import OpenAI
from langchain.prompts import MessagesPlaceholder
from langchain.schema import SystemMessage
from langchain.callbacks.base import BaseCallbackHandler

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

# Custom Callback Handler for Streaming
class StreamHandler(BaseCallbackHandler):
    def __init__(self, container, initial_text=""):
        self.container = container
        self.text = initial_text

    def on_llm_new_token(self, token: str, **kwargs):
        self.text += token
        self.container.markdown(self.text)

# Initialize LLM (OpenAI)
llm = ChatOpenAI(temperature=0, model_name="gpt-4-turbo", streaming=True)

# 1. Grammar Correction Tool
def correct_grammar(text: str) -> str:
    prompt_template = PromptTemplate.from_template(
        "Correct the following text: {text}\n\nCorrected Text:"
    )
    grammar_chain = prompt_template | llm
    return grammar_chain.invoke({"text": text}).content

grammar_tool = Tool(
    name="Grammar Correction",
    func=correct_grammar,
    description="""Useful for correcting grammatical errors in user input. 
                    Use this tool if the user's input might contain grammatical errors. 
                    Input should be the potentially incorrect text.""",
)

# 2. Translation Tool
def translate_to_english(text: str) -> str:
    prompt_template = PromptTemplate.from_template(
        "Translate the following text to English: {text}\n\nEnglish Translation:"
    )
    translation_chain = prompt_template | llm
    return translation_chain.invoke({"text": text}).content

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
    try:
        input_data = ExplanationInput(
            original_text=inputs.get('original_text', ''),
            corrected_text=inputs.get('corrected_text', ''),
            translated_text=inputs.get('translated_text', '')
        )

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
    if original == corrected:
        return "No grammar corrections were necessary."
    return "Text was corrected for grammar and structure."

def _analyze_translation(corrected: str, translated: str) -> str:
    return "Text was translated to English maintaining the original meaning."

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
    prompt_template = PromptTemplate.from_template(
        """Suggest a common phrase in {language} related to {topic}. Provide the phrase and its English translation.

        {language} Phrase and English Translation:
        """
    )
    phrase_chain = prompt_template | llm
    return phrase_chain.invoke({"topic": topic, "language": language}).content

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
    in learning languages by correcting their grammar, translating text, 
    and explaining the nuances of the translation. You also provide common phrases upon request. 
    After your thought is done, and you have decided on using a tool, mention which tool will be used 
    before taking action."""
)

agent_kwargs = {
    "extra_prompt_messages": [MessagesPlaceholder(variable_name="chat_history"), system_message],
}

agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    verbose=False, # Set to False for cleaner output in Streamlit
    memory=memory,
    agent_kwargs=agent_kwargs
)

# 6. Streamlit App
st.title("Polyglot AI Language Tutor")

user_input = st.text_area("Enter your text:", height=200)

if st.button("Process"):
    if user_input:
        try:
            output_container = st.empty()  # Create an empty container to display streaming output
            stream_handler = StreamHandler(output_container)
            llm.callbacks = [stream_handler]

            result = agent.invoke({"input": user_input})

            llm.callbacks = []  # Remove callback after processing.

            st.write("## Output")
            st.write(result['output'])
        except Exception as e:
            st.error(f"An error occurred: {e}")
        finally:
            llm.callbacks = []  # Ensure callbacks are removed even on error
    else:
        st.warning("Please enter some text to process.")
