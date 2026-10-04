import sys
import os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from selftest import offline_harness as H
import requests
# 602: first suite misses the "no repeat" path -> feedback loop must fix it
INCOMPLETE_602 = '''import unittest
from solution import first_repeated_char

class T(unittest.TestCase):
    def test_repeat(self):
        self.assertEqual(first_repeated_char("abcabc"), "a")
'''
HANG_605 = H.TESTS[605].replace("def test_two(self):", "def test_hang(self):\n        while True: pass\n    def test_two(self):")
def post(url, json=None, **kw):
    p = json["messages"][0]["content"]; tid = H.task_id_from(p)
    H.LOG.append(("POST", "repair" if "Coverage report" in p else ("tests" if "Test Generator" in p else "code"), tid))
    if "Coverage report" in p:          out = H.TESTS[tid]
    elif "Test Generator Agent" in p:   out = {602: INCOMPLETE_602, 605: HANG_605}.get(tid, H.TESTS[tid])
    else:                               out = ("```python\n" + H.CODE[tid] + "\n```") if tid == 604 else H.CODE[tid]
    if tid == 603 and "Test Generator" not in p: out = "Here is the solution: def broken("   # unrecoverable garbage
    return H.R(200, {"model": json["model"], "choices": [{"message": {"content": out}}]})
requests.post = post
import pipeline
from agents.test_executor import TestExecutorAgent as Real
pipeline.TestExecutorAgent = lambda timeout_seconds: Real(5)
sys.argv = ["pipeline.py", "-n", "5"]
pipeline.main()
print("\nLLM calls:", [c for c in H.LOG if c[0]=="POST"])
