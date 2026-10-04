"""Deterministic Test Executor Agent.

This component intentionally does not use an LLM. It executes generated
unittest code and measures structural coverage with coverage.py.
"""

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict


class TestExecutorAgent:
    def __init__(self, timeout_seconds: int = 120):
        self.timeout_seconds = timeout_seconds

    def execute(self, problem_dir: str) -> Dict[str, Any]:
        workdir = Path(problem_dir).resolve()
        solution_file = workdir / "solution.py"
        test_file = workdir / "test_solution.py"
        coverage_file = workdir / "coverage.json"

        if not solution_file.exists():
            raise FileNotFoundError(solution_file)
        if not test_file.exists():
            raise FileNotFoundError(test_file)

        # Remove old coverage artifacts.
        subprocess.run(
            [sys.executable, "-m", "coverage", "erase"],
            cwd=workdir,
            capture_output=True,
            text=True,
            check=False,
        )

        start = time.perf_counter()
        test_cmd = [
            sys.executable,
            "-m",
            "coverage",
            "run",
            "--branch",
            "--source=solution",
            "-m",
            "unittest",
            "test_solution.py",
        ]

        timed_out = False
        try:
            test_proc = subprocess.run(
                test_cmd,
                cwd=workdir,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
            stdout, stderr, return_code = (
                test_proc.stdout, test_proc.stderr, test_proc.returncode
            )
        except subprocess.TimeoutExpired as exc:
            # A generated test (or implementation) that never terminates
            # is a FAIL verdict for this problem, not a crash of the run.
            timed_out = True
            stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
            stderr += f"\nTIMEOUT after {self.timeout_seconds}s"
            return_code = -1
        execution_time = time.perf_counter() - start

        json_proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "coverage",
                "json",
                "-o",
                str(coverage_file),
            ],
            cwd=workdir,
            capture_output=True,
            text=True,
            check=False,
        )

        coverage_data = {}
        if coverage_file.exists():
            try:
                coverage_data = json.loads(coverage_file.read_text())
            except json.JSONDecodeError:
                coverage_data = {}

        file_data = coverage_data.get("files", {}).get("solution.py", {})
        summary = file_data.get("summary", {})

        statements = int(summary.get("num_statements", 0))
        missing = int(summary.get("missing_lines", 0))
        covered_statements = statements - missing

        statement_coverage = (
            (covered_statements / statements) * 100
            if statements else 0.0
        )

        branches = int(summary.get("num_branches", 0))
        covered_branches = int(summary.get("covered_branches", 0))
        # A function with no decisions has 100% branch coverage by
        # convention, but only if coverage data was actually collected
        # (e.g. not when the run was killed by the timeout).
        branch_coverage = (
            (covered_branches / branches) * 100
            if branches else (100.0 if file_data else 0.0)
        )

        tests_run = self._count_tests(stdout, stderr)

        return {
            "passed": return_code == 0,
            "verdict": "TIMEOUT" if timed_out else (
                "PASS" if return_code == 0 else "FAIL"
            ),
            "return_code": return_code,
            "tests_run": tests_run,
            "statement_coverage": round(statement_coverage, 2),
            "branch_coverage": round(branch_coverage, 2),
            "execution_time_seconds": round(execution_time, 3),
            "missing_lines": file_data.get("missing_lines", []),
            "missing_branches": file_data.get("missing_branches", []),
            "stdout": stdout,
            "stderr": stderr,
            "coverage_command_return_code": json_proc.returncode,
        }

    @staticmethod
    def _count_tests(stdout: str, stderr: str) -> int:
        combined = f"{stdout}\n{stderr}"
        # unittest prints "Ran N tests in ..."
        import re

        match = re.search(r"Ran\s+(\d+)\s+tests?", combined)
        return int(match.group(1)) if match else 0
