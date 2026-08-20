"""Smoke tests for prod_audit.py. Run: python3 -m unittest discover tests"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import prod_audit  # noqa: E402


def make_repo(files: dict[str, str]) -> Path:
    root = Path(tempfile.mkdtemp())
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    return root


def audit(files: dict[str, str]) -> dict:
    root = make_repo(files)
    cats, fp = prod_audit.run_audit(root)
    return prod_audit.render_json(cats, root.name, fp)


class EmptyRepo(unittest.TestCase):
    def test_empty_repo_does_not_crash_and_has_empty_fingerprint(self):
        r = audit({})
        self.assertEqual(r["stack_fingerprint"]["adapters_matched"], [])
        self.assertFalse(r["stack_fingerprint"]["multi_surface"])


class NextJsRepo(unittest.TestCase):
    FILES = {"package.json": json.dumps({"dependencies": {"next": "15.0.0"}}),
             "tsconfig.json": "{}", "package-lock.json": "{}"}

    def test_nextjs_without_vercel_json_infers_vercel_adapter(self):
        r = audit(self.FILES)
        fp = r["stack_fingerprint"]
        self.assertIn("nextjs", fp["frameworks"])
        self.assertIn("vercel", fp["deploy_surfaces"])
        self.assertIn("nextjs-vercel", fp["adapters_matched"])
        self.assertTrue(any("inferred" in e for e in fp["deploy_evidence"]["vercel"]))

    def test_nextjs_on_netlify_does_not_infer_vercel(self):
        r = audit({**self.FILES, "netlify.toml": ""})
        self.assertNotIn("vercel", r["stack_fingerprint"]["deploy_surfaces"])


class GradeCap(unittest.TestCase):
    def test_any_critical_caps_grade_at_d(self):
        r = audit(NextJsRepo.FILES)  # no CI, no tests -> criticals
        crit = sum(c["blocking_count"] if "blocking_count" in c else
                   sum(1 for k in c["checks"] if k["status"] == "fail" and k["severity"] == "critical")
                   for c in r["categories"])
        self.assertGreater(crit, 0)
        self.assertTrue(r["grade"].startswith(("D", "F")), r["grade"])

    def test_grade_for_without_criticals_uses_score(self):
        self.assertTrue(prod_audit.grade_for(95).startswith("A"))
        self.assertTrue(prod_audit.grade_for(95, critical_count=1).startswith("D"))
        self.assertTrue(prod_audit.grade_for(30, critical_count=1).startswith("F"))


class ConvexPairedRepo(unittest.TestCase):
    def test_next_plus_convex_matches_both_adapters_and_multi_surface(self):
        r = audit({**NextJsRepo.FILES,
                   "package.json": json.dumps({"dependencies": {"next": "15.0.0", "convex": "1.0.0"}}),
                   "convex/schema.ts": "export default {}"})
        fp = r["stack_fingerprint"]
        self.assertIn("convex", fp["adapters_matched"])
        self.assertIn("nextjs-vercel", fp["adapters_matched"])
        self.assertTrue(fp["multi_surface"])


if __name__ == "__main__":
    unittest.main()
