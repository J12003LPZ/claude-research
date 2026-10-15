import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "controller"))

import davinci_controller as dc  # noqa: E402
from davinci_controller import (Controller, ControllerError, Criterion, Outcome, Phase, RepeatedApproach,  # noqa: E402
                                BudgetExhausted, TaskState)


def ready(criteria=None, baseline=(), digest="d0", phase=Phase.IMPLEMENT):
    s = TaskState(task="fix add()")
    c = Controller(s)
    c.set_criteria(criteria or [Criterion("C1", "add(2,3)==5 and negatives work"), Criterion("C2", "no other test regresses")])
    c.record_baseline(list(baseline), digest)
    s.phase = phase
    return c


class TransitionTests(unittest.TestCase):
    def test_legal_path_and_illegal_jump(self):
        s = TaskState(task="t")
        c = Controller(s)
        c.move(Phase.EXPLORE)
        with self.assertRaises(ControllerError):
            c.move(Phase.IMPLEMENT)  # cannot skip planning
        c.move(Phase.PLAN)
        with self.assertRaises(ControllerError):
            c.move(Phase.IMPLEMENT)  # no criteria yet
        c.set_criteria([Criterion("C1", "x")])
        c.move(Phase.IMPLEMENT)
        self.assertEqual(s.phase, Phase.IMPLEMENT)

    def test_plan_approval_gate(self):
        s = TaskState(task="t", plan_approval_required=True)
        c = Controller(s)
        c.set_criteria([Criterion("C1", "x")])
        s.phase = Phase.PLAN
        with self.assertRaises(ControllerError):
            c.move(Phase.IMPLEMENT)
        s.plan_approved = True
        c.move(Phase.IMPLEMENT)

    def test_review_requires_fresh_passing_run(self):
        c = ready(phase=Phase.VERIFY)
        with self.assertRaises(ControllerError):
            c.move(Phase.REVIEW)
        c.record_verification("python run_tests.py", True, [], ["C1", "C2"], "d0")
        c.move(Phase.REVIEW)

    def test_duplicate_or_missing_criteria_rejected(self):
        c = Controller(TaskState(task="t"))
        with self.assertRaises(ControllerError):
            c.set_criteria([])
        with self.assertRaises(ControllerError):
            c.set_criteria([Criterion("C1", "a"), Criterion("C1", "b")])

    def test_edits_only_in_implement_or_recover(self):
        c = ready(phase=Phase.VERIFY)
        with self.assertRaises(ControllerError):
            c.record_edit(["a.py"], "d1")


class VerificationTests(unittest.TestCase):
    def test_verified_needs_fresh_evidence_for_every_criterion(self):
        c = ready()
        self.assertEqual(c.report().outcome, Outcome.UNVERIFIED)  # nothing run yet
        c.record_verification("t1", True, [], ["C1"], "d0")
        r = c.report()
        self.assertEqual((r.outcome, r.unmet), (Outcome.UNVERIFIED, ["C2"]))
        c.record_verification("t2", True, [], ["C2"], "d0")
        self.assertEqual(c.report().outcome, Outcome.VERIFIED)
        self.assertEqual(c.may_claim("verified"), (True, ""))

    def test_edit_after_pass_makes_evidence_stale(self):
        c = ready()
        c.record_verification("t", True, [], ["C1", "C2"], "d0")
        self.assertEqual(c.report().outcome, Outcome.VERIFIED)
        c.record_edit(["src/app.py"], "d1")
        r = c.report()
        self.assertEqual(r.outcome, Outcome.UNVERIFIED)
        self.assertEqual(sorted(r.stale), ["C1", "C2"])
        ok, why = c.may_claim("verified")
        self.assertFalse(ok)
        self.assertIn("stale", why)

    def test_new_failure_is_failed_and_blocks_claims(self):
        c = ready(baseline=["test_old"])
        c.record_verification("t", False, ["test_old", "test_new"], ["C1", "C2"], "d0")
        r = c.report()
        self.assertEqual(r.outcome, Outcome.FAILED)
        self.assertEqual(r.new_failures, ["test_new"])
        self.assertEqual(r.preexisting_failures, ["test_old"])
        self.assertFalse(c.may_claim("tests_pass")[0])

    def test_preexisting_failure_alone_does_not_block_verified(self):
        c = ready(baseline=["test_old"])
        c.record_verification("full suite", False, ["test_old"], ["C1", "C2"], "d0")
        r = c.report()
        self.assertEqual(r.outcome, Outcome.VERIFIED)
        self.assertEqual(r.preexisting_failures, ["test_old"])
        self.assertTrue(any("preexisting" in n for n in r.notes))

    def test_missing_baseline_treats_failures_as_new(self):
        s = TaskState(task="t")
        c = Controller(s)
        c.set_criteria([Criterion("C1", "x")])
        s.tree_digest = "d0"
        c.record_verification("t", False, ["test_a"], ["C1"], "d0")
        r = c.report()
        self.assertEqual(r.outcome, Outcome.FAILED)
        self.assertTrue(any("baseline_missing" in n for n in r.notes))

    def test_run_failed_without_test_ids_is_a_failure(self):
        c = ready()
        c.record_verification("python run_tests.py", False, [], ["C1", "C2"], "d0")
        self.assertEqual(c.report().outcome, Outcome.FAILED)

    def test_last_run_of_a_command_wins_at_the_same_digest(self):
        c = ready()
        c.record_verification("t", False, ["test_x"], ["C1", "C2"], "d0")
        c.record_verification("t", True, [], ["C1", "C2"], "d0")  # flaky rerun at the same tree
        self.assertEqual(c.report().outcome, Outcome.VERIFIED)

    def test_evidence_validation(self):
        c = ready()
        with self.assertRaises(ControllerError):
            c.record_verification("t", True, [], ["C9"], "d0")
        with self.assertRaises(ControllerError):
            c.record_verification("t", True, ["test_x"], ["C1"], "d0")

    def test_blocked_outranks_everything(self):
        c = ready()
        c.record_verification("t", True, [], ["C1", "C2"], "d0")
        c.block("registry unreachable")
        r = c.report()
        self.assertEqual(r.outcome, Outcome.BLOCKED)
        self.assertIn("registry unreachable", r.notes)

    def test_review_criterion_needs_approved_review_at_current_tree(self):
        c = ready([Criterion("C1", "behavior", "executable"), Criterion("R1", "reviewer approves", "review")])
        c.record_verification("t", True, [], ["C1"], "d0")
        self.assertEqual(c.report().unmet, ["R1"])
        c.record_review(["off by one on empty list"])
        self.assertEqual(c.report().unmet, ["R1"])  # blocking finding
        c.record_review([])
        self.assertEqual(c.report().outcome, Outcome.VERIFIED)
        c.record_edit(["x.py"], "d1")
        self.assertIn("R1", c.report().unmet)  # review is stale after an edit


class NonExecutableChangeTests(unittest.TestCase):
    def test_classify_change(self):
        self.assertEqual(dc.classify_change(["README.md", "docs/a.rst"]), "non_executable")
        self.assertEqual(dc.classify_change(["README.md", "src/app.py"]), "executable")
        self.assertEqual(dc.classify_change(["Makefile"]), "executable")  # unknown stays conservative
        self.assertEqual(dc.classify_change([]), "none")

    def test_docs_only_task_verifies_without_running_tests(self):
        s = TaskState(task="document the --dry-run flag")
        c = Controller(s)
        c.set_criteria([Criterion("D1", "README lists --dry-run with an example", "static")])
        s.tree_digest = "d0"
        c.record_baseline([], "d0")
        c.record_verification("inspect README.md diff", True, [], ["D1"], "d0", kind="inspection")
        r = c.report()
        self.assertEqual(r.outcome, Outcome.VERIFIED)
        self.assertEqual(r.unmet, [])


class ApproachTests(unittest.TestCase):
    def test_same_approach_cannot_repeat_after_failure(self):
        c = ready([Criterion("C1", "x")])
        c.begin_approach("flip the sign", ["src/app.py"])
        c.record_edit(["src/app.py"], "d1")
        c.record_verification("t", False, ["test_a"], ["C1"], "d1")
        with self.assertRaises(RepeatedApproach):
            c.begin_approach("Flip   the SIGN", ["src/app.py"], diagnosis="the test still sees a minus sign")

    def test_diagnosis_required_and_must_change(self):
        c = ready([Criterion("C1", "x")])
        c.begin_approach("a", ["f1.py"])
        c.record_edit(["f1.py"], "d1")
        c.record_verification("t", False, ["test_a"], ["C1"], "d1")
        with self.assertRaises(ControllerError):
            c.begin_approach("b", ["f2.py"], diagnosis="short")
        c.begin_approach("b", ["f2.py"], diagnosis="cause is in the cache key, not the parser")
        c.record_edit(["f2.py"], "d2")
        c.record_verification("t", False, ["test_b"], ["C1"], "d2")
        with self.assertRaises(RepeatedApproach):
            c.begin_approach("c", ["f3.py"], diagnosis="cause is in the cache key, not the parser")

    def test_attempt_budget(self):
        c = ready([Criterion("C1", "x")])
        c.s.max_attempts = 2
        for i, n in enumerate(("a", "b")):
            c.begin_approach(n, [f"f{i}.py"], diagnosis=f"diagnosis number {i} for approach {n}" if i else "")
            c.record_edit([f"f{i}.py"], f"d{i + 1}")
            c.record_verification("t", False, [f"test_{i}"], ["C1"], f"d{i + 1}")
        with self.assertRaises(BudgetExhausted):
            c.begin_approach("c", ["f9.py"], diagnosis="a third and different diagnosis here")
        self.assertEqual(c.report().outcome, Outcome.FAILED)

    def test_same_failure_across_approaches_escalates(self):
        c = ready([Criterion("C1", "x")])
        c.s.max_attempts = 6  # max_same_failure is 2: two approaches ending in the same failure end the retries
        for i in range(2):
            c.begin_approach(f"s{i}", [f"f{i}.py"], diagnosis=f"distinct diagnosis text number {i}" if i else "")
            c.record_edit([f"f{i}.py"], f"d{i + 1}")
            c.record_verification("t", False, ["test_same"], ["C1"], f"d{i + 1}")
        with self.assertRaises(BudgetExhausted):
            c.begin_approach("s9", ["f9.py"], diagnosis="yet another distinct diagnosis text")

    def test_preexisting_only_failure_is_not_an_approach_failure(self):
        c = ready([Criterion("C1", "x")], baseline=["test_old"])
        c.begin_approach("a", ["f.py"])
        c.record_edit(["f.py"], "d1")
        c.record_verification("t", False, ["test_old"], ["C1"], "d1")
        self.assertFalse(c.s.approaches[0].failed)


class ActionPolicyTests(unittest.TestCase):
    def test_table(self):
        ev = dc.evaluate_action
        self.assertEqual(ev("git status", []), ("allow", ""))
        self.assertEqual(ev("git commit -m x", []), ("needs_authorization", "commit"))
        self.assertEqual(ev("git commit -m x", ["commit"]), ("allow", ""))
        self.assertEqual(ev("git push origin HEAD", ["commit"]), ("needs_authorization", "push"))
        self.assertEqual(ev("git push --force-with-lease", ["push"]), ("needs_authorization", "force_push"))
        self.assertEqual(ev("git push -f origin x", ["push", "force_push"]), ("allow", ""))
        self.assertEqual(ev("rm -rf build", []), ("needs_authorization", "destructive:rm_recursive"))
        self.assertEqual(ev("git reset --hard HEAD~1", []), ("needs_authorization", "destructive:git_reset_hard"))
        self.assertEqual(ev("psql -c 'DROP TABLE users'", []), ("needs_authorization", "destructive:drop_table"))
        self.assertEqual(ev("kubectl delete pod x", []), ("needs_authorization", "destructive:kubectl_delete"))
        self.assertEqual(ev("sudo systemctl restart x", ["push", "commit"])[0], "deny")
        self.assertEqual(ev("echo ok && sudo ls", [])[0], "deny")
        self.assertEqual(ev("python -m pytest -q", []), ("allow", ""))

    def test_authorization_is_never_inferred(self):
        self.assertEqual(dc.evaluate_action("git commit -am x", ["push"])[0], "needs_authorization")

    def test_shell_continuation_cannot_downgrade_force_push(self):
        # The shell joins a backslash-newline before git sees argv. A regex over
        # the raw command must not treat the force flag as an ordinary push.
        command = "git push --\\\nforce-with-lease"
        self.assertEqual(dc.evaluate_action(command, ["push"]),
                         ("needs_authorization", "force_push"))


class ReviewTests(unittest.TestCase):
    def test_should_review_reasons(self):
        self.assertEqual(dc.should_review(5, ["a.py"], 0, False), [])
        self.assertEqual(dc.should_review(50, ["a.py"], 0, False), ["large_diff"])
        self.assertIn("sensitive_path", dc.should_review(3, ["src/auth/login.py"], 0, False))
        self.assertIn("needed_recovery", dc.should_review(3, ["a.py"], 2, False))
        self.assertIn("public_api", dc.should_review(3, ["a.py"], 0, True))
        self.assertIn("many_files", dc.should_review(3, list("abcd"), 0, False))

    def test_review_packet_has_no_reasoning_and_only_fresh_evidence(self):
        c = ready([Criterion("C1", "x")])
        c.record_verification("old run", True, [], ["C1"], "d0")
        c.record_edit(["a.py"], "d1")
        c.record_verification("new run", True, [], ["C1"], "d1")
        pkt = dc.review_packet(c.s, "diff --git a/a.py b/a.py")
        self.assertEqual([e["command"] for e in pkt["evidence"]], ["new run"])
        self.assertEqual(sorted(pkt), ["criteria", "diff", "evidence", "task"])


class PersistenceTests(unittest.TestCase):
    def test_round_trip_and_resume_after_compaction(self):
        c = ready([Criterion("C1", "x")], baseline=["test_old"])
        c.begin_approach("flip sign", ["src/app.py"])
        c.record_edit(["src/app.py"], "d1")
        c.record_verification("t", False, ["test_new"], ["C1"], "d1")
        c.s.authorizations.append("commit")
        text = c.s.to_json()
        c2 = Controller(TaskState.from_json(text))
        self.assertEqual(c2.s, c.s)
        block = c2.resume_block()
        self.assertIn("APPROACH FAILED: flip sign", block)
        self.assertIn("BASELINE_FAILURES: test_old", block)
        self.assertIn("AUTHORIZED: commit", block)
        self.assertIn("NEXT:", block)
        with self.assertRaises(RepeatedApproach):
            c2.begin_approach("flip sign", ["src/app.py"], diagnosis="a different diagnosis that is long enough")

    def test_resume_block_keeps_failed_approaches_when_trimmed(self):
        c = ready([Criterion(f"C{i}", "criterion text " * 5) for i in range(30)])
        c.s.approaches.append(dc.Approach(signature="s", strategy="bad idea", files=["a.py"], failed=True))
        block = c.resume_block(max_chars=300)
        self.assertIn("APPROACH FAILED: bad idea", block)
        self.assertLessEqual(len(block), 300)


class TreeDigestTests(unittest.TestCase):
    def test_digest_tracks_content_not_git_or_cache(self):
        def put(path, text):
            with open(path, "w") as fh:
                fh.write(text)

        with tempfile.TemporaryDirectory() as d:
            put(os.path.join(d, "a.py"), "x = 1\n")
            h1 = dc.tree_digest(d)
            os.makedirs(os.path.join(d, ".git"))
            put(os.path.join(d, ".git", "HEAD"), "ref")
            os.makedirs(os.path.join(d, "__pycache__"))
            put(os.path.join(d, "__pycache__", "a.pyc"), "junk")
            self.assertEqual(dc.tree_digest(d), h1)
            put(os.path.join(d, "a.py"), "x = 2\n")
            self.assertNotEqual(dc.tree_digest(d), h1)


class NextActionTests(unittest.TestCase):
    def test_next_action_names_the_open_criteria(self):
        c = ready(phase=Phase.VERIFY)
        self.assertIn("C1", c.next_action())
        c.record_verification("t", True, [], ["C1", "C2"], "d0")
        self.assertIn("review or report", c.next_action())


if __name__ == "__main__":
    unittest.main()
