"""Smoke tests for prod_audit.py. Run: python3 -m unittest discover tests"""
import json
import subprocess
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


def audit(files: dict[str, str], profile=None) -> dict:
    root = make_repo(files)
    cats, fp = prod_audit.run_audit(root, profile)
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


def check(report: dict, check_id: str) -> dict:
    return next(k for c in report["categories"] for k in c["checks"] if k["id"] == check_id)


class HonestyFixes(unittest.TestCase):
    FAKE_KEY = 'AKIA' + 'ABCDEFGHIJKLMNOP'  # AWS access key shape

    def test_secret_in_yaml_config_is_found(self):
        r = audit({"config/production.yaml": f'aws_access_key_id: "{self.FAKE_KEY}"\n'})
        self.assertEqual(check(r, "sec-4")["status"], "fail")

    def test_secret_in_untracked_file_is_found_in_git_repo(self):
        root = make_repo({"README.md": "x"})
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init"],
                       cwd=root, check=True)
        (root / "leak.py").write_text(f'KEY = "{self.FAKE_KEY}"\n')  # untracked
        cats, fp = prod_audit.run_audit(root)
        r = prod_audit.render_json(cats, root.name, fp)
        self.assertEqual(check(r, "sec-4")["status"], "fail")

    def test_comment_only_mention_does_not_pass_rate_limit_or_correlation(self):
        r = audit({"app.py": "# TODO: add rate-limit and correlation-id handling later\n"})
        self.assertNotEqual(check(r, "res-3")["status"], "pass")
        self.assertNotEqual(check(r, "log-4")["status"], "pass")

    def test_text_match_pass_is_marked_weak(self):
        r = audit({"app.py": "limiter = rate_limit(100)\nlog(request_id=rid)\n"})
        self.assertEqual(check(r, "res-3")["confidence"], "weak")
        self.assertEqual(check(r, "log-4")["confidence"], "weak")
        self.assertEqual(check(r, "ci-1")["confidence"], "verified")

    def test_nextjs_with_dockerfile_does_not_infer_vercel(self):
        r = audit({**NextJsRepo.FILES, "Dockerfile": "FROM node:20"})
        fp = r["stack_fingerprint"]
        self.assertIn("docker", fp["deploy_surfaces"])
        self.assertNotIn("vercel", fp["deploy_surfaces"])
        self.assertNotIn("nextjs-vercel", fp["adapters_matched"])

    def test_agents_md_alone_satisfies_agent_context_check(self):
        r = audit({"AGENTS.md": "Build: npm run build. Test: npm test. " * 10})
        self.assertEqual(check(r, "agent-1")["status"], "pass")


class Profiles(unittest.TestCase):
    def test_cli_profile_marks_service_checks_na_and_skips_them_in_score(self):
        r = audit({"tool.py": "print(1)"}, profile="cli")
        self.assertEqual(check(r, "log-3")["status"], "n/a")
        self.assertEqual(check(r, "res-3")["status"], "n/a")
        self.assertEqual(check(r, "ci-1")["status"], "fail")  # still applies
        logging = next(c for c in r["categories"] if c["key"] == "Structured Logging & Observability")
        self.assertTrue(all(k["status"] == "n/a" for k in logging["checks"]))
        self.assertEqual(r["stack_fingerprint"]["profile_source"], "given")

    def test_nextjs_guesses_web_app(self):
        r = audit(NextJsRepo.FILES)
        self.assertEqual(r["stack_fingerprint"]["profile"], "web-app")
        self.assertEqual(r["stack_fingerprint"]["profile_source"], "guessed")

    def test_convex_guesses_api_and_keeps_rate_limit_check(self):
        r = audit({"package.json": json.dumps({"dependencies": {"convex": "1.0.0"}}),
                   "convex/schema.ts": ""})
        self.assertEqual(r["stack_fingerprint"]["profile"], "api")
        self.assertNotEqual(check(r, "res-3")["status"], "n/a")

    def test_package_with_bin_guesses_cli(self):
        r = audit({"package.json": json.dumps({"bin": {"x": "cli.js"}})})
        self.assertEqual(r["stack_fingerprint"]["profile"], "cli")

    def test_language_without_framework_is_unknown(self):
        r = audit({"main.py": "print(1)", "requirements.txt": "requests"})
        self.assertEqual(r["stack_fingerprint"]["profile"], "unknown")
        self.assertEqual(check(r, "log-3")["status"], "n/a")
        self.assertEqual(check(r, "ci-1")["status"], "fail")  # still applies

    def test_nothing_recognized_is_unknown_and_reports_insufficient_evidence(self):
        r = audit({"notes.txt": "hello"})
        self.assertEqual(r["stack_fingerprint"]["profile"], "unknown")
        self.assertEqual(check(r, "log-3")["status"], "n/a")
        self.assertIn("insufficient evidence", check(r, "log-3")["detail"].lower())

    def test_worker_profile_skips_http_checks_only(self):
        r = audit({"job.py": "x=1"}, profile="worker")
        self.assertEqual(check(r, "log-3")["status"], "n/a")
        self.assertNotEqual(check(r, "log-2")["status"], "n/a")


class Security(unittest.TestCase):
    KEY = 'AKIA' + 'ABCDEFGHIJKLMNOP'

    def test_secret_value_never_appears_in_report(self):
        r = audit({"config.yaml": f'aws_key: "{self.KEY}"\n'})
        blob = json.dumps(r)
        self.assertNotIn(self.KEY, blob)
        ev = check(r, "sec-4")["evidence"][0]
        self.assertTrue(ev.startswith("config.yaml:1 [AWS Access Key ID] AKIA"), ev)
        self.assertIn("…", ev)

    def test_symlink_outside_repo_is_not_read(self):
        outside = Path(tempfile.mkdtemp()) / "outside.env"
        outside.write_text(f'AWS_KEY="{self.KEY}"\n')
        root = make_repo({"README.md": "x"})
        (root / "config.env").symlink_to(outside)
        cats, fp = prod_audit.run_audit(root)
        r = prod_audit.render_json(cats, root.name, fp)
        self.assertEqual(check(r, "sec-4")["status"], "pass")
        self.assertNotIn(self.KEY, json.dumps(r))


class NotApplicable(unittest.TestCase):
    def test_fully_na_category_has_null_score_not_100(self):
        r = audit({"tool.py": "print(1)"}, profile="cli")
        logging = next(c for c in r["categories"] if c["key"] == "Structured Logging & Observability")
        self.assertFalse(logging["applicable"])
        self.assertIsNone(logging["score"])

    def test_env_example_not_required_when_no_env_reads(self):
        r = audit({"tool.py": "print(1)"})
        self.assertEqual(check(r, "sec-1")["status"], "n/a")

    def test_env_example_required_when_code_reads_env(self):
        r = audit({"app.py": "import os\nkey = os.environ['API_KEY']\n"})
        self.assertEqual(check(r, "sec-1")["status"], "fail")


class Monorepo(unittest.TestCase):
    def test_workspace_members_contribute_frameworks_and_adapters(self):
        r = audit({
            "package.json": json.dumps({"name": "root", "private": True, "devDependencies": {"turbo": "2"}}),
            "pnpm-workspace.yaml": "packages:\n  - apps/*\n  - packages/*\n",
            "pnpm-lock.yaml": "",
            "apps/web/package.json": json.dumps({"dependencies": {"next": "15", "convex": "1"}, "scripts": {"test": "vitest"}}),
            "apps/web/vercel.json": "{}",
            "packages/backend/convex/schema.ts": "export default {}",
        })
        fp = r["stack_fingerprint"]
        self.assertIn("nextjs", fp["frameworks"])
        self.assertIn("convex", fp["frameworks"])
        self.assertIn("vercel", fp["deploy_surfaces"])
        self.assertIn("nextjs-vercel", fp["adapters_matched"])
        self.assertIn("convex", fp["adapters_matched"])
        self.assertTrue(fp["multi_surface"])
        self.assertEqual(fp["profile"], "web-app")

    def test_worker_dockerfile_in_member_does_not_block_vercel_inference(self):
        r = audit({
            "package.json": json.dumps({"name": "root", "private": True, "workspaces": ["apps/*"]}),
            "package-lock.json": "{}",
            "apps/web/package.json": json.dumps({"dependencies": {"next": "15"}}),
            "apps/worker/package.json": json.dumps({"dependencies": {"fastify": "5"}}),
            "apps/worker/Dockerfile": "FROM node:20",
            "apps/worker/fly.toml": "app = 'worker'",
        })
        fp = r["stack_fingerprint"]
        self.assertIn("fly", fp["deploy_surfaces"])
        self.assertIn("vercel", fp["deploy_surfaces"])
        self.assertTrue(fp["multi_surface"])


class CiDetection(unittest.TestCase):
    def test_unittest_step_counts_as_running_tests(self):
        wf = "on: push\njobs:\n  t:\n    runs-on: ubuntu-latest\n    steps:\n      - run: python -m unittest discover tests\n"
        r = audit({".github/workflows/ci.yml": wf, "tests/test_x.py": "import unittest"})
        self.assertEqual(check(r, "ci-2")["status"], "pass")


if __name__ == "__main__":
    unittest.main()
