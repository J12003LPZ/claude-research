"""Tests for source_pins.py, plus a live check of the committed pins when the extraction exists."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import source_pins  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
PINS = Path(__file__).resolve().parents[1] / "final-runtime-control-decompilation" / "13-source-pins.json"


def default_root():
    env = os.environ.get("REA_EXTRACT_ROOT")
    if env:
        return Path(env)
    for base in (REPO, *REPO.parents):
        candidate = base / "extracted" / "2.1.296" / "~BUN" / "root"
        if candidate.is_dir():
            return candidate
    return None


class CheckPinsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        (Path(self.tmp.name) / "chunk-a.js").write_text("abc function foo(){} tail", encoding="utf-8")

    def check(self, anchor, expect):
        return source_pins.check_pins([{"anchor": anchor, "expect": expect}], self.tmp.name)[0]["status"]

    def test_ok_when_literal_starts_at_offset(self):
        self.assertEqual(self.check("chunk-a.js@4", "function foo("), "ok")

    def test_mismatch_when_offset_is_off_by_one(self):
        self.assertEqual(self.check("chunk-a.js@5", "function foo("), "mismatch")

    def test_out_of_bounds(self):
        self.assertEqual(self.check("chunk-a.js@999", "x"), "out_of_bounds")

    def test_missing_file(self):
        self.assertEqual(self.check("chunk-zzz.js@0", "x"), "missing_file")

    def test_uncited_pin_is_reported(self):
        report = Path(self.tmp.name) / "r.md"
        report.write_text("see chunk-a.js@4 only", encoding="utf-8")
        pins = [{"anchor": "chunk-a.js@4", "expect": "f"}, {"anchor": "chunk-a.js@9", "expect": "f"}]
        self.assertEqual(source_pins.uncited(pins, [report]), ["chunk-a.js@9"])

    def test_main_exit_status(self):
        pins = Path(self.tmp.name) / "p.json"
        pins.write_text(json.dumps({"pins": [{"anchor": "chunk-a.js@4", "expect": "function foo("}]}), encoding="utf-8")
        self.assertEqual(source_pins.main(["--root", self.tmp.name, "--pins", str(pins)]), 0)
        pins.write_text(json.dumps({"pins": [{"anchor": "chunk-a.js@5", "expect": "function foo("}]}), encoding="utf-8")
        self.assertEqual(source_pins.main(["--root", self.tmp.name, "--pins", str(pins)]), 1)


class CommittedPinsTest(unittest.TestCase):
    def test_every_committed_pin_matches_the_extraction(self):
        root = default_root()
        if root is None:
            self.skipTest("extraction not present; set REA_EXTRACT_ROOT")
        pins = json.loads(PINS.read_text(encoding="utf-8"))["pins"]
        self.assertGreater(len(pins), 50)
        failed = [r for r in source_pins.check_pins(pins, root) if r["status"] != "ok"]
        self.assertEqual(failed, [])

    def test_pin_file_has_unique_anchors(self):
        pins = json.loads(PINS.read_text(encoding="utf-8"))["pins"]
        anchors = [p["anchor"] for p in pins]
        self.assertEqual(len(anchors), len(set(anchors)))


if __name__ == "__main__":
    unittest.main()
