"""Main AI-Assisted Unit Testing Pipeline.

Usage:
    python3 pipeline.py                                   # 5 problems, statement+branch
    python3 pipeline.py -n 1                              # demo: one problem
    python3 pipeline.py --criterion branch --target 100   # user-specified criterion
"""

import argparse
import json
import time
import traceback
from pathlib import Path

from agents.code_generator import CodeGeneratorAgent
from agents.openrouter_client import OpenRouterClient
from agents.test_executor import TestExecutorAgent
from agents.test_generator import CRITERIA, TestGeneratorAgent
from dataset_loader import load_mbpp_problems


GENERATED_DIR = Path("generated")
RESULTS_DIR = Path("results")


def save_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def criterion_value(execution: dict, criterion: str) -> float:
    """Coverage figure that the chosen criterion is judged on."""
    if criterion == "statement":
        return execution["statement_coverage"]
    if criterion == "branch":
        return execution["branch_coverage"]
    return min(execution["statement_coverage"], execution["branch_coverage"])


def parse_args():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-n", "--num-problems", type=int, default=5)
    ap.add_argument("--start-from", type=int, default=1,
                    help="skip problems before this 1-based index")
    ap.add_argument("--skip-mbpp-ids", type=int, nargs="+", default=[],
                    metavar="ID",
                    help="MBPP task IDs to skip; the next dataset problem fills the gap")
    ap.add_argument("--criterion", choices=sorted(CRITERIA),
                    default="statement+branch",
                    help="coverage criterion the Test Generator must satisfy")
    ap.add_argument("--target", type=float, default=100.0,
                    help="required coverage (percent) for the criterion")
    ap.add_argument("--max-repair-rounds", type=int, default=2,
                    help="coverage-feedback rounds if the target is missed")
    return ap.parse_args()


def write_summary(summary: dict) -> None:
    (RESULTS_DIR / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")


def main() -> None:
    args = parse_args()
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    problems = load_mbpp_problems(limit=args.num_problems,
                                  skip_ids=args.skip_mbpp_ids or None)

    client = OpenRouterClient()
    code_agent = CodeGeneratorAgent(client)
    test_agent = TestGeneratorAgent(client, criterion=args.criterion)
    executor = TestExecutorAgent(timeout_seconds=180)

    summary = {
        "configuration": {
            "criterion": args.criterion,
            "target_percent": args.target,
            "max_repair_rounds": args.max_repair_rounds,
            "temperature": 0.2,
            "max_tokens_code": 1500,
            "max_tokens_tests": 2500,
        },
        "total_problems": len(problems),
        "successful_executions": 0,
        "pipeline_errors": 0,
        "passed": 0,
        "failed": 0,
        "criterion_met": 0,
        "average_statement_coverage": 0.0,
        "average_branch_coverage": 0.0,
        "total_tests": 0,
        "total_runtime_seconds": 0.0,
        "problems": [],
    }
    statement_values, branch_values = [], []

    for index, problem in enumerate(problems, start=1):
        if index < args.start_from:
            continue
        problem_start = time.perf_counter()
        problem_dir = GENERATED_DIR / f"problem_{index}"
        problem_dir.mkdir(parents=True, exist_ok=True)
        timings = {}

        print("=" * 70)
        print(f"PROBLEM {index}/{len(problems)}")
        print("=" * 70)
        print(f"MBPP ID : {problem['id']}")
        print(f"Task    : {problem['task']}")

        try:
            print("\n[1/3] CODE GENERATOR AGENT")
            t = time.perf_counter()
            code_result = code_agent.generate(problem["task"])
            timings["code_generation_s"] = round(time.perf_counter() - t, 3)
            save_text(problem_dir / "solution.py", code_result["code"])
            print(f"      Model: {code_result['model']}")
            print(f"      ✓ Implementation generated ({timings['code_generation_s']:.1f}s)")

            print("\n[2/3] TEST GENERATOR AGENT")
            t = time.perf_counter()
            test_result = test_agent.generate(problem["task"], code_result["code"])
            timings["test_generation_s"] = round(time.perf_counter() - t, 3)
            save_text(problem_dir / "test_solution.py", test_result["tests"])
            print(f"      Model: {test_result['model']}")
            print(f"      ✓ Tests generated ({timings['test_generation_s']:.1f}s)")

            print("\n[3/3] TEST EXECUTOR AGENT")
            execution = executor.execute(str(problem_dir))
            rounds = [{"round": 0, "verdict": execution["verdict"],
                       "statement_coverage": execution["statement_coverage"],
                       "branch_coverage": execution["branch_coverage"],
                       "tests_run": execution["tests_run"]}]

            # Coverage feedback loop: only when the suite PASSES but misses
            # the criterion. Failing suites are not "repaired", because a
            # failure may expose a real defect in the implementation.
            repair_round = 0
            while (execution["passed"]
                   and criterion_value(execution, args.criterion) < args.target
                   and repair_round < args.max_repair_rounds):
                repair_round += 1
                print(f"      Criterion not met "
                      f"({criterion_value(execution, args.criterion):.1f}% < "
                      f"{args.target:.0f}%) -> feedback round {repair_round}")
                t = time.perf_counter()
                test_result = test_agent.repair(
                    problem["task"], code_result["code"], test_result["tests"],
                    execution["missing_lines"], execution["missing_branches"])
                timings[f"repair_{repair_round}_s"] = round(time.perf_counter() - t, 3)
                save_text(problem_dir / "test_solution.py", test_result["tests"])
                execution = executor.execute(str(problem_dir))
                rounds.append({"round": repair_round, "verdict": execution["verdict"],
                               "statement_coverage": execution["statement_coverage"],
                               "branch_coverage": execution["branch_coverage"],
                               "tests_run": execution["tests_run"]})
            timings["test_execution_s"] = execution["execution_time_seconds"]

            met = (execution["passed"]
                   and criterion_value(execution, args.criterion) >= args.target)
            print(f"      Verdict              : {execution['verdict']}")
            print(f"      Statement coverage  : {execution['statement_coverage']:.2f}%")
            print(f"      Branch coverage     : {execution['branch_coverage']:.2f}%")
            print(f"      Tests executed      : {execution['tests_run']}")
            print(f"      Criterion ({args.criterion} >= {args.target:.0f}%) : "
                  f"{'MET' if met else 'NOT MET'}")

            elapsed = time.perf_counter() - problem_start
            experiment = {
                "problem_number": index,
                "mbpp_id": problem["id"],
                "task": problem["task"],
                "reference_code": problem["reference_code"],
                "reference_tests": problem["reference_tests"],
                "configuration": {
                    "temperature": 0.2,
                    "num_problems": args.num_problems,
                    "test_framework": "unittest",
                    "coverage_tool": "coverage.py",
                    "criterion": args.criterion,
                    "target_percent": args.target,
                    "max_repair_rounds": args.max_repair_rounds,
                },
                "code_generator": {
                    "model": code_result["model"],
                    "prompt": code_result["prompt"],
                    "generated_code": code_result["code"],
                },
                "test_generator": {
                    "model": test_result["model"],
                    "prompt": test_result["prompt"],
                    "generated_tests": test_result["tests"],
                },
                "execution": execution,
                "feedback_rounds": rounds,
                "criterion_met": met,
                "stage_timings": timings,
                "problem_runtime_seconds": round(elapsed, 3),
            }
            (problem_dir / "experiment.json").write_text(
                json.dumps(experiment, indent=2, ensure_ascii=False),
                encoding="utf-8")

            summary["successful_executions"] += 1
            summary["passed"] += int(execution["passed"])
            summary["failed"] += int(not execution["passed"])
            summary["criterion_met"] += int(met)
            summary["total_tests"] += execution["tests_run"]
            statement_values.append(execution["statement_coverage"])
            branch_values.append(execution["branch_coverage"])
            summary["problems"].append({
                "problem_number": index,
                "mbpp_id": problem["id"],
                "tests": execution["tests_run"],
                "verdict": execution["verdict"],
                "passed": execution["passed"],
                "statement_coverage": execution["statement_coverage"],
                "branch_coverage": execution["branch_coverage"],
                "criterion_met": met,
                "feedback_rounds_used": repair_round,
                "stage_timings": timings,
                "runtime_seconds": round(elapsed, 3),
            })
        except Exception as exc:  # one bad LLM answer must not lose the run
            elapsed = time.perf_counter() - problem_start
            summary["pipeline_errors"] += 1
            summary["problems"].append({
                "problem_number": index,
                "mbpp_id": problem["id"],
                "verdict": "PIPELINE_ERROR",
                "error": f"{type(exc).__name__}: {exc}",
                "runtime_seconds": round(elapsed, 3),
            })
            (problem_dir / "error.txt").write_text(traceback.format_exc())
            print(f"\n      ✗ PIPELINE ERROR: {type(exc).__name__}: {exc}")

        summary["total_runtime_seconds"] = round(
            summary["total_runtime_seconds"] + elapsed, 3)
        if statement_values:
            summary["average_statement_coverage"] = round(
                sum(statement_values) / len(statement_values), 2)
            summary["average_branch_coverage"] = round(
                sum(branch_values) / len(branch_values), 2)
        write_summary(summary)  # written after every problem

        print(f"\n      PROBLEM {index} COMPLETE ({elapsed:.1f}s)")
        print(f">>> OVERALL PROGRESS: {index}/{len(problems)} problems "
              f"completed ({100 * index // len(problems)}%)")

    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    print(f"Problems              : {summary['total_problems']}")
    print(f"Passed                : {summary['passed']}")
    print(f"Failed                : {summary['failed']}")
    print(f"Pipeline errors       : {summary['pipeline_errors']}")
    print(f"Criterion met         : {summary['criterion_met']}")
    print(f"Generated tests       : {summary['total_tests']}")
    print(f"Avg statement cover.  : {summary['average_statement_coverage']:.2f}%")
    print(f"Avg branch cover.     : {summary['average_branch_coverage']:.2f}%")
    print(f"Total runtime         : {summary['total_runtime_seconds']:.1f}s")


if __name__ == "__main__":
    main()
