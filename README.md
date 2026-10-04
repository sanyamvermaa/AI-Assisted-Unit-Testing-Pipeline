# AI-Assisted Unit Testing Pipeline

CSE731 Software Testing — Mini Project

## Architecture

```text
MBPP problem
     |
     v
Code Generator Agent
     |
     v
generated solution.py
     |
     v
Test Generator Agent
     |
     v
generated test_solution.py
     |
     v
Test Executor Agent
     |
     +--> unittest PASS/FAIL
     |
     +--> coverage.py
             |
             +--> statement coverage
             +--> branch coverage
```

## Requirements

- Python 3.10+
- OpenRouter API key
- Internet access for MBPP and OpenRouter
- `requests`
- `datasets`
- `coverage`

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
export OPENROUTER_API_KEY="YOUR_KEY"
```

Optional:

```bash
export OPENROUTER_MODEL="MODEL_ID"
```

## Run

```bash
python3 pipeline.py                                  # 5 problems, statement+branch, target 100%
python3 pipeline.py -n 1                             # live demo: one problem
python3 pipeline.py --criterion branch --target 100  # user-specified coverage criterion
python3 pipeline.py --max-repair-rounds 0            # disable the coverage-feedback loop
```

If a passing suite misses the coverage target, the Test Executor's list of
uncovered lines/branches is fed back to the Test Generator (up to
`--max-repair-rounds` times). Failing suites are never auto-repaired.

## Artifacts

For each problem:

```text
generated/problem_N/
├── solution.py
├── test_solution.py
└── experiment.json
```

Aggregate results:

```text
results/summary.json
```

## Important limitation

100% statement/branch coverage does not prove complete functional correctness.
It only means the measured structural elements were exercised. For stronger
validation, run independent MBPP reference tests and/or mutation testing.

## Security note

The executor runs generated Python locally. This is acceptable for a
controlled course experiment but should be sandboxed for untrusted production
use.
