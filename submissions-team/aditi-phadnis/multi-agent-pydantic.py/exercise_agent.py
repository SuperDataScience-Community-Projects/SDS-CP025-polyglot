import os
from openai import OpenAI
from pydantic import BaseModel
from config import client, UserProfile, model, temperature, theme
import json
# --------------------------------------------------------------
# Step 1: Define the response format in a Pydantic model
# --------------------------------------------------------------

class ExerciseFormat(BaseModel):
    question: str # single_choice". "multiple_choice", "fill_in_the_blank", or "matching"
    options: list[str] =[]
    correctAnswer: str
    explanation: str


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

        prompt = f"""
        You are an expert language exercise creator for {self.target_language}.
        Design engaging exercises suitable for {self.difficulty_level} learners.
        Tailor them based on the user's learning focus- {self.learning_focus} 
        and past interactions."""

        #------------------------------------------------
        # Call the model 
        #------------------------------------------------     

        response = client.beta.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Generate a question about the topic of {theme}."}
            ],
            temperature= temperature,
            response_format = ExerciseFormat,
            )
        
                # Ensure OpenAI response is properly handled
        try:
            content = response.choices[0].message.content
            exercises = json.loads(content)  # Ensure the response is valid JSON
            return [ExerciseFormat(**exercise) for exercise in exercises]
        except (json.JSONDecodeError, KeyError, AttributeError) as e:
            return f"Invalid JSON response. Error: {e}"



        

