"""Gate tests for static-report citation inventory."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from audit_static_citations import audit_report, extract_anchors


class StaticCitationAuditTests(unittest.TestCase):
    def test_extracts_exact_and_approximate_chunk_offsets(self):
        anchors = extract_anchors("see chunk-alpha.js@12 and chunk-beta.js@~7")
        self.assertEqual(
            anchors,
            [
                {"chunk": "chunk-alpha.js", "offset": 12, "approximate": False},
                {"chunk": "chunk-beta.js", "offset": 7, "approximate": True},
            ],
        )

    def test_marks_missing_files_and_out_of_bounds_offsets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            root.mkdir()
            (root / "chunk-alpha.js").write_text("abcdef", encoding="utf-8")
            report = Path(tmp) / "report.md"
            report.write_text(
                "chunk-alpha.js@5 chunk-alpha.js@99 chunk-missing.js@1", encoding="utf-8"
            )
            result = audit_report(report, root)

        self.assertEqual(result["anchors_total"], 3)
        self.assertEqual(result["anchors_resolvable"], 1)
        self.assertEqual(result["anchors_missing_file"], 1)
        self.assertEqual(result["anchors_out_of_bounds"], 1)


if __name__ == "__main__":
    unittest.main()
