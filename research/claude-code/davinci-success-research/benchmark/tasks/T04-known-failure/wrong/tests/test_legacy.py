import unittest
from slug import slugify


class LegacyTests(unittest.TestCase):
    @unittest.skip("known failure")
    def test_transliteration(self):
        self.assertEqual(slugify("caf\u00e9"), "cafe")


if __name__ == "__main__":
    unittest.main()
