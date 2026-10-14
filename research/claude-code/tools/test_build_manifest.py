import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import getpass

from build_manifest import FORBIDDEN, fault_was_injected


class FaultManifestTests(unittest.TestCase):
    def test_requires_an_injected_response(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "http-summary.json").write_text(
                json.dumps([{"response": {"status": 429, "injected": False}}]),
                encoding="utf-8",
            )
            self.assertFalse(fault_was_injected(str(directory)))

    def test_detects_an_injected_response(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "http-summary.json").write_text(
                json.dumps([{"response": {"status": 529, "injected": True}}]),
                encoding="utf-8",
            )
            self.assertTrue(fault_was_injected(str(directory)))


class RedactionPatternTests(unittest.TestCase):
    def hits(self, text):
        return [label for label, rx in FORBIDDEN if rx.search(text)]

    def test_bare_account_name_is_forbidden_not_only_paths(self):
        user = getpass.getuser()
        self.assertIn("account-name", self.hits(f"**User identity**: `{user}`"))
        self.assertIn("account-name", self.hits(f"owner={user.upper()}"))

    def test_account_name_inside_a_longer_word_is_not_a_hit(self):
        user = getpass.getuser()
        self.assertEqual(self.hits(f"x{user}y and {user}2"), [])


if __name__ == "__main__":
    unittest.main()
