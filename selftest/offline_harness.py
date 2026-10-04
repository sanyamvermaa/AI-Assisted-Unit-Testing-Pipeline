"""Offline harness: stubs ONLY the network (HF datasets + OpenRouter HTTP).
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
All agent / pipeline / executor code is the project's original code."""
import os, sys, types, json, re
os.environ["OPENROUTER_API_KEY"] = "sk-offline-dummy"

# ---------- fake MBPP (task ids 601-605 = first 5 of the 'train' split) ----------
MBPP = [
 dict(task_id=601, text="Write a function to find the longest chain which can be formed from the given set of pairs.",
      code="", test_list=["assert max_chain_length([Pair(5, 24), Pair(15, 25),Pair(27, 40), Pair(50, 60)], 4) == 3"]),
 dict(task_id=602, text="Write a python function to find the first repeated character in a given string.",
      code="", test_list=['assert first_repeated_char("abcabc") == "a"']),
 dict(task_id=603, text="Write a function to get a lucid number smaller than or equal to n.",
      code="", test_list=["assert get_ludic(10) == [1, 2, 3, 5, 7]"]),
 dict(task_id=604, text="Write a function to reverse words in a given string.",
      code="", test_list=['assert reverse_words("python program")==("program python")']),
 dict(task_id=605, text="Write a function to check if the given integer is a prime number.",
      code="", test_list=["assert prime_num(13)==True"]),
]
ds = types.ModuleType("datasets"); ds.load_dataset = lambda name, split: MBPP
sys.modules["datasets"] = ds

CODE = {
601: '''class Pair:
    def __init__(self, a, b):
        self.a = a
        self.b = b


def max_chain_length(arr, n):
    mcl = [1] * n
    for i in range(1, n):
        for j in range(i):
            if arr[i].a > arr[j].b and mcl[i] < mcl[j] + 1:
                mcl[i] = mcl[j] + 1
    return max(mcl) if mcl else 0''',
602: '''def first_repeated_char(s):
    seen = set()
    for c in s:
        if c in seen:
            return c
        seen.add(c)
    return "None"''',
603: '''def get_ludic(n):
    ludics = list(range(1, n + 1))
    index = 1
    while index != len(ludics):
        first = ludics[index]
        remove_index = index + first
        while remove_index < len(ludics):
            ludics.remove(ludics[remove_index])
            remove_index = remove_index + first - 1
        index += 1
    return ludics''',
604: '''def reverse_words(s):
    return " ".join(reversed(s.split()))''',
605: '''def prime_num(num):
    if num < 2:
        return False
    i = 2
    while i * i <= num:
        if num % i == 0:
            return False
        i += 1
    return True''',
}
TESTS = {
601: '''import unittest
from solution import Pair, max_chain_length

class T(unittest.TestCase):
    def test_example(self):
        self.assertEqual(max_chain_length([Pair(5, 24), Pair(15, 25), Pair(27, 40), Pair(50, 60)], 4), 3)
    def test_empty(self):
        self.assertEqual(max_chain_length([], 0), 0)
    def test_single(self):
        self.assertEqual(max_chain_length([Pair(1, 2)], 1), 1)
    def test_no_chain(self):
        self.assertEqual(max_chain_length([Pair(1, 10), Pair(2, 9)], 2), 1)

if __name__ == "__main__":
    unittest.main()''',
602: '''import unittest
from solution import first_repeated_char

class T(unittest.TestCase):
    def test_repeat(self):
        self.assertEqual(first_repeated_char("abcabc"), "a")
    def test_none(self):
        self.assertEqual(first_repeated_char("abc"), "None")
    def test_empty(self):
        self.assertEqual(first_repeated_char(""), "None")

if __name__ == "__main__":
    unittest.main()''',
603: '''import unittest
from solution import get_ludic

class T(unittest.TestCase):
    def test_10(self):
        self.assertEqual(get_ludic(10), [1, 2, 3, 5, 7])
    def test_25(self):
        self.assertEqual(get_ludic(25), [1, 2, 3, 5, 7, 11, 13, 17, 23, 25])
    def test_1(self):
        self.assertEqual(get_ludic(1), [1])

if __name__ == "__main__":
    unittest.main()''',
604: '''import unittest
from solution import reverse_words

class T(unittest.TestCase):
    def test_two(self):
        self.assertEqual(reverse_words("python program"), "program python")
    def test_empty(self):
        self.assertEqual(reverse_words(""), "")

if __name__ == "__main__":
    unittest.main()''',
605: '''import unittest
from solution import prime_num

class T(unittest.TestCase):
    def test_prime(self):
        self.assertTrue(prime_num(13))
    def test_composite(self):
        self.assertFalse(prime_num(9))
    def test_small(self):
        self.assertFalse(prime_num(1))
    def test_two(self):
        self.assertTrue(prime_num(2))

if __name__ == "__main__":
    unittest.main()''',
}

# ---------- fake OpenRouter HTTP ----------
import requests
LOG = []
class R:
    def __init__(self, code, data): self.status_code, self._d, self.text = code, data, json.dumps(data)
    def json(self): return self._d
def fake_get(url, **kw):
    LOG.append(("GET", url))
    return R(200, {"data": [
        {"id": "openrouter/auto", "pricing": {"prompt": "-1", "completion": "-1"}},
        {"id": "paid/model", "pricing": {"prompt": "0.000001", "completion": "0.000002"}},
        {"id": "qwen/qwen-fake:free", "pricing": {"prompt": "0", "completion": "0"}},
    ]})
def task_id_from(prompt):
    for t in MBPP:
        if t["text"] in prompt: return t["task_id"]
def fake_post(url, json=None, **kw):
    p = json["messages"][0]["content"]
    LOG.append(("POST", json["model"], json["temperature"], json["max_tokens"]))
    tid = task_id_from(p)
    out = TESTS[tid] if "Test Generator Agent" in p else CODE[tid]
    return R(200, {"model": json["model"], "choices": [{"message": {"content": out}}]})
requests.get, requests.post = fake_get, fake_post

if __name__ == "__main__":
    import pipeline
    pipeline.main()
    print("\nHTTP calls:", *LOG, sep="\n  ")
