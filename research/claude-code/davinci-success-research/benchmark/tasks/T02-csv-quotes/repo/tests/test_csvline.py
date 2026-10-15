import unittest
from csvline import parse_line


class CsvTests(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(parse_line("a,b,c"), ["a", "b", "c"])

    def test_single(self):
        self.assertEqual(parse_line("abc"), ["abc"])


if __name__ == "__main__":
    unittest.main()
