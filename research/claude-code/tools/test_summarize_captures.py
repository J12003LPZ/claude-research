import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from summarize_captures import parse_sse, sanitize_run, summarize_debug, summarize_request, summarize_response, summarize_stream


class SanitizeRunTests(unittest.TestCase):
    def test_masks_stdin_file_and_nested_fault_metadata(self):
        run = {
            "cwd": r"C:\Users\sergi\cc-rea-lab\proj-hooks",
            "argv": [r"C:\Users\sergi\Desktop\claude-rea\lab\raw\E31\debug.log"],
            "prompt": "PRIVATE-PROMPT-TOKEN-7319",
            "exe_sha256": "76de74f7694a5bdc03378a5f837c9e132827bf004c98c276bc4e9094ff06769a",
            "stdin_file": r"C:\Users\sergi\cc-rea-lab\compact-flood.txt",
            "fault": {
                "body": {"message": r"C:\Users\sergi\private\prompt.txt"},
                "headers": {"Authorization": "PRIVATE-FAULT-MARKER-9348"},
                "mode": "PRIVATE-MODE-MARKER-9348",
            },
            "stdin_script": [{"t_s": 0, "type": "PRIVATE-TYPE-MARKER-9348", "send": {"message": "PRIVATE-STDIN-MARKER-9348"}}],
            "control_events": [{
                "t_s": 1,
                "subtype": "can_use_tool",
                "auto_response": {"behavior": "deny", "message": "PRIVATE-CONTROL-MARKER-9348"},
            }],
        }

        sanitized = sanitize_run(run)

        self.assertNotIn("sergi", str(sanitized))
        self.assertNotIn("PRIVATE-PROMPT-TOKEN-7319", str(sanitized))
        self.assertNotIn("PRIVATE-FAULT-MARKER-9348", str(sanitized))
        self.assertNotIn("PRIVATE-MODE-MARKER-9348", str(sanitized))
        self.assertNotIn("PRIVATE-TYPE-MARKER-9348", str(sanitized))
        self.assertNotIn("PRIVATE-STDIN-MARKER-9348", str(sanitized))
        self.assertNotIn("PRIVATE-CONTROL-MARKER-9348", str(sanitized))
        self.assertEqual(sanitized["exe_sha256"], "76de74f7694a5bdc03378a5f837c9e132827bf004c98c276bc4e9094ff06769a")
        self.assertEqual(set(sanitized["prompt"]), {"len", "sha256"})
        self.assertEqual(sanitized["prompt"]["len"], len("PRIVATE-PROMPT-TOKEN-7319"))
        self.assertEqual(sanitized["stdin_file"], r"C:\Users\<user>\cc-rea-lab\compact-flood.txt")
        self.assertEqual(
            sanitized["fault"]["body"],
            {"type": "object", "keys": ["message"]},
        )
        self.assertEqual(
            sanitized["fault"]["headers"],
            {"type": "object", "keys": ["Authorization"]},
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

    def test_debug_summary_keeps_late_breaker_signal(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "debug.log"
            lines = [
                f"2026-10-14T00:00:{i:02d}Z [DEBUG] compact refill {i}"
                for i in range(80)
            ]
            lines.append(
                "2026-10-14T00:01:21Z [ERROR] failure breaker open SENSITIVE-LAB-MARKER-9348"
            )
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")

            summary = summarize_debug(str(path))

        self.assertTrue(any("failure breaker" in signal for signal in summary["signals"]))
        self.assertNotIn("SENSITIVE-LAB-MARKER-9348", str(summary))

    def test_debug_prefix_does_not_publish_arbitrary_log_word(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "debug.log"
            path.write_text(
                "2026-10-14T00:00:00Z [DEBUG] PRIVATE-TOKEN-9348 compact probe\n",
                encoding="utf-8",
            )

            summary = summarize_debug(str(path))

        self.assertNotIn("PRIVATE-TOKEN-9348", str(summary))

    def test_debug_summary_labels_breaker_event_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "debug.log"
            path.write_text(
                "2026-10-14T00:00:00Z [ERROR] failure_breaker_open\n"
                "2026-10-14T00:00:01Z [ERROR] tengu_auto_compact_circuit_breaker\n",
                encoding="utf-8",
            )

            summary = summarize_debug(str(path))

        self.assertTrue(any("failure_breaker_open" in signal for signal in summary["signals"]))
        self.assertTrue(any("tengu_auto_compact_circuit_breaker" in signal for signal in summary["signals"]))

    def test_debug_summary_extracts_reactive_compact_numbers_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "debug.log"
            path.write_text(
                "2026-10-14T00:00:01Z [INFO] Reactive compact: attempt 2 hit prompt-too-long "
                "(gap=50000 → gap_guided step 1), next preserves 5/7 SENSITIVE-LAB-MARKER-9348\n"
                "2026-10-14T00:00:02Z [INFO] Reactive compact: round ladder exhausted, last resort "
                "(keeping 3 trailing messages, head truncations so far: 1)\n"
                "2026-10-14T00:00:03Z [INFO] Reactive compact: last-resort request still too long "
                "after 1 head truncations, giving up\n"
                "2026-10-14T00:00:04Z [INFO] Reactive compact: no assistant messages in summarize set, bailing\n",
                encoding="utf-8",
            )

            summary = summarize_debug(str(path))

        self.assertEqual(
            summary["reactive_compact"],
            [
                {"t": "2026-10-14T00:00:01Z", "event": "attempt_prompt_too_long", "attempt": 2,
                 "gap": 50000, "step": 1, "preserves": 5, "of": 7},
                {"t": "2026-10-14T00:00:02Z", "event": "last_resort", "keeping": 3, "head_truncations": 1},
                {"t": "2026-10-14T00:00:03Z", "event": "gave_up", "head_truncations": 1},
                {"t": "2026-10-14T00:00:04Z", "event": "bail_no_assistant_messages"},
            ],
        )
        self.assertNotIn("SENSITIVE-LAB-MARKER-9348", str(summary))

    def test_debug_summary_extracts_watchdog_numbers_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "debug.log"
            path.write_text(
                "2026-10-14T00:00:01Z [WARN] [Stall] stream_idle_partial lastChunkAgeMs=14999 "
                "bytesTotal=247 idleDeadlineMs=1800000 SENSITIVE-LAB-MARKER-9348\n"
                "2026-10-14T00:00:02Z [WARN] Streaming idle warning: no chunks received for 150s\n"
                "2026-10-14T00:00:03Z [ERROR] Streaming idle timeout: no chunks received for 300s, aborting stream\n"
                "2026-10-14T00:00:04Z [ERROR] [byte-watchdog] firing: idle=10000ms\n"
                "2026-10-14T00:00:05Z [ERROR] Error streaming, falling back to non-streaming mode: "
                "Stream idle timeout SENSITIVE-LAB-MARKER-9348\n",
                encoding="utf-8",
            )

            summary = summarize_debug(str(path))

        self.assertEqual(
            summary["watchdog"],
            [
                {"t": "2026-10-14T00:00:01Z", "event": "stall_partial", "last_chunk_age_ms": 14999,
                 "bytes_total": 247, "idle_deadline_ms": 1800000},
                {"t": "2026-10-14T00:00:02Z", "event": "idle_warning", "seconds": 150},
                {"t": "2026-10-14T00:00:03Z", "event": "idle_timeout", "seconds": 300},
                {"t": "2026-10-14T00:00:04Z", "event": "byte_watchdog_fired", "idle_ms": 10000},
                {"t": "2026-10-14T00:00:05Z", "event": "fallback_non_streaming"},
            ],
        )
        self.assertNotIn("SENSITIVE-LAB-MARKER-9348", str(summary))

    def test_debug_summary_extracts_autocompact_events_without_free_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "debug.log"
            path.write_text(
                "2026-10-14T00:00:01Z [DEBUG] autocompact: tokens=[REDACTED] level=blocked effectiveWindow=980000\n"
                "2026-10-14T00:00:02Z [DEBUG] autocompact: routing through reactive (thresholdSource=model-default)\n"
                "2026-10-14T00:00:03Z [DEBUG] PreCompact:auto [python hooklog.py PreCompact log] completed with status 0\n"
                "2026-10-14T00:00:04Z [INFO] Reactive compact: summarization returned API error: "
                "API Error: 400 SENSITIVE-LAB-MARKER-9348\n"
                "2026-10-14T00:00:05Z [WARN] autocompact: circuit breaker tripped SENSITIVE-LAB-MARKER-9348\n",
                encoding="utf-8",
            )

            summary = summarize_debug(str(path))

        self.assertEqual(
            summary["autocompact"],
            [
                {"t": "2026-10-14T00:00:01Z", "event": "level", "level": "blocked", "effective_window": 980000},
                {"t": "2026-10-14T00:00:02Z", "event": "routed_reactive", "threshold_source": "model-default"},
                {"t": "2026-10-14T00:00:03Z", "event": "pre_compact_hook_ran"},
                {"t": "2026-10-14T00:00:04Z", "event": "summary_api_error"},
                {"t": "2026-10-14T00:00:05Z", "event": "circuit_breaker_tripped"},
            ],
        )
        self.assertNotIn("SENSITIVE-LAB-MARKER-9348", str(summary))

    def test_stream_summary_keeps_task_status_fields_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "stdout.jsonl"
            frames = [
                {"type": "system", "subtype": "task_started", "task_type": "local_agent",
                 "description": "SENSITIVE-LAB-MARKER-9348"},
                {"type": "system", "subtype": "task_updated",
                 "patch": {"status": "killed", "end_time": 1, "note": "SENSITIVE-LAB-MARKER-9348"}},
                {"type": "system", "subtype": "task_notification", "status": "stopped",
                 "summary": "SENSITIVE-LAB-MARKER-9348"},
                {"type": "system", "subtype": "background_tasks_changed",
                 "tasks": [{"id": "a", "description": "SENSITIVE-LAB-MARKER-9348"}]},
            ]
            path.write_text("\n".join(json.dumps(f) for f in frames) + "\n", encoding="utf-8")

            events = summarize_stream(str(path))["events"]

        task = [{k: e[k] for k in e if k in ("subtype", "task_type", "status", "patch_status", "task_count")}
                for e in events]
        self.assertEqual(task, [
            {"subtype": "task_started", "task_type": "local_agent"},
            {"subtype": "task_updated", "patch_status": "killed"},
            {"subtype": "task_notification", "status": "stopped"},
            {"subtype": "background_tasks_changed", "task_count": 1},
        ])
        self.assertNotIn("SENSITIVE-LAB-MARKER-9348", str(events))

    def test_stream_summary_keeps_every_result_frame(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "stdout.jsonl"
            frames = [
                {"type": "result", "subtype": "success", "is_error": True, "terminal_reason": "blocking_limit",
                 "api_error_status": None, "num_turns": 1, "result": "SENSITIVE-LAB-MARKER-9348"},
                {"type": "result", "subtype": "success", "is_error": True, "terminal_reason": "api_error",
                 "api_error_status": 400, "num_turns": 1, "result": "x"},
            ]
            path.write_text("\n".join(json.dumps(f) for f in frames) + "\n", encoding="utf-8")

            summary = summarize_stream(str(path))

        self.assertEqual(
            summary["results"],
            [
                {"terminal_reason": "blocking_limit", "api_error_status": None, "is_error": True, "num_turns": 1},
                {"terminal_reason": "api_error", "api_error_status": 400, "is_error": True, "num_turns": 1},
            ],
        )
        self.assertNotIn("SENSITIVE-LAB-MARKER-9348", str(summary["results"]))

    def test_bare_account_name_is_masked_in_heads_and_digests(self):
        import getpass

        from summarize_captures import digest, mask

        user = getpass.getuser()
        masked = mask(f"**User identity**: `{user}`. The `$USER/...` pattern")
        self.assertNotIn(user, masked)
        self.assertIn("<user>", masked)
        self.assertNotIn(user, digest(f"\n\n## Session Context\n\n- **User identity**: `{user}`")["head"])
        self.assertEqual(mask(f"x{user}y"), f"x{user}y")  # not a whole word

    def test_request_model_ids_are_kept_but_arbitrary_model_strings_are_digested(self):
        def model_of(value):
            req = {"seq": "1", "t_ms": 0, "method": "POST", "url": "/v1/messages", "body_bytes": 1,
                   "headers": {}, "body": {"model": value}}
            return summarize_request(req)["body"]["model"]

        self.assertEqual(model_of("claude-sonnet-5"), "claude-sonnet-5")
        self.assertEqual(model_of("claude-sonnet-5[1m]"), "claude-sonnet-5[1m]")
        self.assertEqual(model_of("claude-haiku-5-5"), "claude-haiku-5-5")
        leaked = model_of("my-private-model-SENSITIVE-9348")
        self.assertNotIn("SENSITIVE-9348", str(leaked))
        self.assertEqual(set(leaked), {"len", "sha256"})

    def test_schema_keys_keep_camel_case_but_digest_secret_like_keys(self):
        from summarize_captures import structural_shape

        shape = structural_shape({
            "dangerouslyDisableSandbox": 1,
            "run_in_background": 2,
            "sk-ant-api03-SENSITIVE-9348": 3,
            "token_9348": 4,
        })

        self.assertIn("dangerouslyDisableSandbox", shape["keys"])
        self.assertIn("run_in_background", shape["keys"])
        self.assertNotIn("sk-ant-api03-SENSITIVE-9348", str(shape))
        self.assertNotIn("token_9348", str(shape))
        self.assertEqual(sum(k.startswith("<key:") for k in shape["keys"]), 2)

    def test_request_summary_does_not_publish_container_or_mcp_values(self):
        marker = "SENSITIVE-LAB-MARKER-9348"
        req = {
            "seq": "0001",
            "t_ms": 0,
            "method": "POST",
            "url": "/v1/messages",
            "body_bytes": 123,
            "headers": {},
            "body": {
                "container": {"id": marker, "url": "https://private.example"},
                "mcp_servers": [{"name": marker, "headers": {"Authorization": "Bearer secret"}}],
                "context_management": {"PRIVATE-REQUEST-MARKER-9348": marker},
                "tool_choice": {"value": marker},
            },
        }

        summary = summarize_request(req)["body"]

        self.assertNotIn(marker, str(summary))
        self.assertEqual(summary["container"], {"type": "object", "keys": ["id", "url"]})
        self.assertEqual(
            summary["mcp_servers"],
            {"count": 1, "items": [{"type": "object", "keys": ["headers", "name"]}]},
        )

    def test_response_error_message_is_digest_only(self):
        marker = "SENSITIVE-LAB-MARKER-9348"
        raw = (
            '{"error":{"type":"invalid_request_error","message":"'
            + marker
            + '"}}'
        ).encode("utf-8")

        summary = summarize_response(
            {"status": 400, "headers": {"content-type": "application/json"}},
            raw,
            [],
        )

        self.assertNotIn(marker, str(summary))
        self.assertEqual(summary["error"]["type"], "invalid_request_error")
        self.assertEqual(summary["error"]["message"]["len"], len(marker))
        self.assertNotIn("head", summary["error"]["message"])

    def test_non_json_response_body_is_digest_only(self):
        marker = "SENSITIVE-LAB-MARKER-9348"
        summary = summarize_response(
            {"status": 502, "headers": {"content-type": "text/plain"}},
            marker.encode("utf-8"),
            [],
        )

        self.assertNotIn(marker, str(summary))
        self.assertEqual(summary["body_digest"]["len"], len(marker))
        self.assertNotIn("body_head", summary)

    def test_sse_error_message_is_digest_only(self):
        marker = "PRIVATE-SSE-ERROR-MARKER-9348"
        raw = (
            'event: error\n'
            'data: {"type":"error","error":{"type":"api_error","message":"'
            + marker
            + '"}}\n\n'
        )

        summary = summarize_response(
            {"status": 529, "headers": {"content-type": "text/event-stream"}},
            raw.encode("utf-8"),
            [],
        )

        self.assertNotIn(marker, str(summary))
        self.assertEqual(summary["sse_error"]["message"]["len"], len(marker))

    def test_incomplete_sse_message_start_does_not_crash(self):
        raw = 'event: message_start\ndata: {"type":"message_start"}\n\n'

        summary = summarize_response(
            {"status": 200, "headers": {"content-type": "text/event-stream"}},
            raw.encode("utf-8"),
            [],
        )

        self.assertEqual(summary["sse_event_runs"], [["message_start", 1]])
        self.assertNotIn("message_start", summary)

    def test_parse_sse_accepts_multiple_crlf_events(self):
        raw = (
            'event: message_start\r\n'
            'data: {"type":"message_start"}\r\n\r\n'
            'event: message_delta\r\n'
            'data: {"type":"message_delta"}\r\n\r\n'
        )

        self.assertEqual(
            parse_sse(raw),
            [
                ("message_start", {"type": "message_start"}),
                ("message_delta", {"type": "message_delta"}),
            ],
        )

    def test_parse_sse_accepts_mixed_line_endings(self):
        raw = (
            'event: message_start\n'
            'data: {"type":"message_start"}\n\r\n'
            'event: message_delta\r\n'
            'data: {"type":"message_delta"}\r\n\r\n'
        )

        self.assertEqual(
            parse_sse(raw),
            [
                ("message_start", {"type": "message_start"}),
                ("message_delta", {"type": "message_delta"}),
            ],
        )


if __name__ == "__main__":
    unittest.main()
