import unittest

from solution import reverse_words


class TestReverseWords(unittest.TestCase):
    def test_empty_string(self):
        self.assertEqual(reverse_words(""), "")

    def test_single_word(self):
        self.assertEqual(reverse_words("hello"), "hello")

    def test_two_words(self):
        self.assertEqual(reverse_words("hello world"), "world hello")

    def test_multiple_words(self):
        self.assertEqual(
            reverse_words("the quick brown fox"),
            "fox brown quick the"
        )

    def test_leading_and_trailing_spaces(self):
        self.assertEqual(reverse_words("  hello world  "), "world hello")

    def test_multiple_spaces_between_words(self):
        self.assertEqual(reverse_words("hello   world"), "world hello")

    def test_whitespace_only_string(self):
        self.assertEqual(reverse_words("   \t\n  "), "")

    def test_mixed_whitespace_separators(self):
        self.assertEqual(reverse_words("a\tb\nc"), "c b a")

    def test_words_with_punctuation(self):
        self.assertEqual(reverse_words("hello, world!"), "world! hello,")

    def test_unicode_words(self):
        self.assertEqual(reverse_words("héllo wörld"), "wörld héllo")

    def test_numeric_words(self):
        self.assertEqual(reverse_words("1 2 3"), "3 2 1")

    def test_single_character_words(self):
        self.assertEqual(reverse_words("a b c"), "c b a")

    def test_duplicate_words(self):
        self.assertEqual(reverse_words("same same same"), "same same same")

    def test_returns_string(self):
        self.assertIsInstance(reverse_words("hello world"), str)


if __name__ == "__main__":
    unittest.main()