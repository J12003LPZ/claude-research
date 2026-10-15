import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REPORTS = ROOT / "research" / "claude-code"


class ReportConsistencyTests(unittest.TestCase):
    def test_daemon_report_distinguishes_runtime_boundaries(self):
        text = (REPORTS / "03-runtime-experiments.md").read_text(encoding="utf-8")
        self.assertIn("E84's successful background-session `respawn` is a separate path", text)
        self.assertIn("`POST /v1/messages?beta=true` and received HTTP 401", text)
        self.assertIn("Marker\n  absence is not independent proof of input-forwarding rejection", text)
        self.assertIn("resume/autocompact scenarios can use", text)
        self.assertIn("each run's `run.json` argv is authoritative", text)

    def test_matrix_records_pty_and_model_limits(self):
        text = (REPORTS / "06-verification-matrix.md").read_text(encoding="utf-8")
        self.assertIn("E85 proves Windows PTY byte transport", text)
        self.assertIn("E92 also attempted `POST /v1/messages?beta=true` and received 401", text)
        self.assertIn("authenticated PTY success and supervisor worker respawn remain untested", text)

    def test_readme_scopes_side_entry_and_scripted_runs(self):
        text = (REPORTS / "README.md").read_text(encoding="utf-8")
        self.assertIn("Supplemental daemon, worker, PTY, and attach probes", text)
        self.assertIn("local scripted proxy", text)
        self.assertIn("2,186", text)
        self.assertIn("941 report paragraphs", text)
        self.assertNotIn("headless mode only", text)
        self.assertNotIn("Each experiment makes real model requests", text)

    def test_static_decompilation_supplement_is_present(self):
        text = (REPORTS / "static-05-subagents-sessions-rendering.md").read_text(encoding="utf-8")
        self.assertIn("Source-level decompilation supplement", text)
        self.assertIn("Fresh scheduler decompilation", text)
        self.assertIn("Fresh input and Escape decompilation", text)
        for anchor in ("chunk-39q3j8sd.js@47617", "chunk-v44rfc3q.js@319644", "chunk-9w4htdvs.js@1251327"):
            self.assertIn(anchor, text)

    def test_coding_workflow_layer_is_documented(self):
        text = (REPORTS / "static-02-prompt-context-compaction.md").read_text(encoding="utf-8")
        for needle in ("Coding-workflow layer: what the CLI actually instructs",
                       "chunk-phacttch.js@2001457", "chunk-phacttch.js@4442619",
                       "chunk-phacttch.js@107269", "chunk-phacttch.js@201549",
                       "chunk-phacttch.js@3641002", "tengu_verified_vs_assumed",
                       "The loop is almost entirely prompt text",
                       "Independent implementation spec for the coding workflow"):
            self.assertIn(needle, text)

    def test_lean_prompt_correction_and_control_paths_are_documented(self):
        text = (REPORTS / "static-02-prompt-context-compaction.md").read_text(encoding="utf-8")
        for needle in ("Audit correction (twenty-sixth pass)",
                       "Coding-workflow control paths and the lean prompt (twenty-sixth source pass)",
                       "chunk-phacttch.js@2019875", "chunk-bykygzr4.js@6140", "chunk-wccxtr0h.js@1959",
                       "chunk-z3vv06zx.js@7602", "chunk-phacttch.js@2086295", "chunk-306ef358.js@12822",
                       "No built-in reviewer, verifier or debugger exists in the default registry"):
            self.assertIn(needle, text)
        runtime = (REPORTS / "03-runtime-experiments.md").read_text(encoding="utf-8")
        self.assertIn("Coding-workflow mechanisms with a scripted model (E50)", runtime)
        matrix = (REPORTS / "06-verification-matrix.md").read_text(encoding="utf-8")
        self.assertIn("## 6. Coding-workflow checks (E50, scripted model)", matrix)

    def test_davinci_research_directory_is_complete_and_makes_no_unrun_claims(self):
        base = REPORTS / "davinci-success-research"
        for name in ("README.md", "01-runtime-verified-mechanisms.md", "02-static-findings-and-unknowns.md",
                     "03-coding-success-mechanism-model.md", "04-davinci-workflow-controller.md",
                     "05-benchmark-design.md", "06-open-questions-and-next-steps.md",
                     "controller/davinci_controller.py", "benchmark/harness.py", "benchmark/score.py",
                     "benchmark/runner.py"):
            self.assertTrue((base / name).exists(), name)
        bench = (base / "05-benchmark-design.md").read_text(encoding="utf-8")
        self.assertIn("Not run against any model", bench)
        self.assertIn("none is reported here", bench)
        readme = (base / "README.md").read_text(encoding="utf-8")
        self.assertIn("Success rate comparison: not available", readme)
        self.assertEqual(len(list((base / "benchmark" / "tasks").glob("T*/task.json"))), 6)

    def test_coding_workflow_decompilation_deliverables_are_complete(self):
        base = REPORTS / "coding-workflow-decompilation"
        names = [
            "01-complete-workflow-callgraph.md", "02-system-prompt-internals.md",
            "03-planning-mode-internals.md", "04-builtin-agents-internals.md",
            "05-tool-orchestration-internals.md", "06-failure-recovery-internals.md",
            "07-context-and-session-internals.md", "08-completion-and-verification-internals.md",
            "09-source-evidence-index.md", "10-complete-coding-workflow-reconstruction.md",
        ]
        for name in names:
            self.assertTrue((base / name).exists(), name)
        workflow = (base / "10-complete-coding-workflow-reconstruction.md").read_text(encoding="utf-8")
        for needle in ("Ad", "H5t", "ExitPlanMode", "Qj", "Stop/SubagentStop", "does not contain a general acceptance controller"):
            self.assertIn(needle, workflow)
        evidence = (base / "09-source-evidence-index.md").read_text(encoding="utf-8")
        self.assertIn("REA MCP was disconnected", evidence)
        self.assertIn("chunk-93pksqr2.js@126966", evidence)

    def test_supervisor_and_screen_diff_bodies_are_documented(self):
        text = (REPORTS / "static-05-subagents-sessions-rendering.md").read_text(encoding="utf-8")
        for needle in ("Supervisor body `Mt`", "Screen diff `Zd`", "Kept bytes and front-cut rows",
                       "chunk-39q3j8sd.js@53230", "chunk-v44rfc3q.js@254020",
                       "Background manager `Pt`", "Worker class `Ke`", "Daemon auth manager `Y$o`",
                       "Service install paths", "Key and kitty decoding tables", "**Producer (fresh pass):**",
                       "onRenderScreenReader", "**Resize** (**VERIFIED-STATIC**, `handleResize@313584`)",
                       "screen-reader accessibility mode",
                       "Terminal input tokenizer, terminal reply parsers and print-mode output",
                       "chunk-t3baq28d.js@3672", "chunk-v44rfc3q.js@187551",
                       "chunk-fzzrkchm.js@404377", "tengu_jazzy_puddle",
                       "Error: No messages returned from query",
                       "Headless session closure `VL`", "76 distinct subtype strings", "`@649306` and is not a dispatched subtype",
                       "handleSetCwdControlRequest",
                       "`VL` handlers: interrupt, rewind, fork, file and MCP calls",
                       "More `VL` handlers (same pass)",
                       "Headless turn runner `kf`, result router `Zp` and frame intake `Tp`",
                       "`tengu_sdk_result`", "chunk-fzzrkchm.js@190435",
                       "Held-turn machine `jf`", "ccr_keepalive_after_stop",
                       "Pre-arm interrupt latch `Ff`",
                       "`VL` remote-UI surface: the `ui_*` requests",
                       "`VL` settings, feedback, side-question, remote-control and the end of the dispatch loop",
                       "cli_control_request_handled", "main-agent `poll-event` command",
                       "`VL` MCP, plugin, skill and OAuth requests",
                       "OAuth state mismatch",
                       "`VL` dialog, Chrome, SDK-MCP, review, rating, device-hook and remote-tool requests",
                       "File-staging and read-state requests", "hook_forwarding_disabled",
                       "`claim_session`: spare-process claim logic",
                       "env_key_not_claimable", "project_settings_not_claimable",
                       "`jf` held-turn machine, remaining methods",
                       "served_adopted_at_boot", "cli_parked_answer_wait_over",
                       "`jf` answer handling and inherited ask", "cli_strict_answer_dropped",
                       "late_answer_discarded",
                       "Orphaned-answer handler `Rw`", "handled_during_read",
                       "Working-directory move `Tgt` and the `set_cwd` request",
                       "needs_trust", "chunk-zw045t1m.js@5536",
                       "Directory-move helpers: target resolver `s6n`", "chunk-j144endc.js@37781",
                       "`remote_control` inline bridge callbacks inside `VL`", "bridge:onInboundMessage: dropped before attachment materialization",
                       "MCP set applier `sh` and single-server applier `Zc`", "tengu_mcp_reconcile",
                       "Bridge module `chunk-2kr6zq6e.js`: persistence sync", "caught_up_after_retry",
                       "`initReplBridge` (`yi`): gates, reattach, titles and bridge creation", "work_secret_no_target",
                       "Bridge factory `a5o`: connect phase", "bridge_connect_reattach_gone",
                       "`a5o`: dead ends, presence events, owner-change settle and worker state", "client_events_lost_at_dead_end",
                       "`a5o`: branch metadata, proactive token refresh, connect handler and close handling", "bridge_repl_v2_proactive_refresh_unreachable",
                       "`a5o`: transport rebuild, re-mint loop, close-code recovery table", "bridge_repl_v2_remint_loop_recovered",
                       "`a5o`: backfill, teardown, the bridge object and the module", "bridge_repl_transcript_backfill_dropped"):
            self.assertIn(needle, text)
        self.assertNotIn("The body of the daemon supervisor loop (`Mt` in `chunk-39q3j8sd.js`): lock acquisition order", text)

    def test_internal_contract_supplement_is_present(self):
        text = (REPORTS / "04-internal-contracts.md").read_text(encoding="utf-8")
        self.assertIn("## 10. Daemon worker and PTY contracts", text)
        self.assertIn("## 11. Renderer and input scheduler contracts", text)
        self.assertIn("chunk-75p1g95y.js@10757", text)

    def test_superseded_open_question_wording_is_absent(self):
        for name in ("03-runtime-experiments.md", "06-verification-matrix.md"):
            text = (REPORTS / name).read_text(encoding="utf-8")
            for stale in (
                "Daemon lifecycle probe: help and status only",
                "All runs used `claude -p`",
                "Not tested: a response that has real text when it is cut",
                "The 180 s first-party byte default is still unwaited",
                "No contradiction in 150 manifest runs",
                "Blocked by PTY tooling on native Windows",
            ):
                self.assertNotIn(stale, text, f"{name}: {stale}")


if __name__ == "__main__":
    unittest.main()
