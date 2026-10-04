"""Code Generator Agent."""

import ast
import textwrap
from typing import Dict

from ._text import strip_code_fences
from .openrouter_client import OpenRouterClient


class CodeGeneratorAgent:
    def __init__(self, client: OpenRouterClient):
        self.client = client

    @staticmethod
    def build_prompt(task: str) -> str:
        return textwrap.dedent(
            f"""
            You are the Code Generator Agent in an automated software-testing
            experiment.

            Programming problem:
            {task}

            Generate a correct Python implementation for the problem.

            Strict output rules:
            - Return ONLY executable Python source code.
            - Do not use Markdown code fences.
            - Do not include explanations.
            - Do not include JSON.
            - Do not include safety classifications.
            - Do not include analysis.
            - Define the function(s) required by the problem.
            - Keep the implementation concise and self-contained.
            """
        ).strip()

    MAX_RETRIES = 2

    @staticmethod
    def validate(code: str) -> None:
        if not code.strip():
            raise ValueError("Code Generator returned an empty response.")
        try:
            ast.parse(code)
        except SyntaxError as exc:
            raise ValueError(f"Generated implementation is invalid Python: {exc}")

    def generate(self, task: str) -> Dict[str, str]:
        prompt = self.build_prompt(task)
        last_exc: Exception = RuntimeError("no attempts made")
        excluded: list = []
        for attempt in range(1, self.MAX_RETRIES + 2):
            response = None
            try:
                response = self.client.chat(
                    [{"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_tokens=1500,
                    exclude_models=excluded or None,
                )
                code = strip_code_fences(response["text"])
                self.validate(code)
                return {"code": code, "prompt": prompt, "model": response["model"]}
            except ValueError as exc:
                last_exc = exc
                if response and response.get("model"):
                    excluded.append(response["model"])
                if attempt <= self.MAX_RETRIES:
                    print(f"      Retrying code generation (attempt {attempt + 1}): {exc}")
        raise last_exc
