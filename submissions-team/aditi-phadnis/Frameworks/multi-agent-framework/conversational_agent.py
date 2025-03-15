from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import Tool
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from models import MultiInputMemory, UserProfile
from config import DEFAULT_LANGUAGE

class ConversationAgent:
    def __init__(self, llm: ChatOpenAI):
        include_keys = ["target_language", "difficulty_level"]
        self.llm = llm
        self.memory = MultiInputMemory(memory_key="chat_history", 
                                       include_keys=include_keys,  
                                       return_messages=True)

        # Define tools for the agent
        self.tools = [
            Tool(name="Translation", func=self.translate_text, description="Translates text between languages"),
            Tool(name="LanguageDetection", func=self.detect_language, description="Detects the language of the provided text"),
            # Tool(name="PronunciationCheck", func=self.check_pronunciation, description="Provides feedback on pronunciation"),
            Tool(name="RequestExerciseGeneration", func=self.request_exercise, description="Requests an exercise based on context")
        ]
        
        # Define prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a multilingual AI language tutor.
            When responding in {target_language}, always provide the English translation immediately after.
            Your responses should follow this format and should be in Markdown Language:
            

             
             {target_language} | English Translation
            :------------------------------------------------------ | :------------------------| 
            [Response in {target_language}] | [Translation in English]

            
            Provide helpful, engaging, and educational responses for learners of all levels."""),
            ("user", "{input}"),
            ("assistant", "{agent_scratchpad}")
        ])
        
        # Create agent
        self.agent = create_openai_functions_agent(llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, memory=self.memory, verbose=True)
    
    def translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translates text between languages."""
        return f"Translating '{text}' from {source_lang} to {target_lang}."
    
    def detect_language(self, text: str) -> str:
        """Detects the language of given text."""
        return "Detected language: English"  # Placeholder implementation
    
    # def check_pronunciation(self, audio_text: str, expected_text: str, language: str) -> str:
    #     """Provides feedback on pronunciation."""
    #     return "Pronunciation feedback: Good"  # Placeholder implementation
    
    def request_exercise(self, difficulty: str, focus_area: str) -> str:
        """Requests an exercise from the Exercise Agent."""
        return f"Requesting a {difficulty} exercise focusing on {focus_area}."
    
    def respond(self, user_input: str, user_profile: UserProfile) -> str:
        """Generate a response to user input."""
        response = self.agent_executor.invoke({
            "input": user_input,
            "target_language": user_profile.target_language,
            "difficulty_level": user_profile.difficulty_level,
            "learning_focus": ", ".join(user_profile.learning_focus)
        })
        user_profile.conversation_history.append({"user": user_input, "agent": response["output"]})
        return response["output"]
