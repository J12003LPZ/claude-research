"""Gate tests for static-report claim inventory."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from audit_static_claims import inventory_report


class StaticClaimInventoryTests(unittest.TestCase):
    def test_records_heading_lines_hash_and_anchor_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            root.mkdir()
            (root / "chunk-alpha.js").write_text("abcdef", encoding="utf-8")
            report = Path(tmp) / "report.md"
            report.write_text(
                "# Title\n\n## Section\n\nA fact. `chunk-alpha.js@2` evidence.\n\n"
                "A second fact without a source.\n",
                encoding="utf-8",
            )
            result = inventory_report(report, root)

        self.assertEqual(result["units_total"], 2)
        self.assertEqual(result["units_all_anchors_resolvable"], 1)
        self.assertEqual(result["units_without_anchors"], 1)
        self.assertEqual(result["units"][0]["heading"], "Section")
        self.assertEqual(result["units"][0]["line_start"], 5)
        self.assertEqual(len(result["units"][0]["text_sha256"]), 16)


if __name__ == "__main__":
    unittest.main()
