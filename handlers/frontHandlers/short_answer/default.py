import json
import os
from typing import Union

import dotenv
from google import genai
from pydantic import BaseModel, Field, create_model

dotenv.load_dotenv()

API_KEY = os.environ.get("API_KEY")
MODEL = os.environ.get("MODEL") or "gemini-2.0-pro-exp-02-05"

client = genai.Client(api_key=API_KEY)


class QuestionBlock(BaseModel):
    context: str = Field(
        ...,
        description="The question's context.",
    )
    question: str = Field(
        ...,
        description="The question itself to be read by the student. MUST INCLUDE THE CONTEXT ABOVE. Must ask something that CAN BE ANSWERED with A SINGLE NUMBER (int or float). Be LONG and VERY DETAILED!",
    )
    solution: str = Field(
        ...,
        description="Solution to the problem (with reasoning and calculation). Be detailed: What are the given info, what the step by step reasonings.",
    )
    answer: Union[int, float] = Field(
        ...,
        description="The single answer. MUST BE CONSISTENT THE SOLUTION ABOVE.",
    )


def handler(prompt_content: str, n_problems: int):
    """
    Takes in content of a prompt and the number of problems to be generated.
    Return LLM's response.
    """

    response_raw = client.models.generate_content(
        model=MODEL,
        contents=prompt_content,
        config={
            "response_mime_type": "application/json",
            "response_schema": create_model(
                "MyQuestions",
                **{f"q{i}": (QuestionBlock, ...) for i in range(n_problems)},
            ),
            "temperature": 1.2,
        },
    ).text
    assert response_raw is not None

    response = json.loads(response_raw)
    for key in response.keys():
        response[key]["ptype"] = "short_answer"

    return response
