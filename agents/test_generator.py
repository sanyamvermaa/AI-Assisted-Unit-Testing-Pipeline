"""Test Generator Agent."""

import ast
import textwrap
from typing import Dict, List

from ._text import strip_code_fences
from .openrouter_client import OpenRouterClient

# User-selectable coverage criteria. The "statement+branch" wording is
# exactly the wording used in the original experiment, so the default
# prompt is unchanged.
CRITERIA = {
    "statement+branch": "Aim for high statement and branch coverage.",
    "statement": (
        "Aim for 100% statement coverage: every executable line of the "
        "implementation must run at least once."
    ),
    "branch": (
        "Aim for 100% branch coverage: every decision must be exercised "
        "with both its True and its False outcome."
    ),
}


class TestGeneratorAgent:
    TEMPERATURE = 0.2
    MAX_TOKENS = 2500

    def __init__(self, client: OpenRouterClient,
                 criterion: str = "statement+branch"):
        if criterion not in CRITERIA:
            raise ValueError(f"Unknown coverage criterion: {criterion}")
        self.client = client
        self.criterion = criterion

    @staticmethod
    def build_prompt(task: str, implementation: str,
                     criterion: str = "statement+branch") -> str:
        return textwrap.dedent(
            f"""
            You are the Test Generator Agent in an AI-assisted unit-testing
            pipeline.

            Programming problem:
            {task}

            Generated Python implementation:
            {implementation}

            Create a complete Python unittest module named test_solution.py.

            Test-design requirements:
            1. Use Python's built-in unittest framework.
            2. Import the function(s) from solution.py.
            3. Include normal/representative cases.
            4. Include boundary cases where meaningful.
            5. Include edge cases such as empty, singleton, negative,
               duplicate, or unusual inputs when applicable.
            6. For each important conditional, exercise both outcomes.
            7. For loops, exercise zero iterations and one-or-more iterations
               when meaningful.
            8. Use strong assertions with expected outputs.
            9. Do not test implementation details that are irrelevant to the
               problem specification.
            10. {CRITERIA[criterion]}

            Strict output rules:
            - Return ONLY executable Python source code.
            - Do not use Markdown code fences.
            - Do not include explanations.
            - Do not include JSON.
            - Do not include safety classifications.
            """
        ).strip()

    @staticmethod
    def build_repair_prompt(task: str, implementation: str, tests: str,
                            missing_lines: List[int],
                            missing_branches: List[List[int]],
                            criterion: str) -> str:
        numbered = "\n".join(
            f"{i:>3}: {line}"
            for i, line in enumerate(implementation.splitlines(), start=1)
        )
        lines = ", ".join(map(str, missing_lines)) or "none"
        branches = ", ".join(
            f"line {a} -> {'exit' if b < 0 else 'line ' + str(b)}"
            for a, b in missing_branches
        ) or "none"
        return textwrap.dedent(
            f"""
            You are the Test Generator Agent in an AI-assisted unit-testing
            pipeline. Your previous test module passed but did not satisfy
            the coverage criterion: {CRITERIA[criterion]}

            Programming problem:
            {task}

            Implementation (with line numbers):
            {numbered}

            Current test module:
            {tests}

            Coverage report from the Test Executor Agent:
            - Statements never executed: {lines}
            - Branch outcomes never taken: {branches}

            Return the COMPLETE updated test module: keep every existing
            test and add tests whose inputs reach the uncovered statements
            and branch outcomes. Expected values must follow the problem
            specification.

            Strict output rules:
            - Return ONLY executable Python source code.
            - Do not use Markdown code fences.
            - Do not include explanations.
            - Do not include JSON.
            - Do not include safety classifications.
            """
        ).strip()

    @staticmethod
    def validate(tests: str) -> None:
        if not tests.strip():
            raise ValueError("Test Generator returned an empty response.")

        try:
            tree = ast.parse(tests)
        except SyntaxError as exc:
            raise ValueError(f"Generated tests are invalid Python: {exc}")

        if "unittest" not in tests:
            raise ValueError("Generated tests do not import/use unittest.")

        test_methods = [
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test_")
        ]
        if not test_methods:
            raise ValueError("Generated test module contains no test_ methods.")

    MAX_RETRIES = 2

    def _ask(self, prompt: str) -> Dict[str, str]:
        last_exc: Exception = RuntimeError("no attempts made")
        excluded: list = []
        for attempt in range(1, self.MAX_RETRIES + 2):
            response = None
            try:
                response = self.client.chat(
                    [{"role": "user", "content": prompt}],
                    temperature=self.TEMPERATURE,
                    max_tokens=self.MAX_TOKENS,
                    exclude_models=excluded or None,
                )
                tests = strip_code_fences(response["text"])
                self.validate(tests)
                return {"tests": tests, "prompt": prompt, "model": response["model"]}
            except ValueError as exc:
                last_exc = exc
                if response and response.get("model"):
                    excluded.append(response["model"])
                if attempt <= self.MAX_RETRIES:
                    print(f"      Retrying test generation (attempt {attempt + 1}): {exc}")
        raise last_exc

    def generate(self, task: str, implementation: str) -> Dict[str, str]:
        return self._ask(self.build_prompt(task, implementation, self.criterion))

    def repair(self, task: str, implementation: str, tests: str,
               missing_lines, missing_branches) -> Dict[str, str]:
        return self._ask(self.build_repair_prompt(
            task, implementation, tests, missing_lines, missing_branches,
            self.criterion))
