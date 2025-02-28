# -*- coding: utf-8 -*-
"""Rockae.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1nSMI0rVzSuht_gXGlwfTEDcpVBM5xQsl
"""

import google.generativeai as genai
import json
from typing import Dict, List
import logging
import asyncio
import nest_asyncio

nest_asyncio.apply()

class QuizGenerationError(Exception):
    """Custom exception for quiz generation failures"""
    pass

class QuizGenerator:
    def __init__(self, api_key: str):
        self.model_name = "gemini-2.0-flash"
        self.temperature = 0.7
        self.max_output_tokens = 2000
        self.valid_difficulties = ["easy", "medium", "hard"]
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(self.model_name)
            self.logger = logging.getLogger(__name__)
        except Exception as e:
            raise QuizGenerationError(f"Failed to initialize Gemini API: {str(e)}")

    def _call_api(self, prompt: str) -> dict:
        """Simplified API call with logging"""
        try:
            self.logger.debug(f"Sending prompt: {prompt[:100]}...")  # Log first 100 chars
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_output_tokens
                )
            )
            self.logger.debug(f"Full API response: {response}")
            if not response.candidates:
                raise QuizGenerationError("No candidates in response")
            text = response.candidates[0].content.parts[0].text.strip()
            self.logger.debug(f"Extracted response text: '{text}'")
            if not text:
                raise QuizGenerationError("API returned empty response text")
            return json.loads(text)
        except Exception as e:
            self.logger.error(f"API call failed with: {str(e)}")
            raise QuizGenerationError(f"API error: {str(e)}")

    def generate_quiz(self, difficulty: str, num_questions: int, notes: str, question_type: str = "multiple_choice") -> Dict:
        if not all([difficulty, num_questions, notes]):
            raise QuizGenerationError("All parameters must be provided")

        if difficulty not in self.valid_difficulties:
            raise QuizGenerationError(f"Difficulty must be one of {self.valid_difficulties}")

        if not isinstance(num_questions, int) or num_questions <= 0:
            raise QuizGenerationError("Number of questions must be a positive integer")

        if question_type != "multiple_choice":  # Only multiple_choice for now, as per the example
            raise QuizGenerationError("Question type must be 'multiple_choice' to match the requested format")

        prompt = f"""
        Generate exactly {num_questions} multiple-choice quiz questions based on the following notes.
        Difficulty level: {difficulty}
        Requirements:
        - Each question must have exactly one correct answer and four options labeled answer_a, answer_b, answer_c, and answer_d
        - Questions must be based solely on the provided notes
        - Make questions appropriate for the specified difficulty level

        Notes: {notes}

        Return the response in this exact JSON format:
        {{
          "from": "Gemini",
          "text": "[{{"question_text": "question text", "answer_a": "option 1", "answer_b": "option 2", "answer_c": "option 3", "answer_d": "option 4", "correct_answer": "A"}}]"
        }}
        Ensure the correct_answer is one of 'A', 'B', 'C', or 'D'.
        """

        try:
            quiz_data = self._call_api(prompt)
            if not self._validate_response(quiz_data, num_questions):
                raise QuizGenerationError("Invalid quiz format returned from API")
            return quiz_data
        except Exception as e:
            raise QuizGenerationError(f"Failed to generate quiz: {str(e)}")

    async def generate_quiz_async(self, difficulty: str, num_questions: int, notes: str, question_type: str = "multiple_choice") -> Dict:
        # Same validation as above
        if not all([difficulty, num_questions, notes]):
            raise QuizGenerationError("All parameters must be provided")

        if difficulty not in self.valid_difficulties:
            raise QuizGenerationError(f"Difficulty must be one of {self.valid_difficulties}")

        if not isinstance(num_questions, int) or num_questions <= 0:
            raise QuizGenerationError("Number of questions must be a positive integer")

        if question_type != "multiple_choice":  # Only multiple_choice for now
            raise QuizGenerationError("Question type must be 'multiple_choice' to match the requested format")

        prompt = f"""
        Generate exactly {num_questions} multiple-choice quiz questions based on the following notes.
        Difficulty level: {difficulty}
        Requirements:
        - Each question must have exactly one correct answer and four options labeled answer_a, answer_b, answer_c, and answer_d
        - Questions must be based solely on the provided notes
        - Make questions appropriate for the specified difficulty level

        Notes: {notes}

        Return the response in this exact JSON format:
        {{
          "from": "Gemini",
          "text": "[{{"question_text": "question text", "answer_a": "option 1", "answer_b": "option 2", "answer_c": "option 3", "answer_d": "option 4", "correct_answer": "A"}}]"
        }}
        Ensure the correct_answer is one of 'A', 'B', 'C', or 'D'.
        """

        try:
            loop = asyncio.get_running_loop()
            quiz_data = await loop.run_in_executor(None, lambda: self._call_api(prompt))
            if not self._validate_response(quiz_data, num_questions):
                raise QuizGenerationError("Invalid quiz format returned from API")
            return quiz_data
        except Exception as e:
            raise QuizGenerationError(f"Failed to generate quiz: {str(e)}")

    def _validate_response(self, quiz_data: Dict, expected_questions: int) -> bool:
        if not isinstance(quiz_data, dict) or "from" not in quiz_data or quiz_data["from"] != "Gemini" or "text" not in quiz_data:
            return False

        try:
            questions = json.loads(quiz_data["text"])
            if not isinstance(questions, list) or len(questions) != expected_questions:
                return False

            for question in questions:
                if not all(key in question for key in ["question_text", "answer_a", "answer_b", "answer_c", "answer_d", "correct_answer"]):
                    return False
                if question["correct_answer"] not in ["A", "B", "C", "D"]:
                    return False
                if not all(isinstance(question[key], str) for key in ["question_text", "answer_a", "answer_b", "answer_c", "answer_d"]):
                    return False

            return True
        except json.JSONDecodeError:
            return False

def main():
    try:
        api_key = ""  # Removed API key
        generator = QuizGenerator(api_key)

        difficulty = "medium"
        num_questions = 1  # Match the example in the screenshot
        notes = """A dog is a domesticated mammal from the species *Canis lupus familiaris*,
        known for its loyalty, intelligence, and companionship with humans."""

        quiz = generator.generate_quiz(difficulty, num_questions, notes, question_type="multiple_choice")
        print("Synchronous Quiz:")
        print(json.dumps(quiz, indent=2))

    except QuizGenerationError as e:
        print(f"Error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")

async def main_async():
    try:
        api_key = ""  # Removed API key
        generator = QuizGenerator(api_key)

        difficulty = "medium"
        num_questions = 1  # Match the example
        notes = """A dog is a domesticated mammal from the species *Canis lupus familiaris*,
        known for its loyalty, intelligence, and companionship with humans."""

        quiz = await generator.generate_quiz_async(difficulty, num_questions, notes, question_type="multiple_choice")
        print("Asynchronous Quiz:")
        print(json.dumps(quiz, indent=2))

    except QuizGenerationError as e:
        print(f"Error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
    asyncio.run(main_async())