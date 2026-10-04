"""MBPP dataset loader."""

from typing import Any, Dict, List

from datasets import load_dataset


def _first(record: Dict[str, Any], keys, default=None):
    for key in keys:
        if key in record and record[key] is not None:
            return record[key]
    return default


def load_mbpp_problems(
    split: str = "train",
    limit: int = 5,
    skip_ids: List[int] = None,
) -> List[Dict[str, Any]]:
    """Load MBPP records and normalize them for the pipeline.

    skip_ids: MBPP task IDs to exclude; the next available problem fills the gap.
    """
    dataset = load_dataset("google-research-datasets/mbpp", split=split)
    skip_set = set(skip_ids or [])

    problems = []
    for record in dataset:
        mbpp_id = _first(record, ["task_id", "id"])
        if mbpp_id in skip_set:
            continue
        problems.append(
            {
                "id": mbpp_id,
                "task": _first(record, ["text", "task"]),
                "reference_code": _first(
                    record, ["code", "reference_code"], ""
                ),
                "reference_tests": _first(
                    record, ["test_list", "test", "reference_tests"], []
                ),
            }
        )

        if len(problems) >= limit:
            break

    return problems
