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


if __name__ == "__main__":
    unittest.main()
