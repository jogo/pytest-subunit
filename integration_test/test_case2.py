import unittest


class Tests(unittest.TestCase):
    def test_true(self):
        assert True

    def test_false(self):
        # Expected to fail
        assert False