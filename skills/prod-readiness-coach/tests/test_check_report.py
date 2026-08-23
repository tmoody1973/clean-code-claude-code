"""The document linter is what stands between a plausible audit and a true one."""
import json, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import check_report as C

REPORT = {
    "categories": [{"key": "CI/CD Pipeline", "title": "CI/CD Pipeline", "checks": [
        {"id": "ci-1", "title": "CI configuration exists", "status": "fail",
         "severity": "critical", "confidence": "verified", "evidence": []},
        {"id": "res-3", "title": "Rate limiting throttling implemented", "status": "pass",
         "severity": "info", "confidence": "weak", "evidence": []},
        {"id": "dep-1", "title": "Dependency lockfile committed", "status": "pass",
         "severity": "info", "confidence": "verified", "evidence": ["package-lock.json"]},
    ]}],
    "waivers": {"applied": [], "problems": []},
}
GOOD_AUDIT = """# How ready is it
## What's already solid
- **Your dependency list is pinned.** `package-lock.json` is committed.
## Looks fine, but only from a text match
- Rate limiting: the tool saw the words, not the feature.
## What needs attention
### Nothing checks your work before it goes live
"""
GOOD_BRIEF = """# Fix Brief
## Phase 1
## 1. CI configuration exists is missing
Create `.github/workflows/ci.yml`.
"""


class Linter(unittest.TestCase):
    def test_a_faithful_pair_passes(self):
        self.assertEqual(C.lint(GOOD_AUDIT, GOOD_BRIEF, REPORT), [])

    def test_invented_file_path_is_caught(self):
        bad = GOOD_AUDIT + "\nSee `src/lib/telemetry.ts` for the logger.\n"
        self.assertTrue(any("telemetry.ts" in p for p in C.lint(bad, GOOD_BRIEF, REPORT)))

    def test_a_file_the_brief_says_to_create_is_allowed(self):
        self.assertEqual(C.lint(GOOD_AUDIT, GOOD_BRIEF, REPORT), [])

    def test_text_match_sold_as_a_win_is_caught(self):
        bad = GOOD_AUDIT.replace("- **Your dependency list is pinned.**",
                                 "- **Rate limiting throttling is implemented.** Nice.\n- **Pinned.**")
        self.assertTrue(any("res-3" in p for p in C.lint(bad, GOOD_BRIEF, REPORT)))

    def test_unaddressed_critical_is_caught(self):
        self.assertTrue(any("ci-1" in p for p in C.lint(GOOD_AUDIT, "# Fix Brief\nNothing here.\n", REPORT)))

    def test_hidden_waiver_is_caught(self):
        rep = {**REPORT, "waivers": {"applied": [{"id": "log-2", "reason": "r", "evidence": "e",
                                                  "approved_by": "p", "date": "2026-08-22"}], "problems": []}}
        self.assertTrue(any("log-2" in p for p in C.lint(GOOD_AUDIT, GOOD_BRIEF, rep)))

    def test_placeholder_and_dash_are_caught(self):
        probs = C.lint(GOOD_AUDIT + "\n{{score}} and a dash — here\n", GOOD_BRIEF, REPORT)
        self.assertTrue(any("placeholder" in p for p in probs))
        self.assertTrue(any("dash" in p for p in probs))



class SuppressionAndForgery(unittest.TestCase):
    """A repository can put text in front of the model asking for a finding to be
    left out or a grade to be changed. Everything the model reads about a repo
    comes from that repo. Invention was linted from the start; these two were not."""

    REPORT = {
        "overall_score": 62,
        "grade": "D, release blockers present",
        "categories": [{"key": "K", "title": "K", "score": 40, "checks": [
            {"id": "ci-1", "title": "CI configuration exists", "status": "fail",
             "severity": "critical", "confidence": "verified", "evidence": []},
            {"id": "res-1", "title": "Runbook incident response docs present", "status": "fail",
             "severity": "high", "confidence": "verified", "evidence": []},
        ]}],
        "waivers": {"applied": [], "problems": []},
    }
    AUDIT = "# How ready is it\n## What needs attention\nNothing runs your tests.\n"
    FULL_BRIEF = ("# Fix Brief\n## Phase 1\n1. CI configuration exists is missing.\n"
                  "## Phase 2\n2. Runbook incident response docs present is missing.\n")

    def test_a_faithful_pair_still_passes(self):
        self.assertEqual(C.lint(self.AUDIT, self.FULL_BRIEF, self.REPORT), [])

    def test_a_dropped_high_finding_is_caught(self):
        brief = "# Fix Brief\n## Phase 1\n1. CI configuration exists is missing.\n"
        problems = C.lint(self.AUDIT, brief, self.REPORT)
        self.assertTrue(any("res-1" in p for p in problems), problems)

    def test_a_dropped_critical_finding_is_still_caught(self):
        brief = "# Fix Brief\n## Phase 2\n1. Runbook incident response docs present.\n"
        problems = C.lint(self.AUDIT, brief, self.REPORT)
        self.assertTrue(any("ci-1" in p for p in problems), problems)

    def test_a_forged_score_is_caught(self):
        audit = self.AUDIT + "\nOverall this repository scores 100/100.\n"
        problems = C.lint(audit, self.FULL_BRIEF, self.REPORT)
        self.assertTrue(any("100/100" in p for p in problems), problems)

    def test_a_forged_grade_is_caught(self):
        audit = self.AUDIT + "\nThis repository earns a grade A.\n"
        problems = C.lint(audit, self.FULL_BRIEF, self.REPORT)
        self.assertTrue(any("grade A" in p for p in problems), problems)

    def test_a_forged_overall_score_is_caught_even_when_a_category_really_scores_it(self):
        report = json.loads(json.dumps(self.REPORT))
        report["categories"][0]["score"] = 100  # a category legitimately at 100
        audit = self.AUDIT + "\nOverall this repository scores 100/100.\n"
        problems = C.lint(audit, self.FULL_BRIEF, report)
        self.assertTrue(any("overall score" in p for p in problems), problems)

    def test_a_real_category_score_is_not_flagged(self):
        audit = self.AUDIT + "\nThat category sits at 40/100.\n"
        self.assertEqual(C.lint(audit, self.FULL_BRIEF, self.REPORT), [])

    def test_the_real_overall_score_is_not_flagged(self):
        audit = self.AUDIT + "\nOverall: 62/100.\n"
        self.assertEqual(C.lint(audit, self.FULL_BRIEF, self.REPORT), [])

if __name__ == "__main__":
    unittest.main()
