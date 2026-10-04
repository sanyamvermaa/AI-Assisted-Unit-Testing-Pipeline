"""Unit-level checks of the executor, validators and client (offline)."""
import os, sys, tempfile
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from selftest import offline_harness as H      # installs network stubs
import requests
from agents.test_executor import TestExecutorAgent
from agents.code_generator import CodeGeneratorAgent
from agents.test_generator import TestGeneratorAgent
from agents.openrouter_client import OpenRouterClient

def mk(sol, tst):
    d = Path(tempfile.mkdtemp())
    (d / "solution.py").write_text(sol); (d / "test_solution.py").write_text(tst)
    return str(d)

ex = TestExecutorAgent(timeout_seconds=5)
results = []
def check(name, ok, detail): results.append(ok); print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")

r = ex.execute(mk("def f(x):\n    return x + 2\n",
    "import unittest\nfrom solution import f\nclass T(unittest.TestCase):\n    def test_a(self):\n        self.assertEqual(f(1), 2)\n"))
check("F1 buggy implementation -> FAIL", r["verdict"] == "FAIL", r["verdict"])

r = ex.execute(mk("def sign(x):\n    if x > 0:\n        return 1\n    return -1\n",
    "import unittest\nfrom solution import sign\nclass T(unittest.TestCase):\n    def test_pos(self):\n        self.assertEqual(sign(3), 1)\n"))
check("F2 partial coverage measured", (r["statement_coverage"], r["branch_coverage"]) == (75.0, 50.0),
      f"stmt={r['statement_coverage']} branch={r['branch_coverage']} missing={r['missing_branches']}")

r = ex.execute(mk("def f():\n    while True: pass\n",
    "import unittest\nfrom solution import f\nclass T(unittest.TestCase):\n    def test_a(self):\n        f()\n"))
check("F4 hanging test -> TIMEOUT", r["verdict"] == "TIMEOUT" and r["branch_coverage"] == 0.0, r["verdict"])

requests.post = lambda url, json=None, **k: H.R(200, {"model": "m", "choices": [{"message": {"content": "```python\ndef f():\n    return 1\n```"}}]})
out = CodeGeneratorAgent(OpenRouterClient()).generate("x")
check("F5 fenced reply unwrapped", out["code"] == "def f():\n    return 1", repr(out["code"]))

calls = []
def flaky(url, json=None, **k):
    calls.append(json["model"])
    if len(calls) == 1: return H.R(429, {"error": "rate limited"})
    return H.R(200, {"model": json["model"], "choices": [{"message": {"content": "def f():\n    return 1"}}]})
requests.post = flaky
requests.get = lambda url, **k: H.R(200, {"data": [{"id": "a/m1:free", "pricing": {}}, {"id": "b/m2:free", "pricing": {}}]})
out = CodeGeneratorAgent(OpenRouterClient()).generate("x")
check("F7 HTTP 429 -> next free model", out["model"] == "b/m2:free", f"tried {calls}")

try:
    TestGeneratorAgent.validate("User Safety: safe"); ok = False
except ValueError:
    ok = True
check("F8 'User Safety: safe' rejected", ok, "ValueError raised")

r = ex.execute(mk("def total(xs):\n    s = 0\n    for x in xs:\n        s += x\n    return s\n",
    "import unittest\nfrom solution import total\nclass T(unittest.TestCase):\n    def test_a(self):\n        self.assertEqual(total([1, 2]), 3)\n"))
print(f"[INFO] loop blind spot: only total([1, 2]) tested -> stmt={r['statement_coverage']} "
      f"branch={r['branch_coverage']} (zero-iteration case not required by coverage.py)")

print(f"\n{sum(results)}/{len(results)} checks passed")
sys.exit(0 if all(results) else 1)
