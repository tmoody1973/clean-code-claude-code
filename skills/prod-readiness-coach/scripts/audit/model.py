"""Findings, categories, waivers, contradictions, and the substance helpers."""
import fnmatch
import json
import re
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

# --------------------------------------------------------------------------
# Data model
# --------------------------------------------------------------------------

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4, "pass": 5}
SEVERITY_LABEL = {
    "critical": "🔴 CRITICAL",
    "high": "🟠 HIGH",
    "medium": "🟡 MEDIUM",
    "low": "🔵 LOW",
    "info": "ℹ️ INFO",
    "pass": "✅ PASS",
}
# Points removed from the 100-point category score when a check with this
# severity fails. Weighted so a single CRITICAL miss visibly tanks the score.
SEVERITY_PENALTY = {"critical": 30, "high": 18, "medium": 10, "low": 5, "info": 0}


@dataclass
class CheckResult:
    id: str
    category: str
    title: str
    status: str  # "pass" | "fail" | "warn" | "info"
    severity: str  # "critical" | "high" | "medium" | "low" | "info"
    detail: str
    recommendation: str = ""
    evidence: list[str] = field(default_factory=list)
    best_practice_ref: str = ""
    # "verified": structural evidence (file/config/dependency exists).
    # "weak": a text match only. A weak pass means "possible, verify by hand";
    # it never counts as proof that the control exists.
    confidence: str = "verified"
    # Set when a repo waiver moved this check out of "fail". Keeps the original status.
    waived_from: str = ""


# Checks whose pass is based on a text search, not a structural check.
WEAK_PASS_IDS = {"log-4", "res-3", "sec-4"}

# A control can live outside the repository (an org-level pipeline, a platform
# dashboard, a secrets vault). Without a way to say so, --fail-on can never
# reach 0 and a phase gate becomes a trap that rewards faking the fix. A waiver
# is that escape hatch, and it is deliberately expensive: every field is
# required, it is dated, it expires, and it is printed in every report.
WAIVER_FILE = ".prod-audit-waivers.json"
WAIVER_FIELDS = ("id", "reason", "evidence", "approved_by", "date")
WAIVER_MAX_AGE_DAYS = 180

# Pairs where one check's pass is undermined by another check's failure.
# (passing ids, failing ids, what the conflict means)
CONTRADICTIONS = [
    ({"sec-4"}, {"sec-2"},
     "The secret scan found nothing, but `.gitignore` does not exclude env files. A real `.env` "
     "could be committed and never match a pattern. Treat the clean scan as unproven, not as a win."),
    ({"log-4"}, {"log-1"},
     "Request or correlation IDs are mentioned, but no logging library is configured. IDs with "
     "nothing to write them into are a mention, not a control."),
    ({"test-1"}, {"ci-2"},
     "Test files exist but no pipeline step runs them. Tests nobody runs are documentation."),
    ({"res-2"}, {"ms-1"},
     "A rollback procedure is documented, but this repo deploys to more than one surface and no "
     "coordinated procedure covering all of them was found. The documented rollback may undo only part."),
]


# A control that exists in name only is a costume. `docs/runbook.md` can be an
# empty file; a CI step can be `echo "test skipped"`; a README "rollback" can be
# an unchecked TODO. Existence is not function, so these checks look at content.
TEST_RUNNER_RX = re.compile(
    r"\b(?:npm|pnpm|yarn|bun)\s+(?:run\s+)?test\b|\bnpx?\s+(?:vitest|jest|mocha|ava|playwright|cypress)\b"
    r"|\b(?:vitest|jest|mocha|ava|karma)\b|\bpytest\b|\bpython\s+-m\s+(?:pytest|unittest)\b"
    r"|\bgo\s+test\b|\bcargo\s+test\b|\brspec\b|\bphpunit\b|\bdotnet\s+test\b|\bmvn\s+test\b"
    r"|\bgradle(?:w)?\s+test\b|\bnode\s+--test\b|\brake\s+test\b",
    re.IGNORECASE,
)
# An unchecked task box, or a promise to do it later, is not a procedure.
TODO_LINE_RX = re.compile(r"^\s*[-*]?\s*\[\s\]|\b(?:todo|tbd|coming soon|someday|we should|should probably)\b",
                          re.IGNORECASE)
MIN_DOC_WORDS = 50


def runs_a_test_suite(text: str) -> bool:
    """True when text invokes a real test runner, not merely the word 'test'.
    Shell strings are stripped first so `echo "test skipped"` does not count."""
    without_strings = re.sub(r"""(['"]).*?\1""", " ", text or "", flags=re.S)
    return bool(TEST_RUNNER_RX.search(without_strings))


def has_substance(text: str, min_words: int = MIN_DOC_WORDS) -> bool:
    """A document with almost no prose is a placeholder, not documentation."""
    body = "\n".join(l for l in (text or "").splitlines() if not l.lstrip().startswith("#"))
    return len(body.split()) >= min_words


def load_waivers(repo: "Repo") -> tuple[dict, list[str]]:
    """Return ({check_id: waiver}, [problems]). A bad waiver is reported, never silently ignored."""
    raw = repo.read(WAIVER_FILE)
    if not raw.strip():
        return {}, []
    try:
        entries = json.loads(raw)
    except Exception as e:
        return {}, [f"{WAIVER_FILE} is not valid JSON ({e}). No waivers applied."]
    if not isinstance(entries, list):
        return {}, [f"{WAIVER_FILE} must be a list of waiver objects. No waivers applied."]
    good, problems, now = {}, [], datetime.now(timezone.utc)
    for i, w in enumerate(entries):
        if not isinstance(w, dict):
            problems.append(f"{WAIVER_FILE}[{i}] is not an object; skipped.")
            continue
        missing = [f for f in WAIVER_FIELDS if not str(w.get(f, "")).strip()]
        if missing:
            problems.append(f"{WAIVER_FILE}[{i}] ({w.get('id', 'no id')}) is missing "
                            f"{', '.join(missing)}; skipped. Every field is required.")
            continue
        try:
            when = datetime.strptime(str(w["date"]).strip(), "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            problems.append(f"{WAIVER_FILE}[{i}] ({w['id']}) has date '{w['date']}'; "
                            "use YYYY-MM-DD. Skipped.")
            continue
        age = (now - when).days
        if age > WAIVER_MAX_AGE_DAYS:
            problems.append(f"Waiver for {w['id']} expired ({age} days old, limit "
                            f"{WAIVER_MAX_AGE_DAYS}). The finding is back. Re-confirm it or fix it.")
            continue
        good[str(w["id"]).strip()] = w
    return good, problems


def find_contradictions(categories: list["Category"]) -> list[dict]:
    """Where a pass and a fail disagree about the same control, say so."""
    by_id = {c.id: c for cat in categories for c in cat.checks}
    out = []
    for passing, failing, note in CONTRADICTIONS:
        if all(by_id.get(i) and by_id[i].status == "pass" for i in passing) \
                and all(by_id.get(i) and by_id[i].status == "fail" for i in failing):
            out.append({"ids": sorted(passing | failing), "passing": sorted(passing),
                        "failing": sorted(failing), "note": note})
    return out

# What kind of thing the repo is. A check that does not apply to the profile
# is reported as "n/a" and left out of the score. A framework or deploy
# surface implies web-app (strict). A language alone implies nothing, so the
# profile is "unknown" and runtime checks report insufficient evidence.
PROFILES = ("web-app", "api", "worker", "cli", "library", "unknown")
_SERVICE_ONLY = {"log-3", "res-3"}                       # needs an HTTP surface
_DEPLOYED_ONLY = {"log-1", "log-2", "log-4", "res-1", "res-2", "res-4", "res-5",
                  "sec-5", "ms-1", "ci-5"} | _SERVICE_ONLY  # needs to run somewhere
CHECK_SKIPS_BY_PROFILE = {
    "web-app": set(),
    "api": set(),
    "worker": _SERVICE_ONLY,
    "cli": _DEPLOYED_ONLY,
    "library": _DEPLOYED_ONLY,
    # Nothing recognizable was detected. Runtime-specific checks are reported
    # as n/a ("insufficient evidence") rather than failed web-app checks.
    "unknown": _DEPLOYED_ONLY,
}


@dataclass
class Category:
    key: str
    title: str
    description: str
    best_practice_ref: str
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def score(self) -> int:
        score = 100
        for c in self.checks:
            if c.status == "fail":
                score -= SEVERITY_PENALTY.get(c.severity, 5)
        return max(0, score)

    @property
    def has_weak_evidence(self) -> bool:
        """True when any pass here rests only on a text match, so this is not a clean win."""
        return any(c.status == "pass" and c.confidence == "weak" for c in self.checks)

    @property
    def applicable(self) -> bool:
        return any(c.status != "n/a" for c in self.checks)

    @property
    def blocking_count(self) -> int:
        return sum(1 for c in self.checks if c.status == "fail" and c.severity == "critical")


