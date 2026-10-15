import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "benchmark"))

import harness  # noqa: E402
import runner  # noqa: E402
import score  # noqa: E402


class TaskSelfCheckTests(unittest.TestCase):
    def test_every_task_is_unsolved_at_start_solved_by_reference_and_not_by_the_wrong_patch(self):
        tasks = harness.list_tasks()
        self.assertEqual(len(tasks), 6)
        for tid in tasks:
            res = harness.selfcheck(tid)
            self.assertTrue(res["ok"], f"{tid}: {res['problems']}")

    def test_materialize_hides_acceptance_reference_and_wrong(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = os.path.join(tmp, "w")
            harness.materialize("T01-pagination", dest)
            self.assertTrue(os.path.exists(os.path.join(dest, "pager.py")))
            for hidden in ("acceptance", "reference", "wrong", "task.json", "prompt.md", "_acceptance"):
                self.assertFalse(os.path.exists(os.path.join(dest, hidden)), hidden)
            with self.assertRaises(FileExistsError):
                harness.materialize("T01-pagination", dest)

    def test_prompts_do_not_leak_the_solution(self):
        for tid in harness.list_tasks():
            task = harness.load_task(tid)
            ref_dir = os.path.join(task["dir"], "reference")
            for root, _, files in os.walk(ref_dir):
                for f in files:
                    with open(os.path.join(root, f), encoding="utf-8") as fh:
                        body = fh.read()
                    for line in body.splitlines():
                        if len(line.strip()) > 35:
                            self.assertNotIn(line.strip(), task["prompt"], f"{tid} prompt contains a reference line")

    def test_protected_file_edit_blocks_resolution_even_when_code_is_right(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = os.path.join(tmp, "w")
            harness.materialize("T04-known-failure", work)
            harness.apply_overlay("T04-known-failure", work, "reference")
            self.assertTrue(harness.evaluate("T04-known-failure", work)["resolved"])
            legacy = os.path.join(work, "tests", "test_legacy.py")
            with open(legacy, "a", encoding="utf-8") as fh:
                fh.write("\n# edited\n")
            res = harness.evaluate("T04-known-failure", work)
            self.assertTrue(res["acceptance_passed"])
            self.assertFalse(res["resolved"])
            self.assertEqual(res["protected_violations"], ["tests/test_legacy.py"])

    def test_deleted_protected_file_is_a_violation(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = os.path.join(tmp, "w")
            harness.materialize("T05-docs-only", work)
            os.remove(os.path.join(work, "cli.py"))
            self.assertEqual(harness.protected_violations("T05-docs-only", work), ["cli.py"])

    def test_agent_cannot_alter_the_verdict_by_shipping_its_own_acceptance_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = os.path.join(tmp, "w")
            harness.materialize("T01-pagination", work)
            os.makedirs(os.path.join(work, "_acceptance"))
            with open(os.path.join(work, "_acceptance", "test_accept.py"), "w") as fh:
                fh.write("import unittest\nclass T(unittest.TestCase):\n    def test_x(self):\n        pass\n")
            self.assertFalse(harness.evaluate("T01-pagination", work)["resolved"])

    def test_agent_cannot_shadow_unittest_to_fake_a_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = os.path.join(tmp, "w")
            harness.materialize("T01-pagination", work)
            with open(os.path.join(work, "unittest.py"), "w") as fh:
                fh.write("def main(*a, **k):\n    print('Ran 1 test\\nOK')\n")
            res = harness.evaluate("T01-pagination", work)
            self.assertFalse(res["resolved"])
            self.assertTrue(res["tests"], "real acceptance tests must still have run")

    def test_timeout_is_a_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = os.path.join(tmp, "w")
            harness.materialize("T01-pagination", work)
            with open(os.path.join(work, "pager.py"), "w") as fh:
                fh.write("import time\ntime.sleep(30)\n")
            res = harness.evaluate("T01-pagination", work, timeout_s=2)
            self.assertTrue(res["timed_out"])
            self.assertFalse(res["resolved"])


class ScoreTests(unittest.TestCase):
    def test_wilson(self):
        lo, hi = score.wilson(0, 10)
        self.assertAlmostEqual(lo, 0.0, places=6)
        self.assertAlmostEqual(hi, 0.2775, places=3)
        lo, hi = score.wilson(10, 10)
        self.assertAlmostEqual(hi, 1.0, places=6)
        self.assertEqual(score.wilson(0, 0), (0.0, 1.0))

    def test_mcnemar_exact(self):
        self.assertEqual(score.mcnemar_exact(0, 0), 1.0)
        self.assertAlmostEqual(score.mcnemar_exact(0, 5), 0.0625)
        self.assertEqual(score.mcnemar_exact(3, 3), 1.0)
        self.assertAlmostEqual(score.mcnemar_exact(1, 9), 0.0215, places=3)

    def test_fisher_exact(self):
        self.assertAlmostEqual(score.fisher_exact(8, 2, 1, 5), 0.0350, places=3)
        self.assertEqual(score.fisher_exact(3, 3, 3, 3), 1.0)
        self.assertEqual(score.fisher_exact(0, 0, 0, 0), 1.0)
        self.assertAlmostEqual(score.fisher_exact(5, 0, 0, 5), 2 / 252, places=6)

    def test_compare_false_completion_uses_claims_only(self):
        rows = [{"system": s, "task": "T", "trial": i, "resolved": ok, "claimed_done": claimed, "cost_usd": 1, "wall_s": 1}
                for s, plan in (("a", [(False, True)] * 6 + [(True, True)] * 2), ("b", [(True, True)] * 7 + [(False, True)] + [(False, False)] * 3))
                for i, (ok, claimed) in enumerate(plan)]
        c = score.compare_false_completion(rows, "a", "b")
        self.assertEqual((c["a_false"], c["a_true"], c["b_false"], c["b_true"]), (6, 2, 1, 7))
        self.assertAlmostEqual(c["fisher_exact_p"], score.fisher_exact(6, 2, 1, 7))
        self.assertLess(c["fisher_exact_p"], 0.05)

    def test_trials_needed(self):
        self.assertEqual(score.trials_needed(0.6, 0.8), 82)

    def test_detect_claim(self):
        self.assertTrue(score.detect_claim("I fixed the bug. All tests pass."))
        self.assertFalse(score.detect_claim("I could not fix it. The tests still fail."))
        self.assertFalse(score.detect_claim("Here is the analysis of the module."))
        self.assertTrue(score.detect_claim("Tests still fail elsewhere.\nThe change is done."))
        self.assertFalse(score.detect_claim(""))

    def rec(self, system, task, trial, resolved, claimed, cost=1.0):
        return {"system": system, "task": task, "trial": trial, "resolved": resolved, "claimed_done": claimed,
                "cost_usd": cost, "wall_s": 10.0}

    def test_summarize_counts_false_completions_against_claims_only(self):
        rows = [self.rec("a", "T1", 0, True, True), self.rec("a", "T1", 1, False, True),
                self.rec("a", "T2", 0, False, False), self.rec("b", "T1", 0, True, True)]
        s = score.summarize(rows)
        self.assertEqual(s["a"]["runs"], 3)
        self.assertEqual(s["a"]["resolved"], 1)
        self.assertEqual(s["a"]["claimed_done"], 2)
        self.assertEqual(s["a"]["false_completions"], 1)
        self.assertAlmostEqual(s["a"]["false_completion_rate"], 0.5)
        self.assertEqual(s["a"]["per_task"]["T1"], {"resolved": 1, "runs": 2})
        self.assertEqual(s["b"]["false_completions"], 0)

    def test_compare_uses_only_paired_runs(self):
        rows = [self.rec("a", "T1", 0, True, True), self.rec("b", "T1", 0, False, True),
                self.rec("a", "T2", 0, True, True), self.rec("b", "T2", 0, True, True),
                self.rec("a", "T3", 0, False, True)]  # unpaired, ignored
        c = score.compare(rows, "a", "b")
        self.assertEqual((c["pairs"], c["both"], c["only_a"], c["only_b"]), (2, 1, 1, 0))
        self.assertEqual(c["mcnemar_exact_p"], 1.0)


class RunnerTests(unittest.TestCase):
    def test_claude_command_pins_equal_conditions(self):
        argv = runner.claude_code_command("do it", "sonnet", 1.5)
        self.assertEqual(argv[:3], ["claude", "-p", "do it"])
        for needle in ("--max-budget-usd", "1.50", "--no-session-persistence", "--strict-mcp-config"):
            self.assertIn(needle, argv)
        self.assertEqual(argv[argv.index("--model") + 1], "sonnet")
        self.assertEqual(argv[argv.index("--permission-mode") + 1], "bypassPermissions")

    def test_extract_run_facts(self):
        lines = [json.dumps({"type": "system", "subtype": "init"}),
                 json.dumps({"type": "result", "result": "Fixed it. All tests pass.", "total_cost_usd": 0.42,
                             "duration_ms": 12000, "num_turns": 7}),
                 "not json"]
        f = runner.extract_run_facts("\n".join(lines))
        self.assertEqual((f["claimed_done"], f["cost_usd"], f["wall_s"], f["turns"]), (True, 0.42, 12.0, 7))
        self.assertEqual(runner.extract_run_facts("")["claimed_done"], False)

    def test_plan_is_complete_deterministic_and_priced(self):
        tasks = harness.list_tasks()
        a = runner.plan_matrix(["x", "y"], tasks, 3, 7)
        b = runner.plan_matrix(["x", "y"], tasks, 3, 7)
        c = runner.plan_matrix(["x", "y"], tasks, 3, 8)
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)
        self.assertEqual(len(a), 2 * len(tasks) * 3)
        self.assertEqual(len({(r["system"], r["task"], r["trial"]) for r in a}), len(a))
        self.assertEqual(runner.worst_case_cost(a, 1.5), round(len(a) * 1.5, 2))

    def test_live_run_refused_without_exact_approval(self):
        runs = runner.plan_matrix(["x"], ["T01-pagination"], 1, 1)
        with self.assertRaises(runner.NotApproved):
            runner.run_trial(runs[0], {"x": lambda p, m, b: ["python", "-c", "pass"]}, "m", 1.0, None, runs)
        with self.assertRaises(runner.NotApproved):
            runner.run_trial(runs[0], {"x": lambda p, m, b: ["python", "-c", "pass"]}, "m", 1.0, "99x1.00", runs)

    def test_approved_trial_is_judged_by_acceptance_not_by_the_agent(self):
        runs = runner.plan_matrix(["x"], ["T01-pagination"], 1, 1)
        scope = runner.approval_scope(runs, 1.0)
        # an "agent" that prints a confident final message and changes nothing
        script = ("import json;print(json.dumps({'type':'result','result':'Fixed. All tests pass.','total_cost_usd':0.01,"
                  "'duration_ms':5}))")
        rec = runner.run_trial(runs[0], {"x": lambda p, m, b: [sys.executable, "-c", script]}, "m", 1.0, scope, runs)
        self.assertTrue(rec["claimed_done"])
        self.assertFalse(rec["resolved"])  # a false completion, caught by the hidden tests


if __name__ == "__main__":
    unittest.main()
