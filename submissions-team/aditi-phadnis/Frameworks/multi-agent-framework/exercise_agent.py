from langchain.prompts import ChatPromptTemplate
from langchain.tools import Tool
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from models import UserProfile
import json
import random
import time
import logging

# Set up logging
logging.basicConfig(
    filename="exercise_generation.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)



class ExerciseGeneratorAgent:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        
        # Define tools
        self.tools = [
            Tool(name="GenerateExercises", func=self.generate_exercises, description="Creates a set of 3 exercises")
        ]
        
        # Define prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert language exercise creator for {target_language}.
            Design engaging exercises suitable for {difficulty_level} learners.
            Tailor them based on the user's learning focus and past interactions.
            
            **STRICT RULES:**
            - Always return a **valid JSON array**.
            - Each exercise **must** have a `"type"`, `"question"`, `"options"` (if applicable), `"correctAnswer"`, and `"explanation"`.
            - Allowed `"type"` values: `"multiple_choice"`, `"fill_in_the_blank"`, `"matching"`.
            - Before responding, **validate the JSON internally**.
            - If the JSON is invalid, **think step by step** and regenerate it.

            **If your response contains any invalid JSON, retry until it is correct.**"""),
            ("user", "{input}"),
            ("assistant", "{agent_scratchpad}")
        ])
        
        # Create agent
        self.agent = create_openai_functions_agent(llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)
    
    def generate_valid_exercise(self, generation_func, *args, **kwargs):
        """
        Uses ReAct-style reasoning to ensure exercises are valid JSON.
        Logs attempts and corrections for debugging. 
        """
        for attempt in range(3):  # Allow up to 3 self-corrections
            logging.info(f"🔄 Attempt {attempt + 1} for {generation_func.__name__}...")
            print(f"🔄 ReAct Attempt {attempt + 1} for {generation_func.__name__}...")

            exercise = generation_func(*args, **kwargs)

            # Log raw response
            logging.debug(f"Raw response from {generation_func.__name__}: {exercise}")


            # Verify if the output is valid JSON
            if isinstance(exercise, dict) and "type" in exercise and "question" in exercise:
                logging.info(f"✅ Valid JSON generated for {generation_func.__name__}.")
                print(f"✅ Successfully generated {generation_func.__name__}.")
                return exercise  # Return valid exercise

            # Use ReAct reasoning: Why is it invalid?
            print(f"❌ Invalid response from {generation_func.__name__}, reasoning through the issue...")
            # Log invalid response
            logging.warning(f"❌ Invalid response from {generation_func.__name__}, reasoning through the issue...")

            
            react_prompt = f"""
            You generated an invalid JSON response. Here is the response:
            
            ```
            {exercise}
            ```
            
            **Identify the issue** and regenerate a corrected JSON.
            """
            
            corrected_response = self.llm.invoke(react_prompt)
            
            try:
                corrected_exercise = json.loads(
                    corrected_response.content if hasattr(corrected_response, "content") 
                    else str(corrected_response))
                if isinstance(corrected_exercise, dict) and "type" in corrected_exercise and "question" in corrected_exercise:
                    print("✅ Successfully corrected the JSON.")
                    return corrected_exercise
            except json.JSONDecodeError:
                print("⚠️ JSON correction failed, retrying...")
                logging.warning(print("⚠️ JSON correction failed, retrying..."))
        
        print(f"⚠️ Maximum attempts reached. Skipping {generation_func.__name__}.")
        logging.warning(f"⚠️ Maximum attempts reached. Skipping {generation_func.__name__}.")

        return None

    
    def generate_exercises(self, user_profile):
        exercise_prompt= f"""
        You are an AI language tutor generating language exercises. 

        Generate a list of **valid exercises** based on the user's difficulty level: {user_profile.difficulty_level}.

        **Rules:**
        - Always return a **valid JSON array**.
        - Each exercise **must** have a `"type"`, `"question"`, `"options"` (if applicable), `"correctAnswer"`, and `"explanation"`.
        - Allowed `"type"` values: `"single_choice"`, `"fill_in_the_blank"`, `"matching"`.
        - If the LLM cannot generate an exercise, it **must return an empty array** (`[]`), **never** an error message.
          """      
        exercises = []

        # Define Themes for Different Difficulty Levels
        themes = {
            "Beginner": ["Greetings", "Family", "Food", "Colors", "Numbers"],
            "Intermediate": ["Travel", "Work", "Hobbies", "Weather", "Shopping"],
            "Advanced": ["Politics", "Environment", "Technology", "Literature", "Philosophy"]
        }

        # Select a random theme based on the user's difficulty level
        if user_profile.difficulty_level in themes:
            theme = random.choice(themes[user_profile.difficulty_level])
        else:
            theme = "General"

        print(f"DEBUG: Selected Theme = {theme}")  # Debugging

        grammar_topic = {
                "Beginner": [
                    "Nouns and Pronouns",
                    "Basic Verb Conjugation",
                    "Present Tense",
                    "Definite and Indefinite Articles",
                    "Adjectives and Opposites",
                    "Basic Sentence Structure",
                    "Prepositions of Place and Time",
                    "Common Conjunctions (and, but, or)",
                    "Numbers and Counting",
                    "Asking Simple Questions"
                ],
                "Intermediate": [
                    "Past and Future Tenses",
                    "Comparative and Superlative Adjectives",
                    "Modal Verbs (can, must, should, etc.)",
                    "Reflexive Verbs",
                    "Possessive Pronouns and Adjectives",
                    "Adverbs of Frequency and Manner",
                    "Conditional Sentences (If-clauses)",
                    "Relative Clauses (who, which, that)",
                    "Reported Speech",
                    "Gerunds and Infinitives"
                ],
                "Advanced": [
                    "Subjunctive Mood",
                    "Passive Voice",
                    "Advanced Conditional Sentences",
                    "Indirect Questions",
                    "Inversion in Sentences",
                    "Idiomatic Expressions with Verbs",
                    "Nominalization",
                    "Cleft Sentences",
                    "Complex Sentence Structures",
                    "Ellipsis and Substitution"
                ]
            }


        if user_profile.difficulty_level in grammar_topic:
            grammar_topic = random.choice(grammar_topic[user_profile.difficulty_level])
        else:
            grammar_topic = "Nouns and Pronouns"

        print(f"DEBUG: Selected Grammar Topic = {grammar_topic}")  # Debugging

        # Generate Vocabulary Exercise
        # vocab_exercise = self.generate_vocabulary_exercise(user_profile.difficulty_level, user_profile.target_language, theme)
        # if isinstance(vocab_exercise, dict):  # Ensure valid JSON
        #     exercises.append(vocab_exercise)
        
        vocab_exercise = self.generate_valid_exercise(
                    self.generate_vocabulary_exercise,
                    user_profile.difficulty_level,
                    user_profile.target_language,
                    theme
                )
        if isinstance(vocab_exercise, dict):
            exercises.append(vocab_exercise)


        # Generate Grammar Exercise
        grammar_exercise = self.generate_valid_exercise(
            self.generate_grammar_exercise,
            user_profile.difficulty_level, 
            user_profile.target_language, 
            grammar_topic)
        if isinstance(grammar_exercise, dict):  # Ensure valid JSON
            exercises.append(grammar_exercise)
        
        print("DEBUG: General exercises =", exercises)

        return exercises

        
    
    def generate_vocabulary_exercise(self, difficulty: str, target_language: str, theme: str = "Everyday Conversation", count: int = 2,) -> dict:
        """Generates a vocabulary exercise with translations and example sentences in the target language."""
        prompt = f"""Generate {count} vocabulary words in {target_language} for 
        {difficulty} level learners based on the theme '{theme}'. 
        Format your responses as valid JSON:

        {{
            "type": "single_choice",
            "question": "Translate 'hello' to {target_language}",
            "options": ["Hola", "Bonjour", "Ciao", "Hallo"],
            "correctAnswer": "Hola",
            "explanation": "'Hola' means 'hello' in Spanish."
        }}

        Ensure the response is always valid JSON.
        """
        
        response = self.llm.invoke(prompt)

        # Ensure JSON parsing
        try:
            exercise_data = json.loads(response.content if hasattr(response, "content") else str(response))
            return exercise_data
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            print(f"Raw response: {response}")  # Debugging
            return {"error": "Invalid JSON returned from LLM"}

    
    def generate_grammar_exercise(self, difficulty: str, target_language: str, grammar_topic: str = "Verb Conjugation") -> dict:
        """Generates a grammar exercise based on the target language and grammar topic."""
        prompt = f"""Generate a grammar exercise for {difficulty} level learners in {target_language} 
        on the topic '{grammar_topic}'. Provide the response as **valid JSON** in the following format:

        {{
            "type": "single_choice",
            "question": "Choose the correct conjugation of the verb 'ser' (to be) for 'yo' (I):",
            "options": ["soy", "eres", "es", "somos"],
            "correctAnswer": "soy",
            "explanation": "'Soy' is the correct conjugation of 'ser' for the first-person singular pronoun 'yo'."
        }}

        Ensure the JSON response is valid and does not contain extra text.
        Always ensure to provide an English explanation in the Json. 
        """

        response = self.llm.invoke(prompt)

        # Ensure response is valid JSON
        try:
            grammar_exercise = json.loads(response.content if hasattr(response, "content") else str(response))
            return grammar_exercise
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON Decode Error: {e}")
            print(f"❌ Invalid Response: {response}")  # Debugging log
            return {"error": "Invalid JSON returned from LLM"}

    
    def generate_conversation_exercise(self, difficulty: str, target_language: str, scenario: str) -> dict:
        """Generates a conversation role-play exercise in the target language."""

        prompt = f"""Create a role-play conversation exercise in {target_language} 
        for a {difficulty} level learner. The scenario is '{scenario}'.

        Return a JSON object with the following structure:
        {{
        "scenario": "{scenario}",
        "context": "[Optional brief context or setting]",
        "dialogue": [
            {{"speaker": "Person A", "text": "[Line in {target_language}]", "translation": "[English translation]"}},
            {{"speaker": "You", "text": "[Suggested response in {target_language}]", "translation": "[English translation]"}},
            // ... more dialogue turns
        ],
        "questions": [
            {{"prompt": "[Question about the dialogue]", "answer": "[Expected answer]"}},
            // ... more questions
        ]
        }}

        Only include the JSON, no additional text.
        """
        response = self.llm.invoke(prompt)
        try:
            return json.loads(response.content if hasattr(response, "content") else str(response))
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            print(f"Raw response: {response}")  # Print the raw response for debugging
            return {"error": "Invalid JSON returned from LLM"} # Or handle the error as needed

