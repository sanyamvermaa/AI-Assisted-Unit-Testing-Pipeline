import unittest
from solution import is_prime

class TestIsPrime(unittest.TestCase):
    def test_non_positive(self):
        self.assertFalse(is_prime(0))
        self.assertFalse(is_prime(1))
        self.assertFalse(is_prime(-1))
        self.assertFalse(is_prime(-10))

    def test_small_numbers(self):
        self.assertTrue(is_prime(2))
        self.assertTrue(is_prime(3))
        self.assertFalse(is_prime(4))
        self.assertFalse(is_prime(6))
        self.assertFalse(is_prime(8))
        self.assertFalse(is_prime(9))
        self.assertFalse(is_prime(15))

    def test_prime_numbers(self):
        primes = [5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97]
        for p in primes:
            with self.subTest(p=p):
                self.assertTrue(is_prime(p))

    def test_composite_numbers(self):
        composites = [4,6,8,9,10,12,14,15,16,18,20,21,22,24,25,26,27,28,30,32,33,34,35,36,38,39,40,42,44,45,46,48,49,50,51,52,54,55,56,57,58,60,62,63,64,65,66,68,69,70,72,74,75,76,77,78,80,81,82,84,85,86,87,88,90,91,92,93,94,95,96,98,99,100]
        for n in composites:
            with self.subTest(n=n):
                self.assertFalse(is_prime(n))

    def test_boundary_values(self):
        self.assertFalse(is_prime(0))
        self.assertFalse(is_prime(1))
        self.assertTrue(is_prime(2))
        self.assertTrue(is_prime(3))
        self.assertFalse(is_prime(4))

    def test_negative_numbers(self):
        for n in [-1, -2, -3, -10, -100]:
            self.assertFalse(is_prime(n))

    def test_large_numbers(self):
        primes = [101,103,107,109,113,127,131,137,139,149,151,157,163,167,173,179,181,191,193,197,199]
        for p in primes:
            with self.subTest(p=p):
                self.assertTrue(is_prime(p))

        self.assertFalse(is_prime(100))
        self.assertFalse(is_prime(1024))
        self.assertFalse(is_prime(1048576))
        self.assertFalse(is_prime(999984))

    def test_loop_iteration_cases(self):
        # zero iterations
        self.assertTrue(is_prime(2))
        self.assertTrue(is_prime(3))
        self.assertTrue(is_prime(5))

        # one or more iterations
        self.assertFalse(is_prime(25))   # 5*5, loop runs once
        self.assertFalse(is_prime(121))  # 11*11, loop runs twice
        self.assertFalse(is_prime(221))  # 13*17, loop runs multiple times

if __name__ == '__main__':
    unittest.main()