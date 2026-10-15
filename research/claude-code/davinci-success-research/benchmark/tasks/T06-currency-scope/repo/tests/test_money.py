import unittest
from money import format_total


class MoneyTests(unittest.TestCase):
    def test_usd(self):
        self.assertEqual(format_total(123456), "$1,234.56")


if __name__ == "__main__":
    unittest.main()
