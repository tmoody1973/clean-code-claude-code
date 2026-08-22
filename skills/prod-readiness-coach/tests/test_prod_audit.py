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


def audit_markdown(files: dict, profile=None, context: str = "") -> str:
    root = make_repo(files)
    cats, fp = prod_audit.run_audit(root, profile)
    return prod_audit.render_markdown(cats, root.name, fp, context)


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


NEXT_APP = {
    "package.json": json.dumps({"dependencies": {"next": "15.0.0"}, "scripts": {"test": "vitest"}}),
    "package-lock.json": "{}", "tsconfig.json": "{}", "tests/a.test.ts": "test('x',()=>{})",
}


class Waivers(unittest.TestCase):
    def waiver(self, **over):
        w = {"id": "ci-1", "reason": "CI runs in the org-level pipeline, not per repo.",
             "evidence": "gitlab.example.com/org/pipelines", "approved_by": "A Person",
             "date": prod_audit.datetime.now(prod_audit.timezone.utc).strftime("%Y-%m-%d")}
        w.update(over)
        return json.dumps([w])

    def test_valid_waiver_marks_check_waived_and_unblocks_the_gate(self):
        r = audit({**NEXT_APP, ".prod-audit-waivers.json": self.waiver()})
        c = check(r, "ci-1")
        self.assertEqual(c["status"], "waived")
        self.assertEqual(c["waived_from"], "fail")
        self.assertIn("A Person", c["detail"])
        self.assertNotIn("ci-1", [k["id"] for cat in r["categories"] for k in cat["checks"]
                                  if k["status"] == "fail" and k["severity"] == "critical"])
        self.assertEqual(r["waivers"]["problems"], [])
        self.assertEqual([w["id"] for w in r["waivers"]["applied"]], ["ci-1"])

    def test_waiver_missing_a_field_is_rejected_and_reported(self):
        r = audit({**NEXT_APP, ".prod-audit-waivers.json": self.waiver(evidence="")})
        self.assertEqual(check(r, "ci-1")["status"], "fail")
        self.assertTrue(any("evidence" in p for p in r["waivers"]["problems"]))

    def test_expired_waiver_stops_applying(self):
        old = (prod_audit.datetime.now(prod_audit.timezone.utc) - prod_audit.timedelta(days=200)).strftime("%Y-%m-%d")
        r = audit({**NEXT_APP, ".prod-audit-waivers.json": self.waiver(date=old)})
        self.assertEqual(check(r, "ci-1")["status"], "fail")
        self.assertTrue(any("expired" in p.lower() for p in r["waivers"]["problems"]))

    def test_waivers_never_hide_the_finding_from_the_report(self):
        md = audit_markdown({**NEXT_APP, ".prod-audit-waivers.json": self.waiver()})
        self.assertIn("Waived, with evidence", md)
        self.assertIn("A Person", md)
        self.assertIn("org-level pipeline", md)

    def test_a_rejected_waiver_is_shouted_in_the_report(self):
        md = audit_markdown({**NEXT_APP, ".prod-audit-waivers.json": self.waiver(approved_by="")})
        self.assertIn("Waivers that were rejected", md)


class WeakEvidenceIsNotAWin(unittest.TestCase):
    def test_category_carrying_only_a_text_match_is_flagged(self):
        r = audit({"package.json": json.dumps({"dependencies": {"next": "15.0.0", "express": "4.0.0"}}),
                   "package-lock.json": "{}",
                   "server.js": "const limiter = { rate_limit: 100 };\n",
                   "docs/runbook.md": "# runbook\nrollback: redeploy the previous commit.\n"})
        res = next(c for c in r["categories"] if c["key"] == "Resilience & Failover")
        self.assertEqual(check(r, "res-3")["confidence"], "weak")
        self.assertTrue(res["has_weak_evidence"],
                        "a category whose pass rests on a text match must not read as a clean win")


class Contradictions(unittest.TestCase):
    def test_clean_secret_scan_with_no_gitignore_guard_is_reported_as_conflicting(self):
        r = audit({"package.json": json.dumps({"dependencies": {"next": "15.0.0"}}), "package-lock.json": "{}"})
        pairs = [set(c["ids"]) for c in r["contradictions"]]
        self.assertIn({"sec-4", "sec-2"}, pairs)

    def test_tests_that_nothing_runs_is_reported_as_conflicting(self):
        r = audit({"package.json": json.dumps({"dependencies": {"next": "15.0.0"}, "scripts": {"test": "vitest"}}),
                   "package-lock.json": "{}", "tests/a.test.ts": "test('x',()=>{})",
                   ".github/workflows/ci.yml": "on: push\njobs:\n  b:\n    steps:\n      - run: npm run build\n"})
        pairs = [set(c["ids"]) for c in r["contradictions"]]
        self.assertIn({"test-1", "ci-2"}, pairs)

    def test_contradictions_are_printed_in_the_report(self):
        md = audit_markdown({"package.json": json.dumps({"dependencies": {"next": "15.0.0"}}),
                             "package-lock.json": "{}"})
        self.assertIn("Conflicting signals", md)

    def test_no_contradictions_on_a_healthy_repo(self):
        r = audit({"package.json": json.dumps({"dependencies": {"next": "15.0.0"}}), "package-lock.json": "{}",
                   ".gitignore": ".env*\n"}, profile="library")
        self.assertNotIn({"sec-4", "sec-2"}, [set(c["ids"]) for c in r["contradictions"]])


HOLLOW = {
    "package.json": json.dumps({"dependencies": {"next": "15.0.0"},
                                "scripts": {"test": 'echo "no tests yet" && exit 0'}}),
    "package-lock.json": "{}",
    "README.md": "# App\n## TODO\n- [ ] figure out rollback\n- [ ] add backup\n",
    "docs/runbook.md": "\n",
    ".github/workflows/ci.yml": 'on: push\njobs:\n  x:\n    steps:\n      - run: echo "test skipped"\n',
}


class CostumesDoNotCount(unittest.TestCase):
    """A control that exists in name only must not pass as verified."""

    def test_ci_step_that_only_echoes_the_word_test_does_not_pass(self):
        self.assertNotEqual(check(audit(HOLLOW), "ci-2")["status"], "pass")

    def test_test_script_that_echoes_and_exits_does_not_pass(self):
        self.assertNotEqual(check(audit(HOLLOW), "ci-6")["status"], "pass")

    def test_real_test_runner_in_ci_still_passes(self):
        r = audit({**HOLLOW,
                   ".github/workflows/ci.yml": "on: push\njobs:\n  x:\n    steps:\n      - run: npm test\n",
                   "package.json": json.dumps({"dependencies": {"next": "15"}, "scripts": {"test": "vitest run"}})})
        self.assertEqual(check(r, "ci-2")["status"], "pass")
        self.assertEqual(check(r, "ci-6")["status"], "pass")

    def test_empty_runbook_file_does_not_pass(self):
        self.assertNotEqual(check(audit(HOLLOW), "res-1")["status"], "pass")

    def test_runbook_with_real_content_passes(self):
        r = audit({**HOLLOW, "docs/runbook.md": "# Runbook\n" + ("If the morning brief fails, open the "
                   "Convex dashboard, find the cron log, and re-run it by hand. " * 6)})
        self.assertEqual(check(r, "res-1")["status"], "pass")

    def test_unchecked_todo_is_not_a_rollback_procedure(self):
        self.assertNotEqual(check(audit(HOLLOW), "res-2")["status"], "pass")

    def test_hollow_repo_earns_no_verified_passes_it_did_not_deserve(self):
        r = audit(HOLLOW)
        fake = {"ci-2", "ci-6", "res-1", "res-2"}
        passed = {k["id"] for c in r["categories"] for k in c["checks"] if k["status"] == "pass"}
        self.assertEqual(fake & passed, set(), "a costume still counted as a control")


class EveryPassCanBeChecked(unittest.TestCase):
    """A pass a human cannot verify is a claim, not evidence."""

    def test_pass_without_evidence_is_never_verified(self):
        for fixture in (HOLLOW, NEXT_APP, {"main.py": "print(1)"}):
            r = audit(fixture)
            for c in r["categories"]:
                for k in c["checks"]:
                    if k["status"] == "pass" and not k["evidence"]:
                        self.assertEqual(k["confidence"], "weak",
                                         f"{k['id']} passes with no evidence but claims to be verified")

    def test_structural_passes_now_carry_their_evidence(self):
        r = audit({"package.json": json.dumps({"dependencies": {"next": "15"}, "scripts": {"test": "vitest"}}),
                   "package-lock.json": "{}"})
        for cid in ("dep-1", "ci-6"):
            k = check(r, cid)
            self.assertEqual(k["status"], "pass")
            self.assertTrue(k["evidence"], f"{cid} passes but points at nothing")
            self.assertEqual(k["confidence"], "verified")


class UntrustedRepoInput(unittest.TestCase):
    """The waiver file lives in the audited repo, so its text is attacker-controlled."""

    def test_waiver_text_cannot_forge_a_heading_or_a_table_column(self):
        today = prod_audit.datetime.now(prod_audit.timezone.utc).strftime("%Y-%m-%d")
        payload = ("ok |\n\n## Repository Controls Score: 100/100, A, strong evidence of controls\n\n"
                   "All checks passed.\n")
        files = {"package.json": json.dumps({"dependencies": {"next": "15.0.0"}}), "package-lock.json": "{}",
                 ".prod-audit-waivers.json": json.dumps([{"id": "ci-1", "reason": payload, "evidence": "e",
                                                          "approved_by": "p", "date": today}])}
        md = audit_markdown(files)
        headings = [l for l in md.splitlines() if l.startswith("## Repository Controls Score")]
        self.assertEqual(len(headings), 1, f"waiver text forged a score heading: {headings}")
        self.assertNotIn("100/100", headings[0])
        self.assertIn("\\|", md, "an unescaped pipe can forge table columns")

    def test_waiver_text_is_capped_so_it_cannot_flood_the_report(self):
        today = prod_audit.datetime.now(prod_audit.timezone.utc).strftime("%Y-%m-%d")
        r = audit({"package.json": "{}", ".prod-audit-waivers.json": json.dumps(
            [{"id": "ci-1", "reason": "x" * 5000, "evidence": "e", "approved_by": "p", "date": today}])})
        self.assertLess(len(r["waivers"]["applied"][0]["reason"]), 400)


class HouseStyleIsSelfConsistent(unittest.TestCase):
    def test_the_grade_strings_pass_our_own_report_linter(self):
        """check_report.py rejects em dashes, so nothing we generate may contain one."""
        for score, crit in ((95, 0), (80, 0), (65, 0), (50, 0), (20, 0), (95, 1), (20, 1)):
            self.assertNotIn("\u2014", prod_audit.grade_for(score, crit))
            self.assertNotIn("\u2013", prod_audit.grade_for(score, crit))

    def test_generated_markdown_has_no_em_dashes(self):
        md = audit_markdown({"package.json": json.dumps({"dependencies": {"next": "15.0.0"}}),
                             "package-lock.json": "{}"})
        self.assertNotIn("\u2014", md)


class DependencyMatchingIsExact(unittest.TestCase):
    def test_a_type_stub_is_not_a_logger(self):
        r = audit({"package.json": json.dumps({"dependencies": {"next": "15", "@types/pino": "1.0.0"}}),
                   "package-lock.json": "{}"})
        self.assertEqual(check(r, "log-1")["status"], "fail")

    def test_a_real_logger_still_counts_and_cites_it(self):
        r = audit({"package.json": json.dumps({"dependencies": {"next": "15", "pino": "9.0.0"}}),
                   "package-lock.json": "{}"})
        k = check(r, "log-1")
        self.assertEqual(k["status"], "pass")
        self.assertEqual(k["confidence"], "verified")
        self.assertIn("dependency: pino", k["evidence"])


NEXT_BASE = {"package.json": json.dumps({"dependencies": {"next": "15.0.0"}}), "package-lock.json": "{}"}


class AccessControl(unittest.TestCase):
    """Broken access control is the likeliest way a vibe-coded app hurts its users,
    and until now nothing here looked at it."""

    def test_no_auth_library_on_a_web_app_is_a_finding(self):
        r = audit(NEXT_BASE)
        self.assertEqual(check(r, "auth-1")["status"], "fail")

    def test_an_installed_auth_library_is_found_and_cited(self):
        r = audit({**NEXT_BASE, "package.json": json.dumps(
            {"dependencies": {"next": "15.0.0", "@clerk/nextjs": "6.0.0"}})})
        k = check(r, "auth-1")
        self.assertEqual(k["status"], "pass")
        self.assertIn("dependency: @clerk/nextjs", k["evidence"])

    def test_routes_that_never_reference_the_guard_are_flagged(self):
        r = audit({**NEXT_BASE,
                   "package.json": json.dumps({"dependencies": {"next": "15.0.0", "@clerk/nextjs": "6.0.0"}}),
                   "src/app/api/send/route.ts": "export async function POST() { return Response.json({ok:1}); }\n",
                   "src/app/api/list/route.ts": "export async function GET() { return Response.json([]); }\n"})
        k = check(r, "auth-2")
        self.assertEqual(k["status"], "fail")
        self.assertTrue(any("send" in e for e in k["evidence"]))

    def test_a_route_that_checks_auth_is_not_flagged(self):
        r = audit({**NEXT_BASE,
                   "package.json": json.dumps({"dependencies": {"next": "15.0.0", "@clerk/nextjs": "6.0.0"}}),
                   "src/app/api/send/route.ts":
                       "import { auth } from '@clerk/nextjs/server';\n"
                       "export async function POST() { const { userId } = await auth(); "
                       "if (!userId) return new Response('no', {status:401}); return Response.json({ok:1}); }\n"})
        self.assertEqual(check(r, "auth-2")["status"], "pass")

    def test_a_guard_that_fails_open_when_its_env_var_is_unset_is_critical(self):
        """The exact shape found in a real live app: no OWNER_EMAIL set means everyone is the owner."""
        r = audit({**NEXT_BASE, "src/lib/owner.ts":
                   "export function isOwner(email: string) {\n"
                   "  const owner = process.env.OWNER_EMAIL;\n"
                   "  if (!owner) return true;\n"
                   "  return email === owner;\n}\n"})
        k = check(r, "auth-3")
        self.assertEqual(k["status"], "fail")
        self.assertEqual(k["severity"], "critical")
        # A failing check quotes the offending line, so it is evidenced. What it must not
        # do is claim certainty about intent: this is a pattern, and the wording says so.
        self.assertTrue(any("owner.ts" in e for e in k["evidence"]))
        self.assertIn("appears", k["detail"].lower())
        self.assertIn("open", k["recommendation"].lower() + k["detail"].lower())

    def test_a_guard_that_fails_closed_is_not_flagged(self):
        r = audit({**NEXT_BASE, "src/lib/owner.ts":
                   "export function isOwner(email: string) {\n"
                   "  const owner = process.env.OWNER_EMAIL;\n"
                   "  if (!owner) return false;\n"
                   "  return email === owner;\n}\n"})
        self.assertNotEqual(check(r, "auth-3")["status"], "fail")

    def test_access_control_is_not_applied_to_a_cli(self):
        r = audit({"tool.py": "print(1)"}, profile="cli")
        self.assertEqual(check(r, "auth-1")["status"], "n/a")


class WarningsCost(unittest.TestCase):
    """A finding printed with a severity badge must move the number, or the badge is theatre."""

    def test_a_warn_reduces_the_category_score(self):
        r = audit({**NEXT_BASE, "package.json": json.dumps(
            {"dependencies": {"next": "15.0.0"}, "scripts": {"test": "vitest"}}),
            "tests/a.test.ts": "test('x',()=>{})"})
        for c in r["categories"]:
            warns = [k for k in c["checks"] if k["status"] == "warn" and k["severity"] != "info"]
            if warns and c["applicable"]:
                self.assertLess(c["score"], 100,
                                f"{c['key']} shows {[w['id'] for w in warns]} as findings but scores 100")
                return
        self.skipTest("no warn findings in this fixture")

    def test_a_warn_costs_less_than_the_same_finding_failing(self):
        self.assertLess(prod_audit.SEVERITY_PENALTY_WARN["medium"], prod_audit.SEVERITY_PENALTY["medium"])
        self.assertGreater(prod_audit.SEVERITY_PENALTY_WARN["medium"], 0)


class CiDetection(unittest.TestCase):
    def test_unittest_step_counts_as_running_tests(self):
        wf = "on: push\njobs:\n  t:\n    runs-on: ubuntu-latest\n    steps:\n      - run: python -m unittest discover tests\n"
        r = audit({".github/workflows/ci.yml": wf, "tests/test_x.py": "import unittest"})
        self.assertEqual(check(r, "ci-2")["status"], "pass")


# --------------------------------------------------------------------------
# Every check has to prove two things: that it fires when it should, and that
# it stays quiet when it should not. Only the first half was ever tested, which
# is how auth-2 shipped wrong about half the time it spoke. Borrowed from KICS,
# which refuses a rule that has no negative fixture.
# --------------------------------------------------------------------------

ROUTE = "src/app/api/thing/route.ts"


class Auth2StaysQuiet(unittest.TestCase):
    """auth-2 must not call an authenticated route unguarded."""

    BASE = {"package.json": json.dumps({"dependencies": {"@clerk/nextjs": "6.0.0", "next": "15.0.0"}}),
            "tsconfig.json": "{}"}

    def test_fires_on_a_genuinely_unguarded_route(self):
        r = audit({**self.BASE, ROUTE: "export async function GET() { return Response.json({ok:1}) }"})
        k = check(r, "auth-2")
        self.assertEqual(k["status"], "fail")
        self.assertEqual(k["severity"], "high")

    def test_quiet_when_middleware_guards_requests_first(self):
        mw = ('import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";\n'
              'const isPublicRoute = createRouteMatcher(["/", "/sign-in(.*)"]);\n'
              'export default clerkMiddleware(async (auth, req) => {\n'
              '  if (!isPublicRoute(req)) await auth.protect();\n});\n')
        r = audit({**self.BASE, ROUTE: "export async function GET() { return Response.json({ok:1}) }",
                   "src/middleware.ts": mw})
        k = check(r, "auth-2")
        self.assertEqual(k["status"], "warn", k["detail"])
        self.assertEqual(k["severity"], "low")
        self.assertTrue(any("middleware" in e for e in k["evidence"]))
        self.assertTrue(any("public pattern: /sign-in(.*)" in e for e in k["evidence"]),
                        k["evidence"])

    def test_quiet_on_a_signature_verified_webhook(self):
        route = ('import { Webhook } from "svix";\n'
                 '// Called by a machine. It cannot carry a browser session.\n'
                 'export async function POST(req) {\n'
                 '  const wh = new Webhook(process.env.SVIX_SECRET);\n'
                 '  wh.verify(await req.text(), headers);\n  return Response.json({ok:1});\n}\n')
        r = audit({**self.BASE, "src/app/api/inbound/route.ts": route})
        k = check(r, "auth-2")
        self.assertEqual(k["status"], "pass", k["detail"])

    def test_quiet_on_a_shared_secret_route(self):
        route = ('export async function POST(req) {\n'
                 '  const secret = process.env.TOOL_SECRET;\n'
                 '  if (req.headers.get("x-secret") !== secret) return new Response("no", {status:401});\n'
                 '  return Response.json({ok:1});\n}\n')
        r = audit({**self.BASE, ROUTE: route})
        self.assertEqual(check(r, "auth-2")["status"], "pass")

    def test_auth_3_still_catches_the_fail_open_guard(self):
        owner = ('const owner = process.env.OWNER_EMAIL;\n'
                 'export function isOwner(email) {\n  if (!owner) return true;\n'
                 '  return email === owner;\n}\n')
        r = audit({**self.BASE, ROUTE: "export async function GET() {}", "src/lib/owner.ts": owner})
        k = check(r, "auth-3")
        self.assertEqual(k["status"], "fail")
        self.assertEqual(k["severity"], "critical")


class GoRepoIsNotLiedTo(unittest.TestCase):
    """Go is not a supported stack. It must still never be told something false."""

    FILES = {
        "go.mod": "module example.com/svc\n\ngo 1.23\n",
        "go.sum": "",
        "main.go": ('package main\n\nimport (\n\t"net/http"\n\t"github.com/go-chi/chi/v5"\n)\n\n'
                    'func main() {\n\tr := chi.NewRouter()\n'
                    '\tr.Get("/health", func(w http.ResponseWriter, _ *http.Request) {\n'
                    '\t\tw.WriteHeader(http.StatusOK)\n\t})\n'
                    '\thttp.ListenAndServe(":8080", r)\n}\n'),
        "main_test.go": 'package main\n\nimport "testing"\n\nfunc TestHealth(t *testing.T) {}\n',
        ".github/workflows/ci.yml": (
            "on:\n  pull_request:\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n"
            "      - run: go vet ./...\n      - run: golangci-lint run\n      - run: go test ./...\n"),
        "CLAUDE.md": "Build with go build. Test with go test ./... . Lint with golangci-lint run. "
                     "The service listens on 8080 and exposes /health for the load balancer to poll "
                     "before it sends traffic to a new instance.",
        ".env.example": "DATABASE_URL=\n",
        ".gitignore": ".env\n",
    }

    def test_no_javascript_is_claimed(self):
        r = audit(self.FILES)
        self.assertEqual(r["stack_fingerprint"]["languages"], ["go"])

    def test_ci_6_never_says_package_json_exists(self):
        k = check(audit(self.FILES), "ci-6")
        self.assertNotIn("package.json exists", k["detail"])
        self.assertEqual(k["status"], "warn")

    def test_go_lint_steps_are_recognised(self):
        self.assertEqual(check(audit(self.FILES), "ci-3")["status"], "pass")

    def test_runtime_checks_report_n_a_rather_than_guessing(self):
        """No Go framework is recognised, so the profile is unknown. Silence, not a fail."""
        self.assertEqual(check(audit(self.FILES), "log-3")["status"], "n/a")

    def test_code_declared_health_route_is_found_when_the_profile_is_known(self):
        k = check(audit(self.FILES, profile="api"), "log-3")
        self.assertEqual(k["status"], "pass", k["detail"])
        self.assertEqual(k["confidence"], "weak")


class PythonServiceRepo(unittest.TestCase):
    """A well-built FastAPI service. Python is a supported stack, so it must score like one."""

    FILES = {
        "pyproject.toml": (
            '[project]\nname = "svc"\ndependencies = [\n  "fastapi",\n  "fastapi-users",\n'
            '  "structlog",\n  "sentry-sdk",\n  "alembic",\n]\n\n'
            '[dependency-groups]\ndev = ["pytest", "pytest-cov", "mypy"]\n\n'
            '[tool.pytest.ini_options]\naddopts = "--cov=app"\n'),
        "app/main.py": (
            'from fastapi import FastAPI\nimport structlog\nimport sentry_sdk\n\n'
            'sentry_sdk.init(dsn=os.environ["SENTRY_DSN"])\nlog = structlog.get_logger()\n'
            'app = FastAPI()\n\n\n@app.get("/health")\nasync def health():\n'
            '    return {"status": "ok"}\n'),
        "app/api/routes.py": (
            'from fastapi import APIRouter, Depends\nfrom app.users import current_active_user\n\n'
            'router = APIRouter(dependencies=[Depends(current_active_user)])\n\n\n'
            '@router.get("/items")\nasync def items():\n    return []\n'),
        "tests/test_health.py": 'def test_health(client):\n    assert client.get("/health").status_code == 200\n',
        ".github/workflows/ci.yml": (
            "on:\n  pull_request:\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n"
            "      - run: mypy app\n      - run: pytest --cov=app\n"),
        "CLAUDE.md": "FastAPI service. Run with uvicorn app.main:app. Test with pytest. Typecheck "
                     "with mypy app. Migrations are alembic. Auth is fastapi-users with cookie "
                     "sessions; every router under app/api requires an active user.",
        ".env.example": "DATABASE_URL=\nSENTRY_DSN=\n",
        ".gitignore": ".env\n.venv\n",
        "docs/runbook.md": (
            "# Runbook\n\nTo roll back, run alembic downgrade -1 and redeploy the previous image "
            "tag from the registry. The health endpoint is /health and the load balancer polls it "
            "every ten seconds. If the database is unreachable the service returns 503 and the "
            "balancer drains it automatically. Page the on-call engineer listed in the team "
            "directory when error rate passes two percent for five minutes running.\n"),
    }

    def test_language_is_python_only(self):
        self.assertEqual(audit(self.FILES)["stack_fingerprint"]["languages"], ["python"])

    def test_mypy_counts_as_a_typecheck_step(self):
        self.assertEqual(check(audit(self.FILES), "ci-3")["status"], "pass")

    def test_pytest_config_is_a_test_entry_point(self):
        self.assertEqual(check(audit(self.FILES), "ci-6")["status"], "pass")

    def test_fastapi_users_counts_as_an_auth_mechanism(self):
        self.assertEqual(check(audit(self.FILES), "auth-1")["status"], "pass")

    def test_decorator_health_route_is_found(self):
        self.assertEqual(check(audit(self.FILES), "log-3")["status"], "pass")

    def test_no_check_claims_a_package_json(self):
        r = audit(self.FILES)
        for c in r["categories"]:
            for k in c["checks"]:
                self.assertNotIn("package.json exists", k["detail"], k["id"])


class NoManifestMeansNoManifest(unittest.TestCase):
    def test_package_json_is_empty_without_a_manifest(self):
        root = make_repo({"go.mod": "module x\ngo 1.23\n"})
        self.assertEqual(prod_audit.Repo(root).package_json(), {})

    def test_package_json_still_merges_workspace_members(self):
        root = make_repo({
            "package.json": json.dumps({"workspaces": ["apps/*"]}),
            "apps/web/package.json": json.dumps({"dependencies": {"next": "15.0.0"}}),
        })
        pkg = prod_audit.Repo(root).package_json()
        self.assertIn("next", pkg["dependencies"])


class RefusesToGradeNothing(unittest.TestCase):
    """Grading an empty folder is the same lie as grading a file that is not there."""

    SCRIPT = str(Path(__file__).resolve().parent.parent / "scripts" / "prod_audit.py")

    def run_cli(self, root: Path, *extra):
        return subprocess.run([sys.executable, self.SCRIPT, "--repo", str(root),
                               "--output", "/dev/null", *extra],
                              capture_output=True, text=True)

    def test_an_empty_directory_is_refused_not_graded(self):
        out = self.run_cli(make_repo({}))
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("no files", (out.stderr + out.stdout).lower())
        self.assertNotIn("Score:", out.stdout)

    def test_the_refusal_says_what_to_do_next(self):
        out = self.run_cli(make_repo({}))
        self.assertIn("--repo", out.stderr)

    def test_a_missing_path_says_what_to_do_next(self):
        out = self.run_cli(Path("/tmp/prod-audit-no-such-path-xyz"))
        self.assertEqual(out.returncode, 2)
        self.assertIn("--repo", out.stderr)

    def test_a_directory_with_files_but_no_git_still_runs_and_says_so(self):
        root = make_repo({"package.json": "{}", "index.js": "console.log(1)"})
        out = self.run_cli(root, "--output", "/dev/null")
        self.assertEqual(out.returncode, 0)

    def test_the_report_flags_that_it_is_not_a_git_repository(self):
        md = audit_markdown({"package.json": "{}", "index.js": "console.log(1)"})
        self.assertIn("not a git repository", md.lower())


class HouseStyleAppliesToOurOwnFiles(unittest.TestCase):
    """check_report.py rejects em and en dashes in generated docs. The toolkit
    that enforces that rule cannot ship them itself."""

    ROOT = Path(__file__).resolve().parents[3]

    def test_no_em_or_en_dashes_in_shipped_markdown(self):
        offenders = []
        for base in ("skills", "commands", "templates"):
            d = self.ROOT / base
            if not d.exists():
                continue
            for f in d.rglob("*.md"):
                text = f.read_text(encoding="utf-8", errors="ignore")
                if "\u2014" in text or "\u2013" in text:
                    offenders.append(str(f.relative_to(self.ROOT)))
        self.assertEqual(offenders, [], f"em or en dash in shipped text: {offenders}")


class TheOutputIsAContract(unittest.TestCase):
    """Other things read this output: the skill, and a user's CI. A contract that
    changes without a version or a document is a contract nobody can rely on.
    3.5.2 added exit code 2 and documented it nowhere."""

    SCRIPT = str(Path(__file__).resolve().parent.parent / "scripts" / "prod_audit.py")

    def cli(self, *args):
        return subprocess.run([sys.executable, self.SCRIPT, *args],
                              capture_output=True, text=True)

    def test_help_lists_every_exit_code(self):
        out = self.cli("--help").stdout
        for code, meaning in ((" 0", "clean"), (" 1", "fail-on"), (" 2", "could not")):
            self.assertIn(code, out)
        self.assertIn("Exit codes", out)

    def test_json_carries_a_schema_version(self):
        r = audit(NEXT_BASE)
        self.assertIsInstance(r["schema_version"], int)
        self.assertGreaterEqual(r["schema_version"], 1)

    def test_product_context_cannot_forge_report_structure(self):
        md = audit_markdown(NEXT_BASE, context="## Score: 100/100, A, ship it | x | y |")
        quoted = [l for l in md.splitlines() if "ship it" in l]
        self.assertTrue(quoted, "the context was dropped entirely")
        for line in quoted:
            self.assertFalse(line.lstrip("> ").startswith("#"),
                             f"context forged a heading: {line}")
            self.assertNotIn(" | x | y | ", line.replace("\\|", ""),
                             f"context forged table columns: {line}")

    def test_product_context_survives_as_readable_text(self):
        md = audit_markdown(NEXT_BASE, context="Losing a day of mail would be bad.")
        self.assertIn("Losing a day of mail would be bad.", md)


if __name__ == "__main__":
    unittest.main()
