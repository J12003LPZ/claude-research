import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from summarize_captures import sanitize_run, summarize_debug


class SanitizeRunTests(unittest.TestCase):
    def test_masks_stdin_file_and_nested_fault_metadata(self):
        run = {
            "cwd": r"C:\Users\sergi\cc-rea-lab\proj-hooks",
            "argv": [r"C:\Users\sergi\Desktop\claude-rea\lab\raw\E31\debug.log"],
            "prompt": "PRIVATE-PROMPT-TOKEN-7319",
            "exe_sha256": "76de74f7694a5bdc03378a5f837c9e132827bf004c98c276bc4e9094ff06769a",
            "stdin_file": r"C:\Users\sergi\cc-rea-lab\compact-flood.txt",
            "fault": {"body": {"message": r"C:\Users\sergi\private\prompt.txt"}},
        }

        sanitized = sanitize_run(run)

        self.assertNotIn("sergi", str(sanitized))
        self.assertNotIn("PRIVATE-PROMPT-TOKEN-7319", str(sanitized))
        self.assertEqual(sanitized["exe_sha256"], "76de74f7694a5bdc03378a5f837c9e132827bf004c98c276bc4e9094ff06769a")
        self.assertEqual(set(sanitized["prompt"]), {"len", "sha256"})
        self.assertEqual(sanitized["prompt"]["len"], len("PRIVATE-PROMPT-TOKEN-7319"))
        self.assertEqual(sanitized["stdin_file"], r"C:\Users\<user>\cc-rea-lab\compact-flood.txt")
        self.assertEqual(
            sanitized["fault"]["body"]["message"],
            r"C:\Users\<user>\private\prompt.txt",
        )

    def test_does_not_mutate_input(self):
        run = {"cwd": r"C:\Users\sergi\cc-rea-lab\proj-hooks", "argv": []}

        sanitize_run(run)

        self.assertEqual(run["cwd"], r"C:\Users\sergi\cc-rea-lab\proj-hooks")

    def test_debug_summary_keeps_compaction_failure_signals(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "debug.log"
            path.write_text(
                "2026-10-14T00:00:00Z [ERROR] Reactive compact: summarization returned API error\n"
                "2026-10-14T00:00:01Z [DEBUG] [API REQUEST] /v1/messages source=compact\n",
                encoding="utf-8",
            )

            summary = summarize_debug(str(path))

        self.assertEqual(len(summary["signals"]), 2)
        self.assertIn("Reactive compact", summary["signals"][0])
        self.assertIn("source=compact", summary["signals"][1])


if __name__ == "__main__":
    unittest.main()
