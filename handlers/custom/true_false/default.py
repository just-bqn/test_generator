import json
import os
from typing import List

import dotenv
import numpy as np
from google import genai
from pydantic import BaseModel, Field, create_model

dotenv.load_dotenv()

API_KEY = os.environ.get("API_KEY")
MODEL = os.environ.get("MODEL") or "gemini-2.0-flash"

client = genai.Client(api_key=API_KEY)


class StatementsPair(BaseModel):
    true: str = Field(
        ...,
        description="Think about the above carefully. Make sure that this statement MUST BE TRUE.",
    )
    false: str = Field(
        ...,
        description="This statement appears SIMILAR to the true one but MUST BE FALSE.",
    )


class QuestionBlock(BaseModel):
    topic: str = Field(
        ...,
        description="The question's topic. Keep it short.",
    )
    question: str = Field(
        ...,
        description="The detailed context, numbers, events, etc. NOT A QUESTION! Statements about this context will be made, and students will have to determine if each of them is true or false.",
    )
    solution: str = Field(
        ...,
        description="Generate 4 possible pairs statements about the question (one true, one false), then propose the solution (with reasoning and calculation). Be detailed: What are the given info, what the step by step solution for each subtask is.",
    )
    statements: List[StatementsPair] = Field(
        ...,
        min_length=4,
        max_length=4,
        description="List of pairs of statements related to the problem. DO NOT GENERATE STATEMENTS NOT VERIFIED BY THE SOLUTION ABOVE.",
    )


def handler(prompt_content: str, n_problems: int, extra_cfg: dict):
    """
    Takes in content of a prompt and the number of problems to be generated.
    Return LLM's response.
    """

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt_content,
        config={
            "response_mime_type": "application/json",
            "response_schema": create_model(
                "MyQuestions",
                **{f"q{i}": (QuestionBlock, ...) for i in range(n_problems)},
            ),
            "temperature": extra_cfg.get("temperature", 1.2),
        },
    ).text
    assert response is not None
    response_dict = json.loads(response)

    keys = response_dict.keys()

    problems = {
        key: dict.fromkeys(["ptype", "question", "answers", "medias"], None)
        for key in keys
    }

    for key in keys:
        problem_raw = response_dict[key]
        problem = problems[key]

        answer = "".join(np.random.choice(["D", "S"], size=4))
        statements = []
        for j, statement_pair in enumerate(problem_raw["statements"]):
            statement = statement_pair["true" if answer[j] == "D" else "false"]
            statement_prefix = f"{chr(ord('a') + j)})"
            statements.append(f"{statement_prefix} {statement}")

        problem["question"] = "\n\n".join([problem_raw["question"]] + statements)
        problem["solution"] = problem_raw["solution"]
        problem["answers"] = [("*", answer)]
        problem["medias"] = []

    return (problems, response)
