import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prompt_sections_probe as probe  # noqa: E402


def write(raw, exp, seq, body):
    folder = Path(raw) / exp / "http"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{seq:04d}-req.json").write_text(json.dumps({"body": body}), encoding="utf-8")


def main_request(system_text, tools=26, model="m"):
    return {"model": model, "system": [{"type": "text", "text": system_text}], "tools": [{"name": f"t{i}"} for i in range(tools)],
            "thinking": {"type": "adaptive"}, "output_config": {"effort": "medium"}, "max_tokens": 128000}


class SectionsTests(unittest.TestCase):
    def summarize(self, system_text, **kw):
        with tempfile.TemporaryDirectory() as raw:
            write(raw, "X", 1, {"model": "m", "system": "title", "tools": []})   # small helper request is skipped
            write(raw, "X", 2, main_request(system_text, **kw))
            probe.RAW = raw
            return probe.summarize("X")

    def test_markers_are_booleans_and_text_is_not_copied(self):
        result = self.summarize("intro\n# Delivering work\nmore than 3 queries\n")
        self.assertTrue(result["markers"]["delivering_work"])
        self.assertTrue(result["markers"]["explore_nudge"])
        self.assertFalse(result["markers"]["corrections"])
        self.assertNotIn("intro", json.dumps(result))

    def test_request_fields_are_recorded(self):
        result = self.summarize("x", tools=30)
        self.assertEqual((result["tool_count"], result["effort"], result["max_tokens"], result["thinking"]), (30, "medium", 128000, "adaptive"))

    def test_lean_and_full_dedicated_tool_markers_differ(self):
        full = self.summarize("Prefer dedicated tools over Bash")["markers"]
        lean = self.summarize("Prefer the dedicated file/search tools over shell commands")["markers"]
        self.assertTrue(full["prefer_dedicated_tools_full"] and not full["prefer_dedicated_tools_lean"])
        self.assertTrue(lean["prefer_dedicated_tools_lean"] and not lean["prefer_dedicated_tools_full"])

    def test_no_main_request_returns_none(self):
        with tempfile.TemporaryDirectory() as raw:
            write(raw, "Y", 1, {"model": "m", "system": "s", "tools": []})
            probe.RAW = raw
            self.assertIsNone(probe.summarize("Y"))


if __name__ == "__main__":
    unittest.main()
