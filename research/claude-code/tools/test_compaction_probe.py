import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compaction_probe as probe  # noqa: E402


def write(raw, exp, seq, body, url="/v1/messages?beta=true"):
    folder = Path(raw) / exp / "http"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{seq:04d}-req.json").write_text(json.dumps({"url": url, "body": body, "body_bytes": 10}), encoding="utf-8")


def text_msg(role, text):
    return {"role": role, "content": [{"type": "text", "text": text}]}


SUMMARY = (probe.SUMMARY_LEAD + " that ran out of context.\n\nSummary:\n" + probe.SUMMARY_MARKER +
           "\n\nIf you need specific details from before compaction (like exact code snippets), read the full transcript at: p\n" +
           probe.CONTINUE_LINE + " without asking.\n\n" + probe.KEPT_TAIL_NOTE)
ATTACH = ('Called the Read tool with the following input: {"file_path":"C:\\\\Users\\\\u\\\\p\\\\src\\\\app.py"}\n1\tx\n\n'
          "Note: C:\\Users\\u\\p\\src\\util.py was read before the last conversation was summarized, but the contents are too large to include.\n"
          'Called the Read tool with the following input: {"file_path":"C:\\\\Users\\\\u\\\\p\\\\src\\\\b.txt"}\n1\ty\n')


def fixture(raw, instruction="CRITICAL: Respond with TEXT ONLY. x", same_system=True):
    system = [{"type": "text", "text": "sys"}]
    tools = [{"name": "Read"}]
    turn = {"model": "m", "system": system, "tools": tools, "messages": [
        text_msg("user", probe.ORIGINAL_PROMPT + " go"),
        {"role": "assistant", "content": [{"type": "tool_use", "id": probe.TOOL_ID_PREFIX + "1", "name": "Bash", "input": {}}]},
        {"role": "user", "content": [{"type": "tool_result", "tool_use_id": probe.TOOL_ID_PREFIX + "1", "content": probe.FAILING_TEST}]},
    ]}
    write(raw, "B1-turn", 2, turn)
    comp = {"model": "m", "system": system if same_system else [{"type": "text", "text": "other"}], "tools": tools,
            "messages": turn["messages"] + [{"role": "user", "content": [
                {"type": "text", "text": "ctx"}, {"type": "text", "text": instruction + "\n\nAdditional Instructions:\n" + probe.COMMAND_ARG}]}]}
    write(raw, "B2-compact", 2, comp)
    write(raw, "B2-compact", 3, {"messages": [text_msg("user", "x")]}, url="/v1/messages/count_tokens?beta=true")
    after = {"model": "m", "system": system, "tools": tools, "messages": [
        text_msg("user", SUMMARY),
        text_msg("user", "CLAUDE.md: " + probe.PROJECT_INSTRUCTION + " /compact " + probe.COMMAND_ARG + " COMPACT-LAB after"),
        {"role": "system", "content": [{"type": "text", "text": ATTACH}]},
    ]}
    write(raw, "B3-after", 2, after)
    return instruction


class SummarizeTests(unittest.TestCase):
    def run_probe(self, **kw):
        with tempfile.TemporaryDirectory() as raw:
            fixture(raw, **kw)
            return probe.summarize("B", raw_root=raw)

    def test_summary_message_markers(self):
        s = self.run_probe()["after_request"]["summary_message"]
        self.assertTrue(all(s[k] for k in ("is_first_message", "has_canned_summary", "analysis_stripped", "summary_tag_rewritten",
                                           "has_transcript_pointer", "has_continue_guidance", "has_kept_tail_note")))
        self.assertFalse(s["has_arm_resume_guidance"])

    def test_restored_files_keep_order_and_status(self):
        files = self.run_probe()["after_request"]["restored_files"]
        self.assertEqual([(f["name"], f["status"]) for f in files],
                         [("app.py", "content"), ("util.py", "note_too_large"), ("b.txt", "content")])

    def test_what_is_gone(self):
        gone = self.run_probe()["after_request"]["absent_after_compaction"]
        self.assertTrue(all(gone.values()), gone)

    def test_compact_request_shape_and_prefix_sharing(self):
        c = self.run_probe()["compact_request"]
        self.assertTrue(c["same_system_text_as_turn"])
        self.assertFalse(c["cache_control_differs_from_turn"])
        self.assertTrue(c["same_tools_as_turn"])
        self.assertTrue(c["carries_custom_instruction"])
        self.assertTrue(c["history_contains_turn_tool_ids"])
        self.assertEqual(c["count_tokens_calls"], 1)
        self.assertFalse(c["static_prompts_checked"])

    def test_system_difference_is_reported(self):
        self.assertFalse(self.run_probe(same_system=False)["compact_request"]["same_system_text_as_turn"])

    def test_no_prompt_text_is_emitted(self):
        blob = json.dumps(self.run_probe())
        for needle in ("Keep failing test names", "FAILED: add", "read the full transcript", "CRITICAL: Respond"):
            self.assertNotIn(needle, blob)
        self.assertNotIn("Users", blob)

    def test_single_process_layout_is_split_at_the_compaction_request(self):
        with tempfile.TemporaryDirectory() as raw:
            system, tools = [{"type": "text", "text": "sys"}], [{"name": "Read"}]
            turn = {"model": "m", "system": system, "tools": tools, "messages": [text_msg("user", probe.ORIGINAL_PROMPT)]}
            comp = {"model": "m", "system": system, "tools": tools, "messages": turn["messages"] + [text_msg("user", "CRITICAL: Respond with TEXT ONLY")]}
            edits = [{"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": "toolu_cp_x1", "content": "The file p has been updated successfully."},
                {"type": "tool_result", "tool_use_id": "toolu_cp_x2", "content": "<tool_use_error>File has not been read yet. Read it first</tool_use_error>"},
                {"type": "tool_result", "tool_use_id": "toolu_cp_x3", "content": "odd"}]}]
            after = {"model": "m", "system": system, "tools": tools, "messages": [text_msg("user", SUMMARY)] + edits}
            for seq, body in enumerate((turn, comp, after), start=2):
                write(raw, "S0-single", seq, body)
            result = probe.summarize("S", raw_root=raw)
            self.assertEqual(result["out_dir"], "S0-single")
            self.assertEqual(result["after_request"]["edit_results_after"],
                             {"toolu_cp_x1": "applied", "toolu_cp_x2": "refused_not_read", "toolu_cp_x3": "other"})

    def test_missing_compaction_request_fails_loudly(self):
        with tempfile.TemporaryDirectory() as raw:
            fixture(raw, instruction="not the prompt")
            with self.assertRaises(SystemExit):
                probe.summarize("B", raw_root=raw)


if __name__ == "__main__":
    unittest.main()
