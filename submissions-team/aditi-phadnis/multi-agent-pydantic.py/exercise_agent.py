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
        and past interactions.
        **STRICT RULES:**
        - Return output as a **valid JSON object**.
        - The JSON must be an array of exercises.
        - Each exercise must be an object with:
          - `"type"`: One of `"single_choice"`, `"multiple_choice"`, `"fill_in_the_blank"`, `"matching"`.
          - `"question"`: The question text.
          - `"options"`: A list of answer choices (if applicable).
          - `"correctAnswer"`: The correct answer.
          - `"explanation"`: Detailed explanation for the answer in English.
        - Ensure the response is valid JSON before returning.
        """



        #------------------------------------------------
        # Call the model 
        #------------------------------------------------     

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Generate a question about the topic of {theme}."}
            ],
            temperature= temperature,
            response_format = {"type": "json_object"},
            )
        content = response.choices[0].message.content.strip()
            
                # Ensure OpenAI response is properly handled
        # try:
        #     content = response.choices[0].message.content.strip()

        #     # ✅ Ensure OpenAI response is in valid JSON format
        #     exercises = json.loads(content)


        #     # ✅ Ensure JSON is correctly parsed
        #     if isinstance(content, list):
        #         return f"Expected a list of exercises, but got {type(exercises)}: {exercises}"

        #     # ✅ Ensure exercises is a list
        #     if not isinstance(exercises, list):
        #         return f"Expected a list of exercises, but got {type(exercises)}."

        #     return [ExerciseFormat(**exercise) for exercise in exercises]
        # except (json.JSONDecodeError, KeyError, AttributeError, TypeError) as e:
        #     return f"Invalid JSON response. Error: {e}"



if __name__ == "__main__":
    agent = ExerciseGeneratorAgent(target_language="French", difficulty_level="Beginner", learning_focus="Grammar")
    exercises = agent.generate_exercises(theme="Greetings")

    # for ex in exercises:
    #     print(ex.json(indent=2))

    print(ExerciseGeneratorAgent.content)

        

