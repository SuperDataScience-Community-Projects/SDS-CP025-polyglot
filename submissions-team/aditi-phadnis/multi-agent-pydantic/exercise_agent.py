import os
from openai import OpenAI
from pydantic import BaseModel
from config import client, UserProfile, model, temperature, theme, user_profile
import time, random, json, logging
from pydantic_ai import Agent, RunContext
from dataclasses import dataclass




# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------------------------------------------------
# Step 1: Define the response format in a Pydantic model
# --------------------------------------------------------------

class ExerciseFormat(BaseModel):
    question: str # single_choice". "multiple_choice", "fill_in_the_blank", or "matching"
    options: list[str] 
    correctAnswer: str
    explanation: str

class ExerciseFormat(BaseModel):
    exercises: list[ExerciseFormat]


#------------------------------------------------
# Step 2: Set up your Tools 
#------------------------------------------------     

class ExerciseGeneratorAgent:
    def __init__(self, target_language: str, difficulty_level: str, learning_focus: str):
        self.target_language = target_language
        self.difficulty_level = difficulty_level
        self.learning_focus = learning_focus

    def generate_exercises(self, theme: str):
        """Generates a set of exercises for the given topic."""
        current_timestamp = time.time()
        random_seed = random.randint(1, 10000)



        prompt = f"""
        You are an expert language exercise creator for {self.target_language}.
        Design engaging exercises suitable for {self.difficulty_level} learners.
        Tailor them based on the user's learning focus- {self.learning_focus} 
        and past interactions.
        **STRICT RULES:**
        - Create 3 DIFFERENT exercises about {theme}
        - Each exercise should have: 
            - A question and its English translation in bracket on the next line.
            - A list of answer options (at least 4 options)
            - The correct answer
            - An explanation in English
        - Make sure to create DIFFERENT exercises each time this function is called.
        - Random seed: {random_seed} and timestamp: {current_timestamp} to ensure variety.

        """

        # Print input parameters
        print(f"\n--- DEBUG: INPUTS ---")
        print(f"Target Language: {self.target_language}")
        print(f"Difficulty Level: {self.difficulty_level}")
        print(f"Learning Focus: {self.learning_focus}")
        print(f"Theme: {theme}")
        print(f"Model: {model}")
        print(f"Temperature: {temperature}")

        messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Generate a unique question about the topic of {theme}. Make it different from previous questions."}
        ]
        
        # Print the complete prompt
        print(f"\n--- DEBUG: MESSAGES ---")
        print(json.dumps(messages, indent=2))




        #------------------------------------------------
        # Call the model 
        #------------------------------------------------     
        try:
            response = client.beta.chat.completions.parse(
                model=model,
                messages=messages,
                temperature= temperature,
                response_format = ExerciseFormat,
                )
                # Print the full response
                    # Parse the JSON response
            content = response.choices[0].message.content
            print(f"\n--- DEBUG: RAW RESPONSE ---")
            print(content)
            
            # Parse the JSON manually
            exercises_data = json.loads(content)

            return response.choices[0].message
        except Exception as e:
            print(f"\n--- DEBUG: ERROR ---")
            print(f"Error type: {type(e)}")
            print(f"Error message: {str(e)}")
        raise



if __name__ == "__main__":
    from config import user_profile, theme
    
    exercise_agent = ExerciseGeneratorAgent(
        target_language=user_profile.target_language,
        difficulty_level=user_profile.difficulty_level,
        learning_focus=user_profile.learning_focus
    )
    
    # Generate exercises
    response = exercise_agent.generate_exercises(theme)
    # Print the formatted exercises
    print("\n=== GENERATED EXERCISES ===")
    exercise_data = json.loads(response.content)
    
    if "exercises" in exercise_data:
        exercises = exercise_data["exercises"]
        for i, exercise in enumerate(exercises, 1):
            print(f"\nExercise {i}:")
            print(f"Question: {exercise['question']}")
            print(f"Options: {', '.join(exercise['options'])}")
            print(f"Correct Answer: {exercise['correctAnswer']}")
            print(f"Explanation: {exercise['explanation']}")
    else:
        print("Unexpected response format:", exercise_data)


#------------------------------------------------
# Step 3: Set up agent 
#------------------------------------------------     

 


        

