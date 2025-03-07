import streamlit as st
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.prompts import MessagesPlaceholder
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import Tool
import openai
import os
from dotenv import load_dotenv
import time
import glob

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY


def cleanup_audio_files():
    """Delete all temporary audio files"""
    for audio_file in glob.glob("temp_audio_*.mp3"):
        try:
            os.remove(audio_file)
            print(f"Deleted: {audio_file}")
        except Exception as e:
            print(f"Error deleting {audio_file}: {e}")

def text_to_speech(text: str, filename: str):
    """Converts text to speech using OpenAI's TTS API and saves the audio"""
    try:
        response = openai.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text,
            speed=0.75
        )
        with open(filename, "wb") as f:
            f.write(response.content)
        return filename
    except Exception as e:
        print(f"Error generating TTS: {e}")
        return None

def translate_text(text: str, target_lang: str) -> str:
    """Translates text to target language"""
    try:
        translation = translator.translate(text, dest=target_lang)
        return translation.text
    except Exception as e:
        return f"Translation error: {str(e)}"

def play_audio(audio_file):
    """Creates an audio player in Streamlit for a given audio file"""
    with open(audio_file, "rb") as audio:
        st.audio(audio, format="audio/mp3", start_time=0, autoplay=False)

# Define tools
tools = [
    Tool(
        name="text_to_speech",
        description="Converts text to speech and saves as audio file",
        func=text_to_speech
    ),
    Tool(
        name="translate",
        description="Translates text to target language",
        func=translate_text
    )
]

# Initialize OpenAI Model
llm = ChatOpenAI(
    temperature=0.7,
    model="gpt-4-turbo",
    streaming=True
)

# Define the prompt template
SYSTEM_PROMPT = """You are a polyglot AI language tutor, skilled in teaching multiple languages. 
Your role is to:
1. Help users learn new languages through natural conversation
2. Provide translations when requested
3. Explain grammar concepts clearly
4. Offer pronunciation guidance
5. Share cultural context relevant to the language
6. Engage in conversation practice
7. If the user provides you with a response in the selected language, 
    - appreciate the user if the usage is right.
    - correct the user if the usage is wrong. 
    - if you are answering the user in the selected language, provide translation in English for the same,
    don't just respond to the user as a follow up question. 
    Example conversation- 
    User: I want to learn Spanish.
    Your response: "Absolutely, I'd be glad to help you learn Spanish! Whether you're starting from scratch or 
    looking to improve your existing skills, we can work on vocabulary, grammar, pronunciation, and more. 
    How about we start with some basic greetings and introductions? Let me know if you have any 
    specific areas you're interested in or if you'd like to start with the basics."
    User: Start from the basics
    Assistant: Great choice! Spanish is a beautiful language with a rich cultural heritage. Let’s start with some basic greetings and expressions that are commonly used in everyday conversation.

    Hello - Hola (OH-lah)
    Goodbye - Adiós (ah-DYOS)
    Please - Por favor (por fah-VOR)
    Thank you - Gracias (GRAH-syahs)
    Yes - Sí (see)
    No - No (noh)
    Let's practice using a simple greeting. How would you say "Hello, how are you?" in Spanish?

    User: Hola, Como estas
    AI Assistant: 
    Wow! Brilliant, you have used a Spanish greeting correctly- 
    "¿Cómo estás?" is correct in Spanish. It means "How are you?" and is used in a familiar, informal setting 
    when speaking to one person. If you're addressing someone in a formal context or speaking to multiple people,
    you would say "¿Cómo está?" or "¿Cómo están?" respectively. 
    Your follow up response to this should be- 
    "¡Hola! Estoy bien, ¿y tú? ¿Cómo te ha ido aprendiendo español hasta ahora? which means
    Hello! I'm doing well, and you? How has it been going learning Spanish so far?""

    Here's a breakdown:

    "¡Hola!" means "Hello!"
    "Estoy bien" means "I'm well"
    "¿y tú?" means "and you?"
    "¿Cómo te ha ido aprendiendo español hasta ahora?" translates to "How has it been going learning Spanish so far?"
    Would you like to practice responding to this question in Spanish?


When teaching:
- Keep responses concise but informative
- Provide examples in both the target language and English
- Offer pronunciation tips
- Include cultural notes when relevant
- Encourage practice through conversation
- Do not repeat the previous response and duplicate it. 
- Don't just respond in the selected language without translating it. User is still learning the language.
  And will not understand what you are saying. When you are translating always break up a sentence if it is big 
  and then explain the user what it means. 
- Also use bullet points while providing examples. 


You have access to translation and text-to-speech capabilities. Use them to enhance the learning experience.
Remember the user's progress and preferences throughout the conversation."""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="chat_history"),
    ("user", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad")
])

# Set up conversation memory
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# Create Agent with tools
agent = create_openai_functions_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, memory=memory, verbose=True)

# Streamlit UI
st.title("🌍 Language Learning Assistant")
st.markdown("Chat with me to learn new languages! I can help with translations, pronunciation, and more.")

# Language selection
languages = {
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Italian": "it",
    "Japanese": "ja",
    "Chinese": "zh-cn",
    "Korean": "ko",
    "Russian": "ru"
}

selected_language = st.sidebar.selectbox(
    "Select target language",
    list(languages.keys())
)

if "selected_language" not in st.session_state or st.session_state.selected_language != selected_language:
    st.session_state.selected_language = selected_language
    memory.clear()  # Reset memory to avoid repeating initial responses
    st.session_state.messages = []  # Reset chat messages
    st.rerun()


# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Add initial greeting
    welcome_msg = f"Hello! I'm your language learning assistant. I see you're interested in learning {selected_language}. How can I help you today?"
    st.session_state.messages.append({"role": "assistant", "content": welcome_msg})

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "audio_file" in message and os.path.exists(message["audio_file"]):
            play_audio(message["audio_file"])

# Chat input
if prompt := st.chat_input("Type your message here..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate AI response
    with st.chat_message("assistant"):
        response = agent_executor.invoke({
            "input": f"You are teaching {selected_language}."
                     f"Continue the conversation naturally without repeating introductions. "
                     f"Here is the latest user message: {prompt}"
                     """When you are responding to the user in the language 
                        he wants to learn, always translate in English"""


        })
        print("Chat History:", st.session_state.messages)

        ai_response = response['output']
        st.markdown(ai_response)
        
        # Generate audio for responses in target language
        if any(char.isalpha() for char in ai_response):
            audio_file = f"temp_audio_{int(time.time())}.mp3"
            text_to_speech(ai_response, audio_file)
            play_audio(audio_file)
            
            # Store audio file reference
            message = {"role": "assistant", "content": ai_response, "audio_file": audio_file}
        else:
            message = {"role": "assistant", "content": ai_response}
            
        st.session_state.messages.append(message)

# Add a clear button
if st.sidebar.button("Clear Conversation"):
    cleanup_audio_files()  # Clean up audio files
    st.session_state.messages = []
    memory.clear()
    st.rerun()

# Add some helpful learning resources
with st.sidebar:
    st.markdown("### Quick Language Tips")
    st.markdown("1. Listen to the pronunciation carefully")
    st.markdown("2. Practice speaking out loud")
    st.markdown("3. Try to form complete sentences")
    st.markdown("4. Don't be afraid to make mistakes")
    
    st.markdown("### Sample Questions")
    st.markdown("- How do I say 'Hello' in [language]?")
    st.markdown("- Can you explain the basic grammar rules?")
    st.markdown("- What's a common phrase I should know?")
    st.markdown("- Tell me about [language] culture")

# Cleanup audio files when the app is closed
if st.runtime.exists():
    cleanup_audio_files()

