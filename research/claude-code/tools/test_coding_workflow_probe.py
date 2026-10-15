import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import coding_workflow_probe as probe  # noqa: E402


def body(system_text="", messages=None, tools=("Read", "Write")):
    return {"model": "m", "system": [{"type": "text", "text": system_text}], "tools": [{"name": t} for t in tools],
            "messages": messages or [{"role": "user", "content": [{"type": "text", "text": "hi"}]}]}


class ProbeTests(unittest.TestCase):
    def test_markers_split_system_from_messages(self):
        sysmsg = {"role": "system", "content": [{"type": "text", "text": "## Proactivity: high\n- Commit without asking"}]}
        b = body("# Executing actions with care\nx", [{"role": "user", "content": "hi"}, sysmsg])
        r = probe.summarize_request(b)
        self.assertTrue(r["markers"]["executing_actions_heading"])
        self.assertTrue(r["markers_in_system"]["executing_actions_heading"])
        self.assertTrue(r["markers"]["proactivity_heading"])
        self.assertFalse(r["markers_in_system"]["proactivity_heading"])
        self.assertEqual(r["proactivity_levels_found"], ["high"])
        self.assertEqual(r["tool_names"], ["Read", "Write"])

    def test_no_prompt_text_is_emitted(self):
        secret = "ZZ-UNIQUE-PROMPT-TEXT-9183"
        r = probe.summarize_request(body(secret))
        self.assertNotIn(secret, json.dumps(r))

    def test_tool_results_are_scrubbed_of_home_paths(self):
        msg = {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t1", "is_error": True,
                                            "content": "Cannot write to C:\\Users\\someone\\lab\\src\\app.py while in plan mode."}]}
        r = probe.summarize_request(body("", [msg]))
        text = r["tool_results"][0]["text_head"]
        self.assertNotIn("someone", text)
        self.assertIn("<home>/lab/src/app.py", text)
        self.assertTrue(r["tool_results"][0]["is_error"])

    def test_main_writes_sanitized_file_from_raw_capture(self):
        with tempfile.TemporaryDirectory() as raw, tempfile.TemporaryDirectory() as out:
            http = Path(raw) / "E99-x" / "http"
            http.mkdir(parents=True)
            (http / "0001-req.json").write_text(json.dumps({"seq": "0001", "url": "/api/hello", "body": None}))
            (http / "0002-req.json").write_text(json.dumps({"seq": "0002", "url": "/v1/messages?beta=true", "body": body("x")}))
            (http / "0002-res.json").write_text(json.dumps({"status": 200}))
            (Path(raw) / "E99-x" / "stdout.jsonl").write_text(
                json.dumps({"type": "system", "subtype": "init", "permissionMode": "auto"}) + "\n" +
                json.dumps({"type": "result", "subtype": "success", "is_error": False, "num_turns": 1,
                            "terminal_reason": "completed", "permission_denials": [{"tool_name": "Write"}]}) + "\n")
            argv = sys.argv
            sys.argv = ["probe", "E99-x", "--raw-root", raw, "--out", out]
            try:
                probe.main()
            finally:
                sys.argv = argv
            d = json.loads((Path(out) / "E99-x" / "coding-workflow-probe.json").read_text())
            self.assertEqual(d["message_requests"], 1)
            self.assertEqual(d["requests"][0]["response_status"], 200)
            self.assertEqual(d["stream"]["init_permission_mode"], "auto")
            self.assertEqual(d["stream"]["results"][0]["permission_denial_count"], 1)


if __name__ == "__main__":
    unittest.main()
