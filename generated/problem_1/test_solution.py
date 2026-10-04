import unittest
from solution import find_longest_chain


class TestFindLongestChain(unittest.TestCase):

    def test_empty_list(self):
        self.assertEqual(find_longest_chain([]), 0)

    def test_singleton(self):
        self.assertEqual(find_longest_chain([[1, 2]]), 1)

    def test_basic_chain(self):
        pairs = [[1, 2], [3, 4], [5, 6]]
        self.assertEqual(find_longest_chain(pairs), 3)

    def test_no_chain_possible(self):
        pairs = [[1, 2], [2, 3]]
        self.assertEqual(find_longest_chain(pairs), 1)

    def test_negative_numbers(self):
        pairs = [[-3, -1], [-2, 0], [1, 2]]
        self.assertEqual(find_longest_chain(pairs), 2)

    def test_duplicate_pairs(self):
        pairs = [[1, 2], [1, 2], [1, 2]]
        self.assertEqual(find_longest_chain(pairs), 1)

    def test_unordered_input(self):
        pairs = [[3, 4], [1, 2]]