import unittest
from solution import is_prime


class TestIsPrime(unittest.TestCase):
    def test_negative_numbers(self):
        self.assertFalse(is_prime(-1))
        self.assertFalse(is_prime(-2))
        self.assertFalse(is_prime(-10))
        self.assertFalse(is_prime(-100))

    def test_zero_and_one(self):
        self.assertFalse(is_prime(0))
        self.assertFalse(is_prime(1))

    def test_two(self):
        self.assertTrue(is_prime(2))

    def test_even_numbers_greater_than_two(self):
        for n in [4, 6, 8, 10, 12, 14, 16, 18, 20, 100]:
            self.assertFalse(is_prime(n), f"{n} should not be prime")

    def test_small_primes(self):
        primes = [3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]
        for p in primes:
            self.assertTrue(is_prime(p), f"{p} should be prime")

    def test_small_non_primes_odd(self):
        non_primes = [9, 15, 21, 25, 27, 33, 35, 39, 45, 49, 51, 55, 57, 63, 65, 69, 75, 77, 81, 85, 87, 91, 93, 95, 99]
        for n in non_primes:
            self.assertFalse(is_prime(n), f"{n} should not be prime")

    def test_large_prime(self):
        self.assertTrue(is_prime(9973))

    def test_large_non_prime(self):
        self.assertFalse(is_prime(9999))
        self.assertFalse(is_prime(10000))
        self.assertFalse(is_prime(10001))

    def test_loop_zero_iterations(self):
        # n=3 -> i=3, 3*3=9 > 3, loop body never executes
        self.assertTrue(is_prime(3))

    def test_loop_one_iteration(self):
        # n=9 -> i=3, 3*3=9 <=9, one iteration, returns False
        self.assertFalse(is_prime(9))

    def test_loop_multiple_iterations(self):
        # n=25 -> i=3 (3*3=9<=25), i=5 (5*5=25<=25) -> two iterations
        self.assertFalse(is_prime(25))
        # n=49 -> i=3,5,7 -> three iterations
        self.assertFalse(is_prime(49))


if __name__ == "__main__":
    unittest.main()