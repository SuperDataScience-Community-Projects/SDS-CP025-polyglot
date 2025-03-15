import os
import streamlit as st
import speech_recognition as sr
from pydub import AudioSegment
from pydub.playback import play
import tempfile
import uuid
from typing import Dict, Any, List, Optional, Tuple
from langchain.memory.chat_memory import BaseChatMemory

from pydantic import BaseModel, Field
from langchain.agents import AgentType, AgentExecutor, create_openai_functions_agent
from langchain.memory import ConversationBufferMemory
from langchain.memory.chat_memory import BaseChatMemory


from langchain.prompts import PromptTemplate, MessagesPlaceholder, ChatPromptTemplate
from langchain.tools import Tool
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Constants
DEFAULT_LANGUAGE = "Spanish"
DIFFICULTY_LEVELS = ["Beginner", "Intermediate", "Advanced"]

# Initialize OpenAI Model
llm = ChatOpenAI(temperature=0.2, 
                 model="gpt-4-turbo", 
                 streaming=True)

# Data Models
class UserProfile(BaseModel):
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    target_language: str = DEFAULT_LANGUAGE
    difficulty_level: str = "Beginner"
    learning_focus: List[str] = ["Conversation", "Grammar", "Vocabulary"]
    strengths: List[str] = []
    weaknesses: List[str] = []
    conversation_history: List[Dict] = []
    exercise_history: List[Dict] = []
    feedback_history: List[Dict] = []


class MultiInputMemory(BaseChatMemory):
    """Memory class that handles multiple input keys and combines them."""
    
    def __init__(self, 
                memory_key: str = "chat_history", 
                primary_input_key: str = "input", 
                include_keys: List[str] = None, 
                output_key: str = "output", 
                return_messages: bool = True):
        super().__init__(memory_key=memory_key, 
                        output_key=output_key, 
                        return_messages=return_messages)
        self.primary_input_key = primary_input_key
        self.include_keys = include_keys or []
        self.chat_memory.messages = []
    
    def memory_variables(self) -> List[str]:
        """Return the memory variables."""
        return [self.memory_key] + self.include_keys


    def _get_input_output(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> Tuple[str, str]:
        """Extract and format input and output from chain inputs and outputs."""
        # Use primary input key if available
        if self.primary_input_key in inputs:
            primary_input = inputs[self.primary_input_key]
            
            # Optionally include other keys
            additional_info = ""
            if self.include_keys:
                additional_parts = []
                for key in self.include_keys:
                    if key in inputs and key != self.primary_input_key:
                        additional_parts.append(f"{key}: {inputs[key]}")
                if additional_parts:
                    additional_info = f" [{', '.join(additional_parts)}]"
            
            input_str = f"{primary_input}{additional_info}"
        else:
            # Fallback: concatenate all inputs
            input_str = "; ".join(f"{k}: {v}" for k, v in inputs.items())
        
        output_str = outputs.get(self.output_key, "")
        return input_str, output_str
    
    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Return history in format appropriate for the prompt."""
        return {self.memory_key: self.chat_memory.messages}


# Conversation Agent
class ConversationAgent:
      

    def __init__(self, llm):
        include_keys = ["target_language", "difficulty_level"]
        self.llm = llm
        self.memory = MultiInputMemory(memory_key="chat_history",     
                                        primary_input_key="input",
                                        include_keys= include_keys,  # Optional
                                        return_messages=True
                                    )

        # Define tools for the agent
        self.tools = [
            Tool(
                name="Translation",
                func=self.translate_text,
                description="Translates text between English and the target language"
            ),
            Tool(
                name="LanguageDetection",
                func=self.detect_language,
                description="Detects the language of the provided text"
            ),
            Tool(
                name="PronunciationCheck",
                func=self.check_pronunciation,
                description="Provides feedback on pronunciation of text"
            ),
            Tool(
                name="RequestExerciseGeneration",
                func=self.request_exercise,
                description="Requests an exercise based on the conversation context"
            )
        ]
        
        # Define prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a friendly and patient language tutor specialized in teaching {target_language}. 
            Adjust your responses to the user's {difficulty_level} level.
            Engage the user in natural conversation, gently correct errors, and provide explanations when needed.
            If the user speaks in English, respond with both {target_language} and English.
            If the user speaks in {target_language}, respond in {target_language} with English translations.
            Focus on their learning goals: {learning_focus}."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            ("assistant", "{agent_scratchpad}")
        ])
        
        # Create agent
        self.agent = create_openai_functions_agent(llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent, 
            tools=self.tools, 
            memory=self.memory,
            verbose=True
        )
    
    def translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translates text between languages"""
        prompt = PromptTemplate.from_template(
            "Translate the following {source_lang} text to {target_lang}: {text}\n\nTranslation:"
        )
        chain = prompt | self.llm
        result = chain.invoke({"source_lang": source_lang, "target_lang": target_lang, "text": text})
        return result.content if hasattr(result, "content") else str(result)
    
    def detect_language(self, text: str) -> str:
        """Detects the language of given text"""
        prompt = PromptTemplate.from_template(
            "Identify the language of the following text. Respond with only the language name: {text}"
        )
        chain = prompt | self.llm
        result = chain.invoke({"text": text})
        return result.content if hasattr(result, "content") else str(result)
    
    def check_pronunciation(self, audio_text: str, expected_text: str, language: str) -> str:
        """Provides feedback on pronunciation based on audio transcription"""
        prompt = PromptTemplate.from_template(
            """Compare the user's spoken text with the expected text and provide pronunciation feedback:
            
            Language: {language}
            Expected Text: {expected_text}
            Transcribed Audio: {audio_text}
            
            Provide specific feedback on pronunciation errors, accent, and clarity:"""
        )
        chain = prompt | self.llm
        result = chain.invoke({
            "language": language,
            "expected_text": expected_text,
            "audio_text": audio_text
        })
        return result.content if hasattr(result, "content") else str(result)
    
    def request_exercise(self, difficulty: str, focus_area: str) -> str:
        """Requests an exercise to be generated by the Exercise Agent"""
        return f"Requesting a {difficulty} exercise focusing on {focus_area}"
    
    def process_voice_input(self, audio_file):
        """Process voice input and convert to text"""
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data)
                return text
            except:
                return "Sorry, I couldn't understand the audio."
    
    def respond(self, user_input: str, user_profile: UserProfile) -> str:
        """Generate a response to user input"""

        # Create a combined input for memory purposes
        combined_input = f"User input: {user_input} (Target language: {user_profile.target_language}, " \
                         f"Difficulty: {user_profile.difficulty_level}, " \
                         f"Focus: {', '.join(user_profile.learning_focus)})"

        response = self.agent_executor.invoke({
            "input": combined_input,
            "target_language": user_profile.target_language,
            "difficulty_level": user_profile.difficulty_level,
            "learning_focus": ", ".join(user_profile.learning_focus)
        })
        
        # Add to conversation history
        user_profile.conversation_history.append({
            "user": user_input,
            "agent": response["output"]
        })
        
        return response["output"]

# Exercise Generator Agent
class ExerciseGeneratorAgent:
    def __init__(self, llm):
        self.llm = llm
        
        # Define tools
        self.tools = [
            Tool(
                name="GenerateVocabularyExercise",
                func=self.generate_vocabulary_exercise,
                description="Generates vocabulary exercises based on difficulty and theme"
            ),
            Tool(
                name="GenerateGrammarExercise",
                func=self.generate_grammar_exercise,
                description="Generates grammar exercises based on difficulty and grammar point"
            ),
            Tool(
                name="GenerateConversationExercise",
                func=self.generate_conversation_exercise,
                description="Generates conversation practice exercises based on scenario"
            ),
            Tool(
                name="GenerateComprehensionExercise",
                func=self.generate_comprehension_exercise,
                description="Generates reading or listening comprehension exercises"
            )
        ]
        
        # Define prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert language exercise creator specialized in {target_language}.
            Create engaging, relevant exercises at {difficulty_level} level.
            Focus on the user's learning needs: {learning_focus}.
            Address their specific weaknesses: {weaknesses}.
            Build on their established strengths: {strengths}.
            Reference recent conversation topics when relevant."""),
            ("user", "{input}"),
            ("assistant", "{agent_scratchpad}")
        ])
        
        # Create agent
        self.agent = create_openai_functions_agent(llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True
        )
    
    def generate_vocabulary_exercise(self, difficulty: str, theme: str ="Everyday Conversation" , count: int = 5) -> Dict:
        """Generates vocabulary exercises based on theme and difficulty"""
        prompt = PromptTemplate.from_template(
            """Create a vocabulary exercise with {count} items about {theme} at {difficulty} level.
            Include:
            1. Word or phrase in target language
            2. Translation to English
            3. Example sentence using the word
            4. Multiple choice or fill-in-the-blank exercise
            
            Format as a structured dictionary suitable for display in an app."""
        )
        chain = prompt | self.llm
        result = chain.invoke({"difficulty": difficulty, "theme": theme, "count": count})
        
        # Process into structured format
        content = result.content if hasattr(result, "content") else str(result)
        return {
            "type": "vocabulary",
            "theme": theme,
            "difficulty": difficulty,
            "content": content
        }
    
    def generate_grammar_exercise(self, difficulty: str, grammar_point: str, count: int = 3) -> Dict:
        """Generates grammar exercises based on specific grammar points"""
        prompt = PromptTemplate.from_template(
            """Create a grammar exercise focusing on {grammar_point} at {difficulty} level.
            Include:
            1. Brief explanation of the grammar rule
            2. {count} example sentences showing correct usage
            3. {count} practice sentences for the user to complete
            4. Answer key with explanations
            
            Format as a structured dictionary suitable for display in an app."""
        )
        chain = prompt | self.llm
        result = chain.invoke({"difficulty": difficulty, "grammar_point": grammar_point, "count": count})
        
        content = result.content if hasattr(result, "content") else str(result)
        return {
            "type": "grammar",
            "grammar_point": grammar_point,
            "difficulty": difficulty,
            "content": content
        }
    
    def generate_conversation_exercise(self, difficulty: str, scenario: str) -> Dict:
        """Generates conversation practice exercises based on scenarios"""
        prompt = PromptTemplate.from_template(
            """Create a conversation practice exercise set in a {scenario} scenario at {difficulty} level.
            Include:
            1. Setting description
            2. Conversation objective
            3. Key vocabulary and phrases needed
            4. Conversation starter
            5. Potential response paths
            
            Format as a structured dictionary suitable for display in an app."""
        )
        chain = prompt | self.llm
        result = chain.invoke({"difficulty": difficulty, "scenario": scenario})
        
        content = result.content if hasattr(result, "content") else str(result)
        return {
            "type": "conversation",
            "scenario": scenario,
            "difficulty": difficulty,
            "content": content
        }
    
    def generate_comprehension_exercise(self, difficulty: str, topic: str, exercise_type: str = "reading") -> Dict:
        """Generates reading or listening comprehension exercises"""
        prompt = PromptTemplate.from_template(
            """Create a {exercise_type} comprehension exercise about {topic} at {difficulty} level.
            Include:
            1. A {exercise_type} passage (50-100 words for beginner, 100-200 for intermediate, 200-300 for advanced)
            2. 3-5 comprehension questions
            3. Answer key with explanations
            
            Format as a structured dictionary suitable for display in an app."""
        )
        chain = prompt | self.llm
        result = chain.invoke({
            "difficulty": difficulty, 
            "topic": topic, 
            "exercise_type": exercise_type
        })
        
        content = result.content if hasattr(result, "content") else str(result)
        return {
            "type": f"{exercise_type}_comprehension",
            "topic": topic,
            "difficulty": difficulty,
            "content": content
        }
    
    def generate_exercise(self, exercise_type: str, user_profile: UserProfile, context: Dict = None) -> Dict:
        """Generate an exercise based on user profile and context"""
        input_data = {
            "input": f"Generate a {exercise_type} exercise appropriate for the user's profile",
            "target_language": user_profile.target_language,
            "difficulty_level": user_profile.difficulty_level,
            "learning_focus": ", ".join(user_profile.learning_focus),
            "strengths": ", ".join(user_profile.strengths) if user_profile.strengths else "None specified",
            "weaknesses": ", ".join(user_profile.weaknesses) if user_profile.weaknesses else "None specified"
        }
        
        if context:
            input_data["input"] += f" based on their recent conversation about {context.get('topic', 'general topics')}"
        
        response = self.agent_executor.invoke(input_data)
        
        # Add to exercise history
        exercise = response["output"]
        user_profile.exercise_history.append(exercise)
        
        return exercise

# Feedback & Context Agent
class FeedbackContextAgent:
    def __init__(self, llm):
        self.llm = llm
        
        # Define tools
        self.tools = [
            Tool(
                name="AnalyzeProgress",
                func=self.analyze_user_progress,
                description="Analyzes user progress and patterns based on history"
            ),
            Tool(
                name="GenerateFeedback",
                func=self.generate_feedback,
                description="Generates constructive feedback based on user performance"
            ),
            Tool(
                name="UpdateUserProfile",
                func=self.update_user_profile,
                description="Updates user profile based on observed patterns"
            ),
            Tool(
                name="RecommendNextSteps",
                func=self.recommend_next_steps,
                description="Recommends next learning steps or focus areas"
            )
        ]
        
        # Define prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a thoughtful learning analytics system specialized in language learning.
            Analyze user interactions, provide constructive feedback, and maintain learning context.
            Identify patterns in the user's {target_language} learning journey.
            Track progress at their {difficulty_level} level.
            Focus on their stated learning goals: {learning_focus}."""),
            ("user", "{input}"),
            ("assistant", "{agent_scratchpad}")
        ])
        
        # Create agent
        self.agent = create_openai_functions_agent(llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True
        )
    
    def analyze_user_progress(self, user_profile: Dict) -> Dict:
        """Analyzes user progress patterns based on history"""
        # Convert the user profile to a string representation for the LLM
        profile_str = f"""
        Target Language: {user_profile.get('target_language')}
        Difficulty Level: {user_profile.get('difficulty_level')}
        Learning Focus: {', '.join(user_profile.get('learning_focus', []))}
        Strengths: {', '.join(user_profile.get('strengths', []))}
        Weaknesses: {', '.join(user_profile.get('weaknesses', []))}
        Conversation History Size: {len(user_profile.get('conversation_history', []))} entries
        Exercise History Size: {len(user_profile.get('exercise_history', []))} exercises
        """
        
        prompt = PromptTemplate.from_template(
            """Analyze the following user language learning profile and identify progress patterns:
            
            {profile}
            
            Provide insights on:
            1. Learning patterns and trends
            2. Areas of improvement
            3. Areas that need more focus
            4. Overall progress assessment
            
            Format your analysis as a structured report:"""
        )
        chain = prompt | self.llm
        result = chain.invoke({"profile": profile_str})
        
        content = result.content if hasattr(result, "content") else str(result)
        return {
            "type": "progress_analysis",
            "content": content
        }
    
    def generate_feedback(self, user_input: str, agent_response: str, language: str) -> Dict:
        """Generates constructive feedback on a specific interaction"""
        prompt = PromptTemplate.from_template(
            """Review this language learning interaction and provide constructive feedback:
            
            Language: {language}
            User Input: {user_input}
            Tutor Response: {agent_response}
            
            Provide feedback on:
            1. Grammar and vocabulary usage
            2. Communication effectiveness
            3. Specific improvements to consider
            4. Positive reinforcement of what was done well
            
            Format feedback in a supportive, encouraging tone:"""
        )
        chain = prompt | self.llm
        result = chain.invoke({
            "language": language,
            "user_input": user_input,
            "agent_response": agent_response
        })
        
        content = result.content if hasattr(result, "content") else str(result)
        return {
            "type": "interaction_feedback",
            "content": content
        }
    
    def update_user_profile(self, user_profile: UserProfile, new_observations: Dict) -> Dict:
        """Updates user profile based on new observations"""
        # This function would actually modify the user profile object
        # Here we'll simulate the process
        
        if "strengths" in new_observations and new_observations["strengths"]:
            for strength in new_observations["strengths"]:
                if strength not in user_profile.strengths:
                    user_profile.strengths.append(strength)
        
        if "weaknesses" in new_observations and new_observations["weaknesses"]:
            for weakness in new_observations["weaknesses"]:
                if weakness not in user_profile.weaknesses:
                    user_profile.weaknesses.append(weakness)
        
        if "difficulty_adjustment" in new_observations:
            if new_observations["difficulty_adjustment"] in DIFFICULTY_LEVELS:
                user_profile.difficulty_level = new_observations["difficulty_adjustment"]
        
        return {
            "type": "profile_update",
            "updated_profile": user_profile.dict()
        }
    
    def recommend_next_steps(self, user_profile: UserProfile) -> Dict:
        """Recommends next learning steps based on user profile"""
        # Convert profile to string for LLM processing
        profile_str = f"""
        Target Language: {user_profile.target_language}
        Difficulty Level: {user_profile.difficulty_level}
        Learning Focus: {', '.join(user_profile.learning_focus)}
        Strengths: {', '.join(user_profile.strengths) if user_profile.strengths else "None specified"}
        Weaknesses: {', '.join(user_profile.weaknesses) if user_profile.weaknesses else "None specified"}
        """
        
        prompt = PromptTemplate.from_template(
            """Based on this language learner's profile, recommend the next steps in their learning journey:
            
            {profile}
            
            Provide recommendations for:
            1. Next topics or grammar points to focus on
            2. Specific exercise types that would be most beneficial
            3. Learning strategies to address weaknesses
            4. Ways to leverage and build on strengths
            
            Format recommendations as an actionable plan:"""
        )
        chain = prompt | self.llm
        result = chain.invoke({"profile": profile_str})
        
        content = result.content if hasattr(result, "content") else str(result)
        return {
            "type": "learning_recommendations",
            "content": content
        }
    
    def process_interaction(self, user_input: str, agent_response: str, user_profile: UserProfile) -> Dict:
        """Process an interaction and provide feedback/updates"""
        response = self.agent_executor.invoke({
            "input": f"Analyze this interaction: User: '{user_input}' Agent: '{agent_response}'",
            "target_language": user_profile.target_language,
            "difficulty_level": user_profile.difficulty_level,
            "learning_focus": ", ".join(user_profile.learning_focus)
        })
        
        # Add to feedback history
        feedback = response["output"]
        user_profile.feedback_history.append({
            "user_input": user_input,
            "agent_response": agent_response,
            "feedback": feedback
        })
        
        return feedback

# Idioms Agent
class IdiomsAgent:
    def __init__(self, llm):
        self.llm = llm
        
        # Define tools
        self.tools = [
            Tool(
                name="ExplainIdiom",
                func=self.explain_idiom,
                description="Explains the meaning and usage of an idiom"
            ),
            Tool(
                name="DetectIdioms",
                func=self.detect_idioms,
                description="Detects idioms in a given text"
            ),
            Tool(
                name="SuggestIdioms",
                func=self.suggest_idioms,
                description="Suggests idioms related to a topic or situation"
            ),
            Tool(
                name="ExplainSarcasm",
                func=self.explain_sarcasm,
                description="Explains sarcastic expressions and their cultural context"
            )
        ]
        
        # Define prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert in {target_language} idioms, expressions, and cultural nuances.
            Help users understand and use idioms, colloquialisms, and sarcasm appropriate to their {difficulty_level} level.
            Explain cultural context and usage when introducing new expressions.
            Provide examples that illustrate when and how to use each expression."""),
            ("user", "{input}"),
            ("assistant", "{agent_scratchpad}")
        ])
        
        # Create agent
        self.agent = create_openai_functions_agent(llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True
        )
    
    def explain_idiom(self, idiom: str, language: str) -> Dict:
        """Explains the meaning and usage of an idiom"""
        prompt = PromptTemplate.from_template(
            """Explain the following idiom in {language}:
            
            Idiom: {idiom}
            
            Provide:
            1. Literal translation
            2. Actual meaning
            3. Origin/etymology if known
            4. Example usage in a sentence
            5. Equivalent English idiom if one exists
            6. Cultural context for usage
            
            Format your explanation in a structured way:"""
        )
        chain = prompt | self.llm
        result = chain.invoke({"idiom": idiom, "language": language})
        
        content = result.content if hasattr(result, "content") else str(result)
        return {
            "type": "idiom_explanation",
            "idiom": idiom,
            "language": language,
            "content": content
        }
    
    def detect_idioms(self, text: str, language: str) -> Dict:
        """Detects idioms in a given text"""
        prompt = PromptTemplate.from_template(
            """Identify any idioms, colloquialisms, or special expressions in this {language} text:
            
            Text: {text}
            
            For each idiom found, provide:
            1. The idiom itself
            2. Its meaning
            3. How it's used in the context
            
            If no idioms are found, state that none were detected:"""
        )
        chain = prompt | self.llm
        result = chain.invoke({"text": text, "language": language})
        
        content = result.content if hasattr(result, "content") else str(result)
        return {
            "type": "idiom_detection",
            "text": text,
            "language": language,
            "content": content
        }
    
    def suggest_idioms(self, topic: str, language: str, difficulty: str) -> Dict:
        """Suggests idioms related to a topic or situation"""
        prompt = PromptTemplate.from_template(
            """Suggest 3-5 {language} idioms or expressions related to {topic} that would be appropriate for a {difficulty} level language learner.
            
            For each idiom, provide:
            1. The idiom in {language}
            2. Literal translation
            3. Actual meaning
            4. Example usage in a sentence
            5. When it would be appropriate to use
            
            Format your suggestions in a clear, structured way:"""
        )
        chain = prompt | self.llm
        result = chain.invoke({
            "topic": topic, 
            "language": language,
            "difficulty": difficulty
        })
        
        content = result.content if hasattr(result, "content") else str(result)
        return {
            "type": "idiom_suggestions",
            "topic": topic,
            "language": language,
            "difficulty": difficulty,
            "content": content
        }
    
    def explain_sarcasm(self, expression: str, language: str) -> Dict:
        """Explains sarcastic expressions and their cultural context"""
        prompt = PromptTemplate.from_template(
            """Explain the following potentially sarcastic expression in {language}:
            
            Expression: {expression}
            
            Provide:
            1. Literal meaning
            2. Sarcastic intention
            3. Cultural context
            4. Tone and delivery considerations
            5. When it would be appropriate/inappropriate to use
            6. Example dialogue showing its usage
            
            Format your explanation in a structured way:"""
        )
        chain = prompt | self.llm
        result = chain.invoke({"expression": expression, "language": language})
        
        content = result.content if hasattr(result, "content") else str(result)
        return {
            "type": "sarcasm_explanation",
            "expression": expression,
            "language": language,
            "content": content
        }
    
    def process_request(self, request_type: str, content: str, user_profile: UserProfile) -> Dict:
        """Process a request for the idioms agent"""
        input_text = f"{request_type} request: {content}"
        
        response = self.agent_executor.invoke({
            "input": input_text,
            "target_language": user_profile.target_language,
            "difficulty_level": user_profile.difficulty_level
        })
        
        return response["output"]

# Orchestrator
class Orchestrator:
    def __init__(self, llm):
        self.llm = llm
        
        # Initialize agents
        self.conversation_agent = ConversationAgent(llm)
        self.exercise_agent = ExerciseGeneratorAgent(llm)
        self.feedback_agent = FeedbackContextAgent(llm)
        self.idioms_agent = IdiomsAgent(llm)
        
        # Create a router chain to determine which agent should handle the request
        self.router_chain = self.create_router_chain()
    
    def create_router_chain(self):
        """Creates a chain to route requests to the appropriate agent"""
        router_prompt = PromptTemplate.from_template(
            """Determine which agent should handle this user input:
            
            User Input: {input}
            User Context: {context}
            
            Choose one of the following agents:
            1. conversation - for general conversation, questions, and practice
            2. exercise - for requests related to exercises, quizzes, or drills
            3. idioms - for questions about idioms, expressions, or cultural language
            4. feedback - for requests about progress, feedback, or learning analytics
            
            Return ONLY the name of the agent that should handle this (conversation, exercise, idioms, or feedback):"""
        )
        
        return router_prompt | self.llm
    
    def extract_agent_name(self, response):
        """Extract the agent name from the router response"""
        if hasattr(response, "content"):
            content = response.content.lower().strip()
        else:
            content = str(response).lower().strip()
        
        # Handle variations in the response
        if "conversation" in content:
            return "conversation"
        elif "exercise" in content:
            return "exercise"
        elif "idiom" in content:
            return "idioms"
        elif "feedback" in content:
            return "feedback"
        else:
            # Default to conversation agent
            return "conversation"
    
    def process_input(self, user_input: str, user_profile: UserProfile, is_voice: bool = False, audio_file=None):
        """Process user input and route to appropriate agent"""
        # Handle voice input if provided
        if is_voice and audio_file:
            user_input = self.conversation_agent.process_voice_input(audio_file)
        
        # Create context for routing
        context = {
            "target_language": user_profile.target_language,
            "difficulty_level": user_profile.difficulty_level,
            "learning_focus": user_profile.learning_focus,
            "recent_topics": [entry["user"] for entry in user_profile.conversation_history[-3:]] if user_profile.conversation_history else []
        }
        
        # Determine which agent should handle the request
        router_response = self.router_chain.invoke({
            "input": user_input,
            "context": str(context)
        })
        
        agent_name = self.extract_agent_name(router_response)
        
        # Route to appropriate agent
        if agent_name == "conversation":
            response = self.conversation_agent.respond(user_input, user_profile)
            
            # Get feedback on the interaction
            feedback = self.feedback_agent.process_interaction(user_input, response, user_profile)
            
            return {
                "agent": "conversation",
                "response": response,
                "feedback": feedback
            }
            
        elif agent_name == "exercise":
            # Determine exercise type from input
            exercise_type_prompt = PromptTemplate.from_template(
                """Based on this user request, what type of exercise should be generated? 
                Choose from: vocabulary, grammar, conversation, reading_comprehension, listening_comprehension.
                
                User request: {input}
                
                Return ONLY the exercise type:"""
            )
            exercise_type_chain = exercise_type_prompt | self.llm
            exercise_type_response = exercise_type_chain.invoke({"input": user_input})
            exercise_type = exercise_type_response.content.strip() if hasattr(exercise_type_response, "content") else str(exercise_type_response).strip()
            
            # Generate exercise
            exercise = self.exercise_agent.generate_exercise(exercise_type, user_profile)
            
            return {
                "agent": "exercise",
                "response": exercise
            }
            
        elif agent_name == "idioms":
            # Determine request type
            idiom_request_prompt = PromptTemplate.from_template(
                """Based on this user request about idioms or expressions, what type of help do they need? 
                Choose from: explain_idiom, detect_idioms, suggest_idioms, explain_sarcasm.
                
                User request: {input}
                
                Return ONLY the request type:"""
            )
            idiom_request_chain = idiom_request_prompt | self.llm
            idiom_request_response = idiom_request_chain.invoke({"input": user_input})
            request_type = idiom_request_response.content.strip() if hasattr(idiom_request_response, "content") else str(idiom_request_response).strip()
            
            # Process idiom request
            idiom_response = self.idioms_agent.process_request(request_type, user_input, user_profile)
            
            return {
                "agent": "idioms",
                "response": idiom_response
            }
            
        elif agent_name == "feedback":
            # Generate progress analysis and recommendations
            progress_analysis = self.feedback_agent.analyze_user_progress(user_profile.__dict__)
            recommendations = self.feedback_agent.recommend_next_steps(user_profile)
            
            return {
                "agent": "feedback",
                "response": {
                    "progress_analysis": progress_analysis,
                    "recommendations": recommendations
                }
            }
        
        else:
            # Default to conversation agent
            response = self.conversation_agent.respond(user_input, user_profile)
            return {
                "agent": "conversation",
                "response": response
            }
    
    def generate_system_message(self, message_type: str, user_profile: UserProfile):
        """Generate system messages to guide the user"""
        if message_type == "welcome":
            prompt = PromptTemplate.from_template(
                """Generate a friendly welcome message for a new language learner.
                Target language: {language}
                Difficulty level: {difficulty}
                
                Include:
                1. A warm greeting
                2. Brief explanation of what the app can do
                3. Suggestion for how to start
                
                Use a friendly, encouraging tone:"""
            )
            chain = prompt | self.llm
            result = chain.invoke({
                "language": user_profile.target_language,
                "difficulty": user_profile.difficulty_level
            })
            
            return result.content if hasattr(result, "content") else str(result)
            
        elif message_type == "suggestion":
            # Get recent topics from conversation history
            recent_topics = []
            for entry in user_profile.conversation_history[-5:]:
                if "user" in entry:
                    recent_topics.append(entry["user"])
            
            prompt = PromptTemplate.from_template(
                """Based on recent interactions, suggest what the user could do next in their language learning journey.
                
                Target language: {language}
                Difficulty level: {difficulty}
                Recent topics: {topics}
                
                Suggest 1-2 specific actions they could take to advance their learning:"""
            )
            chain = prompt | self.llm
            result = chain.invoke({
                "language": user_profile.target_language,
                "difficulty": user_profile.difficulty_level,
                "topics": str(recent_topics)
            })
            
            return result.content if hasattr(result, "content") else str(result)

# Streamlit UI
def create_streamlit_app():
    st.title("🌍 Polyglot - AI Language Tutor")
    
    # Initialize session state
    if 'user_profile' not in st.session_state:
        st.session_state.user_profile = UserProfile()
    
    if 'orchestrator' not in st.session_state:
        st.session_state.orchestrator = Orchestrator(llm)
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Sidebar for settings
    with st.sidebar:
        st.header("Settings")
        
        # Language selection
        selected_language = st.selectbox(
            "Target Language", 
            ["Spanish", "French", "German", "Italian", "Portuguese", "Japanese", "Mandarin", "Russian", "Arabic"],
            index=0
        )
        
        # Difficulty level
        selected_difficulty = st.selectbox(
            "Difficulty Level",
            DIFFICULTY_LEVELS,
            index=0
        )
        
        # Learning focus
        selected_focus = st.multiselect(
            "Learning Focus",
            ["Conversation", "Grammar", "Vocabulary", "Reading", "Listening", "Idioms"],
            default=["Conversation", "Grammar", "Vocabulary"]
        )
        
        # Update user profile if changes detected
        if (selected_language != st.session_state.user_profile.target_language or
            selected_difficulty != st.session_state.user_profile.difficulty_level or
            selected_focus != st.session_state.user_profile.learning_focus):
            
            st.session_state.user_profile.target_language = selected_language
            st.session_state.user_profile.difficulty_level = selected_difficulty
            st.session_state.user_profile.learning_focus = selected_focus
            
            # Add system message about profile update
            st.session_state.chat_history.append({
                "role": "system",
                "content": f"Settings updated: {selected_language} ({selected_difficulty})"
            })
        
        # Button to generate exercise
        if st.button("Generate Exercise"):
            # Generate exercise based on user profile
            exercise_response = st.session_state.orchestrator.exercise_agent.generate_exercise(
                "vocabulary", st.session_state.user_profile
            )
            
            # Add to chat history
            st.session_state.chat_history.append({
                "role": "system",
                "content": "Here's an exercise for you:",
                "exercise": exercise_response
            })
        
        # Button to get progress feedback
        if st.button("Check My Progress"):
            if len(st.session_state.user_profile.conversation_history) > 3:
                # Generate progress feedback
                feedback_response = st.session_state.orchestrator.feedback_agent.analyze_user_progress(
                    st.session_state.user_profile.__dict__
                )
                
                # Add to chat history
                st.session_state.chat_history.append({
                    "role": "system",
                    "content": "Here's your learning progress:",
                    "feedback": feedback_response
                })
            else:
                st.session_state.chat_history.append({
                    "role": "system",
                    "content": "Please interact more to receive progress feedback."
                })
    
    # Main chat interface
    st.header("Your Language Learning Assistant")
    
    # Display chat history
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.chat_message("user").write(message["content"])
        elif message["role"] == "assistant":
            with st.chat_message("assistant"):
                st.write(message["content"])
                # Display translation if available
                if "translation" in message and message["translation"]:
                    st.caption(f"Translation: {message['translation']}")
        elif message["role"] == "system":
            with st.chat_message("assistant", avatar="🔔"):
                st.write(message["content"])
                
                # Display exercise if present
                if "exercise" in message:
                    with st.expander("View Exercise"):
                        st.write(message["exercise"]["content"])
                
                # Display feedback if present
                if "feedback" in message:
                    with st.expander("View Feedback"):
                        st.write(message["feedback"]["content"])
    
    # Handle initial welcome message
    if len(st.session_state.chat_history) == 0:
        welcome_msg = st.session_state.orchestrator.generate_system_message(
            "welcome", st.session_state.user_profile
        )
        st.session_state.chat_history.append({
            "role": "system",
            "content": welcome_msg
        })
    
    # Input options
    input_option = st.radio("Input Method", ["Text", "Voice"], horizontal=True)
    
    if input_option == "Text":
        # Text input
        user_input = st.chat_input("Type your message in any language...")
        
        if user_input:
            # Add user message to chat history
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_input
            })
            
            # Process with orchestrator
            response = st.session_state.orchestrator.process_input(
                user_input, st.session_state.user_profile
            )
            
            # Add response to chat history
            if response["agent"] == "conversation":
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response["response"]
                })
            elif response["agent"] == "exercise":
                st.session_state.chat_history.append({
                    "role": "system",
                    "content": "Here's an exercise for you:",
                    "exercise": response["response"]
                })
            elif response["agent"] == "idioms":
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response["response"]
                })
            elif response["agent"] == "feedback":
                st.session_state.chat_history.append({
                    "role": "system",
                    "content": "Here's your learning progress:",
                    "feedback": response["response"]["progress_analysis"]
                })
                
                st.session_state.chat_history.append({
                    "role": "system",
                    "content": "Recommendations for next steps:",
                    "feedback": response["response"]["recommendations"]
                })
            
            # Force refresh
            st.rerun()
    else:
        # Voice input
        audio_file = st.file_uploader("Upload audio", type=["wav", "mp3"])
        
        if st.button("Process Voice") and audio_file is not None:
            # Process voice with orchestrator
            response = st.session_state.orchestrator.process_input(
                "", st.session_state.user_profile, is_voice=True, audio_file=audio_file
            )
            
            # Add transcription to chat history
            if "transcription" in response:
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": response["transcription"]
                })
            
            # Add response to chat history
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response["response"]
            })
            
            # Force refresh
            st.rerun()

# Run the Streamlit app
if __name__ == "__main__":
    create_streamlit_app()
