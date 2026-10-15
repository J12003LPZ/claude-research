import unittest
from money import format_total


class Accept(unittest.TestCase):
    def test_eur(self):
        self.assertEqual(format_total(123456, "EUR"), "1.234,56 \u20ac")

    def test_eur_small(self):
        self.assertEqual(format_total(5, "EUR"), "0,05 \u20ac")

    def test_eur_millions(self):
        self.assertEqual(format_total(123456789, "EUR"), "1.234.567,89 \u20ac")

    def test_unknown_currency(self):
        with self.assertRaises(ValueError):
            format_total(100, "GBP")

    def test_usd_characterization(self):
        table = {0: "$0.00", 5: "$0.05", 100: "$1.00", 123456: "$1,234.56",
                 123456789: "$1,234,567.89", -150: "$-2.50", -5: "$-1.95"}
        for cents, want in table.items():
            self.assertEqual(format_total(cents), want, cents)

    def test_usd_explicit_matches_default(self):
        self.assertEqual(format_total(99999, "USD"), format_total(99999))


if __name__ == "__main__":
    unittest.main()
