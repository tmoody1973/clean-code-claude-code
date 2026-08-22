"""Assemble the categories, apply profile skips, weak-evidence rules, and waivers."""
import re
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from .model import (CHECK_SKIPS_BY_PROFILE, WAIVER_FIELDS, Category, CheckResult,
                    WEAK_PASS_IDS, load_waivers)
from .repo import Repo
from .fingerprint import StackFingerprint, detect_stack_fingerprint
from .checks_build import check_claude_md, check_ci_pipeline, check_test_scripts_defined
from .checks_runtime import (check_multi_surface_deployment, check_resilience_and_runbooks,
                             check_secrets_management, check_structured_logging)
from .checks_access import check_access_control
from .checks_quality import check_dependency_security, check_testing_quality_gates

# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------

CATEGORY_META = [
    ("AI Agent Context", "AI Agent Context",
     "Documentation that lets AI coding agents and human contributors operate "
     "safely and consistently on the codebase.",
     "https://docs.claude.com/en/docs/claude-code/memory"),
    ("Access Control", "Access Control",
     "Who is allowed to do what. Shallow by design: these checks can show a guard is "
     "missing or fails open, never that an authorization model is correct.",
     "https://owasp.org/Top10/A01_2021-Broken_Access_Control/"),
    ("CI/CD Pipeline", "CI/CD Pipeline",
     "Automated build/test/lint gates that block broken code from reaching production.",
     "https://docs.github.com/en/actions/learn-github-actions"),
    ("Structured Logging & Observability", "Structured Logging & Observability",
     "Structured, queryable logs plus error tracking so failures are visible "
     "before a customer reports them.",
     "https://sre.google/sre-book/monitoring-distributed-systems/"),
    ("Secrets & Environment Management", "Secrets & Environment Management",
     "Environment-specific configuration and secrets kept out of source control "
     "and rotated correctly.",
     "https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html"),
    ("Resilience & Failover", "Resilience & Failover",
     "Documented and mechanical safeguards (runbooks, rollback, rate limiting, "
     "migrations) for when something breaks in production.",
     "https://sre.google/sre-book/postmortem-culture/"),
    ("Multi-Surface Deployment & Coordinated Rollback", "Multi-Surface Deployment & Coordinated Rollback",
     "Whether a bad deploy across more than one independently-rollback-able "
     "surface (frontend host, backend/BaaS, database migration step) can be "
     "reverted as one coordinated action instead of desyncing.",
     "https://vercel.com/docs/deployments/rollback-production-deployment"),
    ("Testing & Quality Gates", "Testing & Quality Gates",
     "Automated test coverage and static analysis that catch regressions pre-release.",
     "https://martinfowler.com/testing/"),
    ("Dependency & Supply-chain Security", "Dependency & Supply-chain Security",
     "Reproducible, patchable dependency management.",
     "https://docs.github.com/en/code-security/dependabot"),
]


def guess_profile(repo: Repo, fp: StackFingerprint) -> str:
    """Only pick a lenient profile on a clear signal; otherwise stay strict."""
    pkg = repo.package_json()
    web = {"nextjs", "remix", "sveltekit", "nuxt", "astro"}
    api = {"convex", "express", "fastify", "nestjs", "django", "flask", "fastapi"}
    if web & set(fp.frameworks):
        return "web-app"
    if api & set(fp.frameworks):
        return "api"
    if pkg.get("bin"):
        return "cli"
    if pkg and not fp.deploy_surfaces and not pkg.get("private") and (pkg.get("main") or pkg.get("exports")):
        return "library"
    if re.search(r"\[project\.scripts\]", repo.read("pyproject.toml")):
        return "cli"
    if fp.frameworks or fp.deploy_surfaces:
        return "web-app"  # something deploys or serves; stay strict
    # A language alone (e.g. requirements.txt, package.json with no framework)
    # does not tell us what kind of thing this is. Say so and ask.
    return "unknown"


def run_audit(repo_path: Path, profile: Optional[str] = None) -> tuple[list[Category], StackFingerprint]:
    repo = Repo(repo_path)
    fingerprint = detect_stack_fingerprint(repo)
    if profile:
        fingerprint.profile, fingerprint.profile_source = profile, "given"
    else:
        fingerprint.profile, fingerprint.profile_source = guess_profile(repo, fingerprint), "guessed"
    skips = CHECK_SKIPS_BY_PROFILE[fingerprint.profile]
    waivers, waiver_problems = load_waivers(repo)
    fingerprint.waivers_applied = [{k: w[k] for k in WAIVER_FIELDS} for w in waivers.values()]
    fingerprint.waiver_problems = waiver_problems
    categories = {key: Category(key, title, desc, ref) for key, title, desc, ref in CATEGORY_META}

    categories["AI Agent Context"].checks.append(check_claude_md(repo))
    categories["Access Control"].checks.extend(check_access_control(repo))
    categories["CI/CD Pipeline"].checks.extend(check_ci_pipeline(repo))
    categories["CI/CD Pipeline"].checks.append(check_test_scripts_defined(repo))
    categories["Structured Logging & Observability"].checks.extend(check_structured_logging(repo))
    categories["Secrets & Environment Management"].checks.extend(check_secrets_management(repo))
    categories["Resilience & Failover"].checks.extend(check_resilience_and_runbooks(repo))
    categories["Multi-Surface Deployment & Coordinated Rollback"].checks.extend(
        check_multi_surface_deployment(repo, fingerprint))
    categories["Testing & Quality Gates"].checks.extend(check_testing_quality_gates(repo))
    categories["Dependency & Supply-chain Security"].checks.extend(check_dependency_security(repo))

    for cat in categories.values():
        for c in cat.checks:
            if c.id in WEAK_PASS_IDS and c.status == "pass":
                c.confidence = "weak"
            # Confidence follows evidence. A pass that points at nothing cannot be
            # verified by the reader, so it is a hint no matter which check made it.
            # This catches new checks automatically; WEAK_PASS_IDS never has to be
            # remembered again.
            if c.status == "pass" and not c.evidence:
                c.confidence = "weak"
            w = waivers.get(c.id)
            if w and c.status == "fail":
                c.waived_from = c.status
                c.status, c.confidence = "waived", "verified"
                c.detail = (f"Waived {w['date']} by {w['approved_by']}: {w['reason']} "
                            f"Evidence: {w['evidence']} Original finding: {c.detail}")
                c.recommendation = ""
            if c.id in skips:
                c.status, c.severity = "n/a", "info"
                why = ("Project type not determined; insufficient evidence to apply this check. Re-run with --profile."
                       if fingerprint.profile == "unknown" else f"Not applicable to a {fingerprint.profile} project.")
                c.detail = f"{why} {c.detail}"
                c.recommendation = ""

    return list(categories.values()), fingerprint


