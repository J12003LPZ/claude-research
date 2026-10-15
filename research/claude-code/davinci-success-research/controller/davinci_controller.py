"""DaVinci workflow controller: deterministic guards around an LLM coding loop.

Independent design. It is written from the observed behavior recorded in this research (Claude Code 2.1.296
lets a model finish with no test run and with a failing test; see ../01-runtime-verified-mechanisms.md) and from the
requirements in ../04-davinci-workflow-controller.md. It contains no Claude Code code or prompt text.

The model proposes; this module decides what the model may claim and which transitions are legal.
Everything here is pure and deterministic: same state and events give the same answer.
"""
from __future__ import annotations

import dataclasses
import enum
import hashlib
import json
import os
import re
import shlex
from typing import Iterable


class Phase(str, enum.Enum):
    UNDERSTAND = "understand"
    EXPLORE = "explore"
    PLAN = "plan"
    IMPLEMENT = "implement"
    VERIFY = "verify"
    RECOVER = "recover"
    REVIEW = "review"
    REPORT = "report"
    DONE = "done"


class Outcome(str, enum.Enum):
    VERIFIED = "verified"      # every criterion has fresh passing evidence and no new failure exists
    UNVERIFIED = "unverified"  # work was done, evidence is missing or stale; nothing failed
    BLOCKED = "blocked"        # an external condition stops progress
    FAILED = "failed"          # a fresh run shows a new failure, or the attempt budget is spent


TRANSITIONS: dict[Phase, set[Phase]] = {
    Phase.UNDERSTAND: {Phase.EXPLORE},
    Phase.EXPLORE: {Phase.PLAN, Phase.UNDERSTAND},
    Phase.PLAN: {Phase.IMPLEMENT, Phase.EXPLORE},
    Phase.IMPLEMENT: {Phase.VERIFY},
    Phase.VERIFY: {Phase.REVIEW, Phase.RECOVER, Phase.REPORT},
    Phase.RECOVER: {Phase.IMPLEMENT, Phase.PLAN, Phase.REPORT},
    Phase.REVIEW: {Phase.REPORT, Phase.RECOVER},
    Phase.REPORT: {Phase.DONE},
    Phase.DONE: set(),
}


class ControllerError(Exception):
    """A requested action is illegal in the current state. The message says what is required instead."""


class RepeatedApproach(ControllerError):
    pass


class BudgetExhausted(ControllerError):
    pass


# ---------------------------------------------------------------- data

@dataclasses.dataclass
class Criterion:
    id: str
    text: str
    kind: str = "executable"  # executable: a command must pass; static: a file/diff check; review: a reviewer verdict


@dataclasses.dataclass
class Evidence:
    kind: str                 # "run" (a command with an exit code) or "inspection" (a diff or file check)
    command: str
    passed: bool
    tree_digest: str          # digest of the working tree when the evidence was produced
    criteria: list[str]
    failing: list[str] = dataclasses.field(default_factory=list)  # failing test ids, when kind == "run"
    output_digest: str = ""


@dataclasses.dataclass
class Approach:
    signature: str
    strategy: str
    files: list[str]
    failing_after: list[str] = dataclasses.field(default_factory=list)
    diagnosis: str = ""
    failed: bool = False


@dataclasses.dataclass
class Review:
    tree_digest: str
    blocking: list[str]
    approved: bool


@dataclasses.dataclass
class Report:
    outcome: Outcome
    unmet: list[str]
    new_failures: list[str]
    preexisting_failures: list[str]
    stale: list[str]
    notes: list[str]


@dataclasses.dataclass
class TaskState:
    task: str
    phase: Phase = Phase.UNDERSTAND
    criteria: list[Criterion] = dataclasses.field(default_factory=list)
    baseline_failures: list[str] | None = None   # None means the baseline was never recorded
    tree_digest: str = ""
    evidence: list[Evidence] = dataclasses.field(default_factory=list)
    approaches: list[Approach] = dataclasses.field(default_factory=list)
    current: str = ""                             # signature of the approach being tried
    reviews: list[Review] = dataclasses.field(default_factory=list)
    changed_paths: list[str] = dataclasses.field(default_factory=list)
    recover_rounds: int = 0
    plan_approved: bool = False
    plan_approval_required: bool = False
    authorizations: list[str] = dataclasses.field(default_factory=list)
    blocked_reason: str = ""
    waiver: str = ""                              # the user's reason for accepting no verification
    max_attempts: int = 4
    max_same_failure: int = 2

    def to_json(self) -> str:
        return json.dumps(dataclasses.asdict(self), sort_keys=True)

    @staticmethod
    def from_json(text: str) -> "TaskState":
        d = json.loads(text)
        d["phase"] = Phase(d["phase"])
        d["criteria"] = [Criterion(**c) for c in d["criteria"]]
        d["evidence"] = [Evidence(**e) for e in d["evidence"]]
        d["approaches"] = [Approach(**a) for a in d["approaches"]]
        d["reviews"] = [Review(**r) for r in d["reviews"]]
        return TaskState(**d)


# ---------------------------------------------------------------- helpers

EXECUTABLE_EXTS = {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".kt", ".swift", ".c", ".cc", ".cpp",
                   ".h", ".hpp", ".cs", ".rb", ".php", ".sh", ".sql", ".lua"}
NON_EXECUTABLE_EXTS = {".md", ".txt", ".rst", ".adoc"}
SENSITIVE = re.compile(r"(auth|security|secret|payment|billing|migration|\.github/workflows|dockerfile|crypto)", re.I)


def tree_digest(root: str, ignore: Iterable[str] = (".git", "__pycache__", ".pytest_cache", "node_modules")) -> str:
    """Content digest of every file under root, independent of mtimes and of git."""
    skip = set(ignore)
    h = hashlib.sha256()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in skip)
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            h.update(rel.encode() + b"\0")
            with open(full, "rb") as fh:
                h.update(hashlib.sha256(fh.read()).digest())
    return h.hexdigest()


def classify_change(paths: Iterable[str]) -> str:
    """'executable' when any changed path can change behavior, else 'non_executable'. Unknown extensions count as executable."""
    kinds = set()
    for p in paths:
        ext = os.path.splitext(p)[1].lower()
        kinds.add("non_executable" if ext in NON_EXECUTABLE_EXTS else "executable")
    return "non_executable" if kinds == {"non_executable"} else ("executable" if kinds else "none")


def approach_signature(strategy: str, files: Iterable[str]) -> str:
    norm = re.sub(r"\s+", " ", strategy.strip().lower())
    return hashlib.sha1((norm + "|" + ",".join(sorted(set(files)))).encode()).hexdigest()[:16]


def classify_failures(baseline: list[str] | None, failing_now: list[str]) -> dict[str, list[str]]:
    """Split current failures into new (introduced) and preexisting. Without a baseline every failure counts as new."""
    if baseline is None:
        return {"new": sorted(failing_now), "preexisting": [], "fixed": []}
    base, now = set(baseline), set(failing_now)
    return {"new": sorted(now - base), "preexisting": sorted(now & base), "fixed": sorted(base - now)}


# ---------------------------------------------------------------- action policy

COMMIT_RE = re.compile(r"\bgit\s+commit\b")
PUSH_RE = re.compile(r"\bgit\s+push\b")
FORCE_PUSH_RE = re.compile(r"\bgit\s+push\b.*(--force\b|\s-f\b)")
DESTRUCTIVE = [
    ("rm_recursive", re.compile(r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|-r\s+-f|-f\s+-r)\b")),
    ("git_reset_hard", re.compile(r"\bgit\s+reset\s+--hard\b")),
    ("git_clean", re.compile(r"\bgit\s+clean\s+-[a-zA-Z]*f")),
    ("drop_table", re.compile(r"\bdrop\s+(table|database)\b", re.I)),
    ("kubectl_delete", re.compile(r"\bkubectl\s+delete\b")),
]
SUDO_RE = re.compile(r"(^|[;&|]\s*)sudo\b")
SHELL_SYNTAX = re.compile(r"[;&|<>`$]")


def _parse_action_command(command: str) -> list[str] | None:
    """Parse one direct shell command, or return None when shell semantics are opaque.

    Authorization decisions must use the argv the shell will hand to the program, not
    regex matches in the raw source. Compound commands, expansions and substitutions
    are rejected because this small policy parser cannot prove what they execute.
    """
    if not isinstance(command, str):
        return None
    command = re.sub(r"\\\r?\n", "", command)
    if not command.strip() or "\n" in command or "\r" in command or SHELL_SYNTAX.search(command):
        return None
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|<>")
        lexer.whitespace_split = True
        argv = list(lexer)
    except ValueError:
        return None
    if not argv or any(token in {";", "&", "&&", "|", "||", "<", ">", ">>", "<<"} for token in argv):
        return None
    return argv


def evaluate_action(command: str, authorizations: Iterable[str]) -> tuple[str, str]:
    """Return (decision, reason). decision is 'allow', 'needs_authorization' or 'deny'.

    An authorization is a string the user granted explicitly: 'commit', 'push', 'force_push', or 'destructive:<name>'.
    Nothing here ever grants one. Commands whose shell syntax cannot be parsed safely are denied rather than
    classified from a raw substring, preventing a shell/parser differential from downgrading a protected action.
    """
    auth = set(authorizations)
    argv = _parse_action_command(command)
    if argv is None:
        return "deny", "shell syntax is not safely parseable; run one direct command at a time"
    parsed = " ".join(argv)
    if any(os.path.basename(token) == "sudo" for token in argv):
        return "deny", "sudo is never run by the agent; list the command for the user"
    if FORCE_PUSH_RE.search(parsed):
        return ("allow", "") if "force_push" in auth else ("needs_authorization", "force_push")
    if PUSH_RE.search(parsed):
        return ("allow", "") if "push" in auth else ("needs_authorization", "push")
    if COMMIT_RE.search(parsed):
        return ("allow", "") if "commit" in auth else ("needs_authorization", "commit")
    for name, rx in DESTRUCTIVE:
        if rx.search(parsed):
            return ("allow", "") if f"destructive:{name}" in auth else ("needs_authorization", f"destructive:{name}")
    return "allow", ""


# ---------------------------------------------------------------- review trigger

def should_review(changed_lines: int, changed_paths: Iterable[str], recover_rounds: int, public_api_changed: bool) -> list[str]:
    """Reasons an independent review is worth its cost. An empty list means skip it."""
    paths = list(changed_paths)
    reasons = []
    if changed_lines >= 40:
        reasons.append("large_diff")
    if len(paths) >= 4:
        reasons.append("many_files")
    if any(SENSITIVE.search(p) for p in paths):
        reasons.append("sensitive_path")
    if recover_rounds >= 2:
        reasons.append("needed_recovery")
    if public_api_changed:
        reasons.append("public_api")
    return reasons


def review_packet(state: TaskState, diff_text: str) -> dict:
    """What an independent reviewer receives: criteria, evidence summaries and the diff. Never the implementer's reasoning."""
    return {
        "task": state.task,
        "criteria": [dataclasses.asdict(c) for c in state.criteria],
        "evidence": [{"command": e.command, "passed": e.passed, "failing": e.failing, "criteria": e.criteria}
                     for e in state.evidence if e.tree_digest == state.tree_digest],
        "diff": diff_text,
    }


# ---------------------------------------------------------------- controller

class Controller:
    def __init__(self, state: TaskState):
        self.s = state

    # transitions
    def move(self, to: Phase) -> None:
        s = self.s
        if to not in TRANSITIONS[s.phase]:
            raise ControllerError(f"illegal transition {s.phase.value} -> {to.value}")
        if s.phase == Phase.PLAN and to == Phase.IMPLEMENT:
            if not s.criteria:
                raise ControllerError("set acceptance criteria before implementing")
            if s.plan_approval_required and not s.plan_approved:
                raise ControllerError("plan approval is required before implementing")
        if s.phase == Phase.VERIFY and to == Phase.REVIEW and not self._fresh_passing_run_exists():
            raise ControllerError("review needs a fresh passing verification run")
        if to == Phase.RECOVER:
            s.recover_rounds += 1
        s.phase = to

    def _fresh_passing_run_exists(self) -> bool:
        return any(self._effective_pass(e) and e.tree_digest == self.s.tree_digest for e in self.s.evidence)

    # inputs
    def set_criteria(self, criteria: list[Criterion]) -> None:
        if not criteria:
            raise ControllerError("at least one acceptance criterion is required")
        ids = [c.id for c in criteria]
        if len(set(ids)) != len(ids):
            raise ControllerError("criterion ids must be unique")
        self.s.criteria = criteria

    def record_baseline(self, failing: list[str], digest: str) -> None:
        self.s.baseline_failures = sorted(failing)
        self.s.tree_digest = digest

    def record_edit(self, paths: list[str], digest: str) -> None:
        if self.s.phase not in (Phase.IMPLEMENT, Phase.RECOVER):
            raise ControllerError(f"edits are not legal in phase {self.s.phase.value}")
        self.s.changed_paths = sorted(set(self.s.changed_paths) | set(paths))
        self.s.tree_digest = digest

    def begin_approach(self, strategy: str, files: list[str], diagnosis: str = "") -> Approach:
        s = self.s
        failed = [a for a in s.approaches if a.failed]
        if len(s.approaches) >= s.max_attempts:
            raise BudgetExhausted(f"attempt budget of {s.max_attempts} is spent; report the outcome")
        sig = approach_signature(strategy, files)
        if any(a.signature == sig for a in failed):
            raise RepeatedApproach("this approach already failed; choose a different strategy or different files")
        if failed:
            last = failed[-1]
            if len(diagnosis.strip()) < 20:
                raise ControllerError("after a failure, record a diagnosis (at least 20 characters) before the next approach")
            if diagnosis.strip() == last.diagnosis.strip():
                raise RepeatedApproach("the diagnosis is identical to the previous one; the cause is not understood yet")
            same = sum(1 for a in failed if sorted(a.failing_after) == sorted(last.failing_after) and a.failing_after)
            if same >= s.max_same_failure:
                raise BudgetExhausted("the same failure survived several approaches; escalate instead of retrying")
        a = Approach(signature=sig, strategy=strategy, files=sorted(set(files)), diagnosis=diagnosis)
        s.approaches.append(a)
        s.current = sig
        return a

    def record_verification(self, command: str, passed: bool, failing: list[str], criteria: list[str],
                            digest: str, kind: str = "run", output_digest: str = "") -> Evidence:
        s = self.s
        known = {c.id for c in s.criteria}
        bad = [c for c in criteria if c not in known]
        if bad:
            raise ControllerError(f"evidence names unknown criteria: {bad}")
        if passed and failing:
            raise ControllerError("evidence cannot pass and also list failing tests")
        ev = Evidence(kind=kind, command=command, passed=passed, tree_digest=digest, criteria=sorted(criteria),
                      failing=sorted(failing), output_digest=output_digest)
        s.evidence.append(ev)
        if digest == s.tree_digest and not self._effective_pass(ev):
            for a in s.approaches:
                if a.signature == s.current:
                    a.failed, a.failing_after = True, sorted(failing)
        return ev

    def record_review(self, blocking: list[str]) -> Review:
        r = Review(tree_digest=self.s.tree_digest, blocking=list(blocking), approved=not blocking)
        self.s.reviews.append(r)
        return r

    def block(self, reason: str) -> None:
        self.s.blocked_reason = reason

    # outputs
    def _effective_pass(self, e: Evidence) -> bool:
        """A run passes when its command passed, or when every failing test was already failing in the baseline."""
        if e.passed:
            return True
        base = self.s.baseline_failures
        return bool(e.failing) and base is not None and set(e.failing) <= set(base)

    def _fresh(self) -> list[Evidence]:
        """The latest evidence per command at the current tree digest. Earlier digests are stale by definition."""
        latest: dict[str, Evidence] = {}
        for e in self.s.evidence:
            if e.tree_digest == self.s.tree_digest:
                latest[e.command] = e
        return list(latest.values())

    def _satisfied(self, c: Criterion) -> bool:
        s = self.s
        if c.kind == "review":
            return any(r.approved and r.tree_digest == s.tree_digest for r in s.reviews)
        return any(c.id in e.criteria and self._effective_pass(e) for e in self._fresh())

    def report(self) -> Report:
        s = self.s
        notes: list[str] = []
        latest_failing: set[str] = set()
        for e in self._fresh():
            if not e.passed:
                latest_failing |= set(e.failing) or {"<run failed without test ids>"}
        split = classify_failures(s.baseline_failures, sorted(latest_failing))
        if s.baseline_failures is None and latest_failing:
            notes.append("baseline_missing: every failure is treated as new")
        if split["preexisting"]:
            notes.append("preexisting failures remain and were not caused by this change")
        unmet = [c.id for c in s.criteria if not self._satisfied(c)]
        stale = [c.id for c in s.criteria if c.id in unmet and c.kind != "review"
                 and any(c.id in e.criteria and self._effective_pass(e) and e.tree_digest != s.tree_digest for e in s.evidence)]
        if s.waiver:
            notes.append(f"waiver: {s.waiver}")
        if s.blocked_reason:
            return Report(Outcome.BLOCKED, unmet, split["new"], split["preexisting"], stale, [s.blocked_reason] + notes)
        if split["new"]:
            return Report(Outcome.FAILED, unmet, split["new"], split["preexisting"], stale, notes)
        if not unmet:
            return Report(Outcome.VERIFIED, [], [], split["preexisting"], [], notes)
        if sum(1 for a in s.approaches if a.failed) >= s.max_attempts:
            return Report(Outcome.FAILED, unmet, [], split["preexisting"], stale, ["attempt budget spent"] + notes)
        return Report(Outcome.UNVERIFIED, unmet, [], split["preexisting"], stale, notes)

    def may_claim(self, claim: str) -> tuple[bool, str]:
        """Gate for the words the final message may use. 'verified' and 'tests pass' need a VERIFIED report."""
        r = self.report()
        if claim in ("verified", "tests_pass", "done"):
            if r.outcome == Outcome.VERIFIED:
                return True, ""
            return False, f"outcome is {r.outcome.value}: unmet={r.unmet} new_failures={r.new_failures} stale={r.stale}"
        return True, ""

    def next_action(self) -> str:
        s, r = self.s, self.report()
        if s.phase == Phase.UNDERSTAND:
            return "state the task and acceptance criteria, then explore"
        if s.phase == Phase.EXPLORE:
            return "read the code the task touches, record the baseline failures, then plan"
        if s.phase == Phase.PLAN:
            return "set criteria" if not s.criteria else "get plan approval" if s.plan_approval_required and not s.plan_approved else "implement"
        if s.phase in (Phase.IMPLEMENT, Phase.RECOVER):
            return "edit, then verify"
        if s.phase == Phase.VERIFY:
            return f"run verification for: {r.unmet}" if r.unmet else "move to review or report"
        if s.phase == Phase.REVIEW:
            return "send the review packet to an independent reviewer"
        return "write the report"

    def resume_block(self, max_chars: int = 2000) -> str:
        """A compact, deterministic summary to re-inject after context compaction. Failed approaches always survive."""
        s, r = self.s, self.report()
        lines = [f"TASK: {s.task}", f"PHASE: {s.phase.value}  OUTCOME_SO_FAR: {r.outcome.value}",
                 "CRITERIA: " + "; ".join(f"{c.id}[{c.kind}]={'met' if c.id not in r.unmet else 'open'}" for c in s.criteria),
                 "BASELINE_FAILURES: " + ("unknown" if s.baseline_failures is None else ",".join(s.baseline_failures) or "none"),
                 f"CHANGED: {','.join(s.changed_paths) or 'none'}"]
        for a in s.approaches:
            lines.append(f"APPROACH {'FAILED' if a.failed else 'open'}: {a.strategy} files={','.join(a.files)} "
                         f"failing={','.join(a.failing_after)} diagnosis={a.diagnosis[:120]}")
        if s.authorizations:
            lines.append("AUTHORIZED: " + ",".join(s.authorizations))
        if s.blocked_reason:
            lines.append(f"BLOCKED: {s.blocked_reason}")
        lines.append(f"NEXT: {self.next_action()}")
        text = "\n".join(lines)
        if len(text) <= max_chars:
            return text
        keep = [ln for ln in lines if ln.startswith(("TASK", "PHASE", "NEXT", "APPROACH FAILED", "BLOCKED"))]
        return "\n".join(keep)[:max_chars]
