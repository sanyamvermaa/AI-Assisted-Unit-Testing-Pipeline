import unittest

from solution import first_repeated_char


class TestFirstRepeatedChar(unittest.TestCase):
    def test_empty_string_returns_none(self):
        self.assertIsNone(first_repeated_char(""))

    def test_single_character_returns_none(self):
        self.assertIsNone(first_repeated_char("a"))

    def test_no_repeated_characters_returns_none(self):
        self.assertIsNone(first_repeated_char("abc"))

    def test_immediate_repeat_returns_character(self):
        self.assertEqual(first_repeated_char("aa"), "a")

    def test_first_repeated_is_earliest_second_occurrence(self):
        self.assertEqual(first_repeated_char("abcabc"), "a")

    def test_repeat_of_later_character_before_earlier_character(self):
        self.assertEqual(first_repeated_char("abcba"), "b")

    def test_multiple_repeats_returns_first_repeated(self):
        self.assertEqual(first_repeated_char("aabbcc"), "a")

    def test_all_same_returns_first_char(self):
        self.assertEqual(first_repeated_char("aaaa"), "a")

    def test_repeat_of_space(self):
        self.assertEqual(first_repeated_char("a b a"), " ")

    def test_repeat_of_digit(self):
        self.assertEqual(first_repeated_char("121"), "1")

    def test_repeat_of_unicode(self):
        self.assertEqual(first_repeated_char("éé"), "é")

    def test_mixed_case_distinct_returns_none(self):
        self.assertIsNone(first_repeated_char("AbC"))

    def test_mixed_case_repeat(self):
        self.assertEqual(first_repeated_char("aAa"), "a")

    def test_two_chars_one_repeat(self):
        self.assertEqual(first_repeated_char("bb"), "b")

    def test_long_no_repeat(self):
        self.assertIsNone(first_repeated_char("abcdefg"))

    def test_repeat_at_end(self):
        self.assertEqual(first_repeated_char("abcdefa"), "a")


if __name__ == "__main__":
    unittest.main()