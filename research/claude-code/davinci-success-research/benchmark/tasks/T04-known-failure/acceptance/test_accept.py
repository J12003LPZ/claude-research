import unittest
import slug
from slug import slugify


class Accept(unittest.TestCase):
    def test_runs_collapse(self):
        self.assertEqual(slugify("Hello,   World!!"), "hello-world")

    def test_strip_ends(self):
        self.assertEqual(slugify("  --Hi--  "), "hi")

    def test_digits_kept(self):
        self.assertEqual(slugify("Python 3.12 Release"), "python-3-12-release")

    def test_empty_result(self):
        self.assertEqual(slugify("!!!"), "")

    def test_empty_input(self):
        self.assertEqual(slugify(""), "")

    def test_non_ascii_becomes_separator(self):
        self.assertEqual(slugify("caf\u00e9 au lait"), "caf-au-lait")

    def test_no_third_party_import(self):
        import inspect
        src = inspect.getsource(slug)
        self.assertNotIn("unidecode", src)


if __name__ == "__main__":
    unittest.main()
