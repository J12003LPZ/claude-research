import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build_manifest import fault_was_injected


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


if __name__ == "__main__":
    unittest.main()
