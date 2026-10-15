import unittest
from csvline import parse_line


class Accept(unittest.TestCase):
    def test_comma_inside_quotes(self):
        self.assertEqual(parse_line('a,"b,c",d'), ["a", "b,c", "d"])

    def test_escaped_quote(self):
        self.assertEqual(parse_line('"say ""hi""",x'), ['say "hi"', "x"])

    def test_empty_fields(self):
        self.assertEqual(parse_line("a,,c"), ["a", "", "c"])

    def test_trailing_comma(self):
        self.assertEqual(parse_line("a,b,"), ["a", "b", ""])

    def test_empty_line_is_one_empty_field(self):
        self.assertEqual(parse_line(""), [""])

    def test_quoted_empty(self):
        self.assertEqual(parse_line('"",x'), ["", "x"])

    def test_plain_unchanged(self):
        self.assertEqual(parse_line("a,b,c"), ["a", "b", "c"])

    def test_unterminated_quote(self):
        with self.assertRaises(ValueError):
            parse_line('a,"b')


if __name__ == "__main__":
    unittest.main()
