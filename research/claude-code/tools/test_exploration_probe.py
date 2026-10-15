import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import exploration_probe as probe  # noqa: E402


def conversation(results, notes=()):
    """results: list of (tool name, input, content, is_error)."""
    messages = [{"role": "user", "content": [{"type": "text", "text": "go"}]}]
    for i, (name, inp, content, err) in enumerate(results):
        messages.append({"role": "assistant", "content": [{"type": "tool_use", "id": f"t{i}", "name": name, "input": inp}]})
        messages.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": f"t{i}", "content": content,
                                                     "is_error": err}]})
    for note in notes:
        messages.append({"role": "system", "content": [{"type": "text", "text": note}]})
    return {"model": "m", "messages": messages}


class SummaryTests(unittest.TestCase):
    def test_counts_and_markers(self):
        body = conversation([("Glob", {"pattern": "**/*.txt"}, "a\nb\n(Showing 2 of 5 matching files; 3 more are not listed.)", False)])
        row = probe.summarize_conversation(body)["tool_calls"][0]
        self.assertEqual(row["tool"], "Glob")
        self.assertEqual(row["lines"], 3)
        self.assertEqual(row["input"], {"pattern": "**/*.txt"})
        self.assertIn("glob_showing_note", row["markers"])
        self.assertEqual(row["first_lines"], ["a", "b", "(Showing 2 of 5 matching files; 3 more are not listed.)"])
        self.assertEqual(row["last_lines"], row["first_lines"])
        self.assertFalse(row["is_error"])

    def test_home_paths_are_masked_and_long_lines_cut(self):
        path = "C:\\Users\\someone\\lab\\a.txt"
        body = conversation([("Read", {"file_path": path}, path + " " + "x" * 400, True)])
        row = probe.summarize_conversation(body)["tool_calls"][0]
        self.assertNotIn("someone", json.dumps(row))
        self.assertTrue(row["first_line"].startswith("<home>/lab/a.txt"))
        self.assertLessEqual(len(row["first_line"]), 160)
        self.assertEqual(row["input"], {"file_path": f"<str {len(path)} chars>"})
        self.assertTrue(row["is_error"])

    def test_edit_text_is_never_copied(self):
        body = conversation([("Edit", {"file_path": "p", "old_string": "SECRET-OLD", "new_string": "SECRET-NEW"}, "ok", False)])
        self.assertNotIn("SECRET", json.dumps(probe.summarize_conversation(body)))

    def test_truncation_note_comes_from_system_role_only(self):
        body = conversation([("Read", {}, "1\tx", False)], notes=["[Truncated: PARTIAL view - C:\\Users\\u\\f.txt: showing lines 1-5"])
        body["messages"].append({"role": "user", "content": "[Truncated: not a system note"})
        notes = probe.summarize_conversation(body)["truncation_notes"]
        self.assertEqual(len(notes), 1)
        self.assertIn("<home>/f.txt", notes[0])

    def test_partial_view_notice_inside_tool_result_is_a_marker(self):
        notice = "\n\n<system-reminder>\n[Truncated: PARTIAL view - f]\n</system-reminder>"
        body = conversation([("Read", {}, "1\tx" + notice, False)])
        row = probe.summarize_conversation(body)["tool_calls"][0]
        self.assertIn("partial_view_notice", row["markers"])
        self.assertEqual(probe.summarize_conversation(body)["truncation_notes"], [])

    def test_last_request_is_the_longest_conversation(self):
        with tempfile.TemporaryDirectory() as tmp:
            http = Path(tmp) / "E1" / "http"
            http.mkdir(parents=True)
            for seq, n in (("0001", 1), ("0002", 3)):
                (http / f"{seq}-req.json").write_text(json.dumps({
                    "url": "/v1/messages?beta=true",
                    "body": conversation([("Glob", {"pattern": "*"}, "r", False)] * n)}), encoding="utf-8")
            (http / "0003-req.json").write_text(json.dumps({"url": "/api/hello", "body": None}), encoding="utf-8")
            last = probe.last_messages_request(str(Path(tmp) / "E1"))
            self.assertEqual(len(probe.summarize_conversation(last["body"])["tool_calls"]), 3)


if __name__ == "__main__":
    unittest.main()
