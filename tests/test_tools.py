import unittest

from wildpath.tools import flatten


class TestTools(unittest.TestCase):

    def test_flatten_string_items(self):
        L = [["a", "b"], ["c", "d"], ["e", "f", "g"]]
        self.assertEqual(flatten(L, depth=1), ['a', 'b', 'c', 'd', 'e', 'f', 'g'])