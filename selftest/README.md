# Offline self-test (no API key / internet needed)

Stubs only the network (Hugging Face `datasets` and the OpenRouter HTTP API)
and runs the real agents, executor and pipeline. Useful to verify the
pipeline mechanics, or for a demo if the network fails.

Run from the project root (it writes into generated/ and results/, so
back up a real run's artifacts first):

    python3 -m selftest.offline_harness     # happy path, 5 MBPP tasks
    python3 -m selftest.unit_checks         # executor, validators, model fallback
    python3 -m selftest.fault_injection     # fenced code, garbage output,
                                            # incomplete tests (feedback loop),
                                            # hanging test (TIMEOUT)

The "LLM answers" here are hand-written; these runs are NOT experiment results.
