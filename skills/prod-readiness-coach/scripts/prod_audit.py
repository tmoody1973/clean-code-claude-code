#!/usr/bin/env python3
"""
prod_audit.py — Production-Readiness Audit Tool
==================================================

Scans a project repository for essential production-readiness configuration
and generates a Markdown + JSON report of missing configuration and
potential failure points, benchmarked against industry best practices:

  - The Twelve-Factor App               https://12factor.net/
  - OWASP Secrets Management Cheat Sheet https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html
  - Google SRE Book (Monitoring/Postmortems) https://sre.google/sre-book/table-of-contents/
  - GitHub Actions CI best practices     https://docs.github.com/en/actions/learn-github-actions
  - Sentry / OpenTelemetry observability docs

Usage
-----
    python3 prod_audit.py --repo /path/to/project [--output report.md] [--json report.json]

No third-party dependencies — stdlib only. Works on any git repo
(Node/Next.js, Python, Go, etc.) via language-agnostic pattern detection.

The tool is intentionally file-based (static analysis of the working tree +
`git ls-files`), so it works without cloning credentials beyond a local
checkout, and is safe to run in CI as a pre-release gate:

    python3 prod_audit.py --repo . --fail-on critical

Exit code is non-zero when --fail-on threshold is met, so it can block a
pipeline on missing production-readiness configuration.
"""

from __future__ import annotations

import sys as _sys
if _sys.version_info < (3, 9):
    _sys.stderr.write("prod_audit.py needs Python 3.9 or newer (found %d.%d).\n" % _sys.version_info[:2])
    _sys.exit(2)

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

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


# Checks whose pass is based on a text search, not a structural check.
WEAK_PASS_IDS = {"log-4", "res-3", "sec-4"}

# What kind of thing the repo is. A check that does not apply to the profile
# is reported as "n/a" and left out of the score. When the guess is unsure
# we pick the stricter profile (web-app): a false failure is cheaper than a
# skipped real check.
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
    def applicable(self) -> bool:
        return any(c.status != "n/a" for c in self.checks)

    @property
    def blocking_count(self) -> int:
        return sum(1 for c in self.checks if c.status == "fail" and c.severity == "critical")


# --------------------------------------------------------------------------
# Repo scanning helpers
# --------------------------------------------------------------------------

DEFAULT_EXCLUDE_DIRS = {
    ".git", "node_modules", ".next", "dist", "build", "out", "coverage",
    ".venv", "venv", "__pycache__", ".pnpm", ".turbo", ".vercel", "vendor",
    ".cache", "target", ".idea", ".vscode",
}

CODE_EXTS = {
    ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py", ".go", ".rb",
    ".java", ".kt", ".rs", ".php", ".cs",
}
# Secrets live in config as often as in code, so the secret scan covers more.
SECRET_SCAN_EXTS = CODE_EXTS | {
    ".yaml", ".yml", ".json", ".toml", ".env", ".sh", ".tf", ".ini", ".cfg", ".properties",
}
COMMENT_LINE_RX = re.compile(r"^\s*(#|//|/\*|\*|<!--|--)")


class Repo:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self._git_files: Optional[list[str]] = None

    def is_git_repo(self) -> bool:
        return (self.root / ".git").exists()

    def git_files(self) -> list[str]:
        """Files tracked by git (preferred — respects .gitignore automatically)."""
        if self._git_files is not None:
            return self._git_files
        if self.is_git_repo():
            try:
                out = subprocess.run(
                    ["git", "-C", str(self.root), "ls-files"],
                    capture_output=True, text=True, timeout=30, check=True,
                )
                self._git_files = [l for l in out.stdout.splitlines() if l.strip()]
                return self._git_files
            except Exception:
                pass
        # Fallback: walk filesystem excluding common junk dirs.
        files = []
        for p in self.root.rglob("*"):
            if p.is_dir():
                continue
            if any(part in DEFAULT_EXCLUDE_DIRS for part in p.parts):
                continue
            files.append(str(p.relative_to(self.root)))
        self._git_files = files
        return self._git_files

    def untracked_files(self) -> list[str]:
        """Untracked, non-ignored files. Empty when not a git repo (walk already covers them)."""
        if not self.is_git_repo():
            return []
        try:
            out = subprocess.run(
                ["git", "-C", str(self.root), "ls-files", "--others", "--exclude-standard"],
                capture_output=True, text=True, timeout=30, check=True,
            )
            return [l for l in out.stdout.splitlines() if l.strip()]
        except Exception:
            return []

    def exists(self, *candidates: str) -> Optional[str]:
        """Return the first candidate path (relative) that exists on disk, else None."""
        for c in candidates:
            if (self.root / c).exists():
                return c
        return None

    def glob(self, pattern: str) -> list[str]:
        """Glob within tracked files (case-sensitive fnmatch), pattern uses '**' for recursion."""
        matches = []
        for f in self.git_files():
            if fnmatch.fnmatch(f, pattern) or fnmatch.fnmatch("/" + f, pattern):
                matches.append(f)
        return matches

    def find_any(self, patterns: list[str]) -> list[str]:
        found = []
        for pat in patterns:
            found.extend(self.glob(pat))
        return sorted(set(found))

    def read(self, relpath: str, max_bytes: int = 200_000) -> str:
        try:
            p = self.root / relpath
            # Never follow a symlink out of the repository. A cloned repo is
            # untrusted input; a link named config.env could point at ~/.aws.
            if not p.resolve().is_relative_to(self.root.resolve()):
                return ""
            data = p.read_bytes()[:max_bytes]
            return data.decode("utf-8", errors="ignore")
        except Exception:
            return ""

    def grep(self, pattern: str, paths: Optional[list[str]] = None, flags=re.IGNORECASE,
             skip_comments: bool = True, with_lineno: bool = False) -> list:
        """Return (file, matching line) for regex pattern across given files (or all code files).
        Comment lines are skipped by default so a TODO never counts as an implementation."""
        rx = re.compile(pattern, flags)
        hits = []
        target_files = paths if paths is not None else [
            f for f in self.git_files() if Path(f).suffix in CODE_EXTS
        ]
        for f in target_files:
            content = self.read(f)
            if not content:
                continue
            for lineno, line in enumerate(content.splitlines(), 1):
                if skip_comments and COMMENT_LINE_RX.match(line):
                    continue
                if rx.search(line):
                    hits.append((f, line.strip()[:160]) if not with_lineno else (f, lineno, line))
        return hits

    def package_json(self) -> dict:
        for candidate in ("package.json",):
            if (self.root / candidate).exists():
                try:
                    return json.loads(self.read(candidate))
                except Exception:
                    return {}
        return {}

    def requirements_text(self) -> str:
        parts = []
        for f in ("requirements.txt", "pyproject.toml", "Pipfile"):
            if (self.root / f).exists():
                parts.append(self.read(f))
        return "\n".join(parts)


# --------------------------------------------------------------------------
# Stack fingerprinting — deterministic detection of runtime/framework/deploy
# signals from manifests and deploy configs. This is what lets the skill
# layer load only the reference adapter file(s) relevant to THIS repo
# (progressive disclosure) instead of hardcoding stack-specific advice into
# one generic prompt. Two runs on the same commit must produce the same
# fingerprint — no LLM involvement here.
# --------------------------------------------------------------------------

@dataclass
class StackFingerprint:
    languages: list[str] = field(default_factory=list)
    package_managers: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    deploy_surfaces: list[str] = field(default_factory=list)
    deploy_evidence: dict[str, list[str]] = field(default_factory=dict)
    runtimes: list[str] = field(default_factory=list)
    migration_tooling: list[str] = field(default_factory=list)
    profile: str = "web-app"
    profile_source: str = "default"  # "given" | "guessed" | "default"
    multi_surface: bool = False
    multi_surface_evidence: list[str] = field(default_factory=list)
    adapters_matched: list[str] = field(default_factory=list)

    def add_surface(self, name: str, evidence: str) -> None:
        if name not in self.deploy_surfaces:
            self.deploy_surfaces.append(name)
        self.deploy_evidence.setdefault(name, [])
        if evidence not in self.deploy_evidence[name]:
            self.deploy_evidence[name].append(evidence)


def parse_compose_services(content: str) -> dict[str, str]:
    """Lightweight, stdlib-only extraction of top-level service blocks from a
    docker-compose file. Not a full YAML parser — deliberately heuristic and
    indentation-based, which is sufficient for the standard 2-space-indented
    `services:` block every compose file uses, and keeps this tool dependency-free.
    """
    services: dict[str, str] = {}
    lines = content.splitlines()
    in_services = False
    current: Optional[str] = None
    buf: list[str] = []
    for line in lines:
        if re.match(r"^services:\s*$", line):
            in_services = True
            continue
        if not in_services:
            continue
        if re.match(r"^\S", line):  # dedented back to top-level key — services block ended
            if current:
                services[current] = "\n".join(buf)
            break
        m = re.match(r"^  ([\w.-]+):\s*$", line)
        if m:
            if current:
                services[current] = "\n".join(buf)
            current = m.group(1)
            buf = []
        elif current is not None:
            buf.append(line)
    if current:
        services[current] = "\n".join(buf)
    return services


def detect_stack_fingerprint(repo: Repo) -> StackFingerprint:
    fp = StackFingerprint()
    pkg = repo.package_json()
    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

    # --- Languages & package managers -------------------------------------
    if pkg:
        fp.languages.append("typescript" if repo.exists("tsconfig.json") else "javascript")
        if repo.exists("bun.lock", "bun.lockb") or pkg.get("packageManager", "").startswith("bun"):
            fp.package_managers.append("bun")
        elif repo.exists("pnpm-lock.yaml"):
            fp.package_managers.append("pnpm")
        elif repo.exists("yarn.lock"):
            fp.package_managers.append("yarn")
        elif repo.exists("package-lock.json"):
            fp.package_managers.append("npm")
    if repo.requirements_text() or repo.exists("requirements.txt", "pyproject.toml", "Pipfile"):
        fp.languages.append("python")
        fp.package_managers.append("pip" if repo.exists("requirements.txt") else "poetry/pipenv")
    if repo.exists("go.mod"):
        fp.languages.append("go")
        fp.package_managers.append("go modules")

    # --- Frameworks ---------------------------------------------------------
    framework_deps = {
        "next": "nextjs", "convex": "convex", "@remix-run/dev": "remix",
        "express": "express", "fastify": "fastify", "@sveltejs/kit": "sveltekit",
        "nuxt": "nuxt", "@nestjs/core": "nestjs", "astro": "astro",
    }
    for dep_name, fw in framework_deps.items():
        if dep_name in deps:
            fp.frameworks.append(fw)
    req_text = repo.requirements_text().lower()
    for needle, fw in (("django", "django"), ("flask", "flask"), ("fastapi", "fastapi")):
        if needle in req_text:
            fp.frameworks.append(fw)

    # --- Deploy surfaces ------------------------------------------------
    if repo.exists("vercel.json") or repo.exists(".vercel") or "vercel-build" in pkg.get("scripts", {}):
        fp.add_surface("vercel", repo.exists("vercel.json", ".vercel") or "package.json scripts.vercel-build")
    if repo.exists("netlify.toml"):
        fp.add_surface("netlify", "netlify.toml")
    if repo.exists("fly.toml"):
        fp.add_surface("fly", "fly.toml")
    if repo.exists("wrangler.toml", "wrangler.jsonc", "wrangler.json"):
        fp.add_surface("cloudflare-workers", repo.exists("wrangler.toml", "wrangler.jsonc", "wrangler.json"))
    if repo.exists("render.yaml"):
        fp.add_surface("render", "render.yaml")
    if repo.exists("Procfile"):
        fp.add_surface("heroku", "Procfile")
    dockerfiles = repo.find_any(["**/Dockerfile", "Dockerfile"])
    compose_files = repo.find_any(["docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"])
    if dockerfiles or compose_files:
        fp.add_surface("docker", ", ".join(dockerfiles[:3] + compose_files[:2]))
    if "convex" in fp.frameworks or repo.exists("convex/schema.ts", "convex/schema.js"):
        fp.add_surface("convex", "convex/ directory or convex dependency")

    # --- Runtimes -------------------------------------------------------
    if "convex" in fp.frameworks:
        fp.runtimes.append("convex-v8-isolate")
        if repo.grep(r'^[\'"]use node[\'"]', paths=repo.find_any(["convex/**/*.ts", "convex/**/*.js"])):
            fp.runtimes.append("convex-node")
    if "cloudflare-workers" in fp.deploy_surfaces:
        fp.runtimes.append("cloudflare-v8-isolate")
    if "nextjs" in fp.frameworks:
        fp.runtimes.append("node")
        if repo.grep(r"runtime\s*[:=]\s*['\"]edge['\"]") or repo.exists("middleware.ts", "middleware.js"):
            fp.runtimes.append("edge")
    if "python" in fp.languages:
        fp.runtimes.append("python")

    # --- Migration tooling ------------------------------------------------
    if repo.find_any(["prisma/migrations/*"]):
        fp.migration_tooling.append("prisma")
    if repo.exists("drizzle.config.ts", "drizzle.config.js") or repo.find_any(["drizzle/*", "**/drizzle/*"]):
        fp.migration_tooling.append("drizzle")
    if repo.find_any(["alembic/versions/*"]):
        fp.migration_tooling.append("alembic")
    if repo.find_any(["db/migrate/*"]):
        fp.migration_tooling.append("rails-migrations")
    if repo.exists("convex/schema.ts", "convex/schema.js"):
        fp.migration_tooling.append("convex-schema")

    # --- Multi-surface detection ------------------------------------------
    # Most Next.js apps on Vercel have no vercel.json. If Next.js is present and
    # no other frontend host was detected, assume Vercel (flagged as inferred).
    if "nextjs" in fp.frameworks and not any(
            sfc in fp.deploy_surfaces for sfc in ("vercel", "netlify", "fly", "cloudflare-workers", "render", "heroku", "docker")):
        fp.add_surface("vercel", "inferred: Next.js with no other deploy config (confirm)")

    independently_deployable = {"vercel", "netlify", "fly", "cloudflare-workers", "render", "heroku", "convex"}
    matched_platforms = [s for s in fp.deploy_surfaces if s in independently_deployable]
    if len(matched_platforms) >= 2:
        fp.multi_surface = True
        fp.multi_surface_evidence.append(
            f"Multiple independently-deployable platforms detected: {', '.join(sorted(matched_platforms))}. "
            "These deploy and roll back on separate timelines."
        )
    for cf in compose_files:
        content = repo.read(cf)
        services = parse_compose_services(content)
        migrate_services = [s for s, block in services.items()
                             if re.search(r"migrat", s, re.IGNORECASE) or re.search(r"migrat", block, re.IGNORECASE)]
        app_services = [s for s in services if s not in migrate_services]
        if migrate_services and app_services:
            fp.multi_surface = True
            fp.multi_surface_evidence.append(
                f"{cf}: dedicated migration service(s) {migrate_services} run alongside "
                f"{len(app_services)} app/data service(s) ({', '.join(app_services[:6])}). "
                "A bad deploy needs the app rolled back AND the migration's effects accounted for."
            )

    # --- Adapter matching (progressive disclosure) -------------------------
    if "vercel" in fp.deploy_surfaces and "nextjs" in fp.frameworks:
        fp.adapters_matched.append("nextjs-vercel")
    if "convex" in fp.deploy_surfaces:
        fp.adapters_matched.append("convex")
    if "fly" in fp.deploy_surfaces:
        fp.adapters_matched.append("fly")
    if "cloudflare-workers" in fp.deploy_surfaces:
        fp.adapters_matched.append("cloudflare-workers")
    if "netlify" in fp.deploy_surfaces:
        fp.adapters_matched.append("netlify")

    fp.languages = sorted(set(fp.languages))
    fp.package_managers = sorted(set(fp.package_managers))
    fp.frameworks = sorted(set(fp.frameworks))
    fp.runtimes = sorted(set(fp.runtimes))
    fp.migration_tooling = sorted(set(fp.migration_tooling))
    return fp


# --------------------------------------------------------------------------
# Individual checks — each returns a CheckResult
# --------------------------------------------------------------------------

def check_claude_md(repo: Repo) -> CheckResult:
    path = repo.exists("CLAUDE.md", "AGENTS.md")
    ref = "https://docs.claude.com/en/docs/claude-code/memory"
    if not path:
        return CheckResult(
            "agent-1", "AI Agent Context", "CLAUDE.md / AGENTS.md present",
            "fail", "high",
            "No CLAUDE.md or AGENTS.md found at the repository root.",
            "Add a CLAUDE.md (or AGENTS.md) documenting build/test/lint commands, architecture "
            "conventions, and guardrails so AI coding agents (and new engineers) "
            "operate consistently instead of re-deriving project context every session.",
            best_practice_ref=ref,
        )
    content = repo.read(path).strip()
    # A CLAUDE.md that only delegates (e.g. "@AGENTS.md") is valid but should
    # be flagged as info so the auditor knows to check the delegate target too.
    delegate_match = re.match(r"^@([\w./-]+\.md)\s*$", content)
    if delegate_match:
        target = delegate_match.group(1)
        target_exists = repo.exists(target)
        if target_exists:
            return CheckResult(
                "agent-1", "AI Agent Context", "CLAUDE.md / AGENTS.md present",
                "pass", "info",
                f"{path} delegates to {target}, which exists.",
                evidence=[path, target],
                best_practice_ref=ref,
            )
        return CheckResult(
            "agent-1", "AI Agent Context", "CLAUDE.md / AGENTS.md present",
            "fail", "medium",
            f"{path} delegates to {target}, but that file was not found.",
            f"Create {target} or point CLAUDE.md at an existing file.",
            evidence=[path],
            best_practice_ref=ref,
        )
    word_count = len(content.split())
    if word_count < 30:
        return CheckResult(
            "agent-1", "AI Agent Context", "CLAUDE.md / AGENTS.md present",
            "warn", "low",
            f"{path} exists but is very short ({word_count} words) — may be a stub.",
            "Expand CLAUDE.md with commands (build/test/lint/deploy), directory "
            "map, and any non-obvious conventions or footguns.",
            evidence=[path],
            best_practice_ref=ref,
        )
    return CheckResult(
        "agent-1", "AI Agent Context", "CLAUDE.md / AGENTS.md present",
        "pass", "info",
        f"CLAUDE.md exists with {word_count} words of guidance.",
        evidence=[path],
        best_practice_ref=ref,
    )


def check_ci_pipeline(repo: Repo) -> list[CheckResult]:
    ref = "https://docs.github.com/en/actions/learn-github-actions"
    results = []

    workflow_files = repo.find_any([
        ".github/workflows/*.yml", ".github/workflows/*.yaml",
        ".gitlab-ci.yml", ".circleci/config.yml", "azure-pipelines.yml",
        "Jenkinsfile", ".buildkite/pipeline.yml",
    ])
    if not workflow_files:
        results.append(CheckResult(
            "ci-1", "CI/CD Pipeline", "CI configuration exists",
            "fail", "critical",
            "No CI/CD pipeline configuration found (checked GitHub Actions, "
            "GitLab CI, CircleCI, Azure Pipelines, Jenkins, Buildkite).",
            "Add a CI workflow (e.g. .github/workflows/ci.yml) that runs on "
            "every pull request: install deps, lint, typecheck, run tests, "
            "and build. Without this, broken code can merge to main undetected.",
            best_practice_ref=ref,
        ))
        # Downstream checks are moot without any pipeline.
        results.append(CheckResult(
            "ci-2", "CI/CD Pipeline", "Pipeline runs automated tests",
            "fail", "critical",
            "Cannot verify test execution — no CI pipeline exists.",
            "See ci-1.",
            best_practice_ref=ref,
        ))
        return results

    combined = "\n".join(repo.read(f) for f in workflow_files)
    results.append(CheckResult(
        "ci-1", "CI/CD Pipeline", "CI configuration exists",
        "pass", "info",
        f"Found {len(workflow_files)} CI config file(s).",
        evidence=workflow_files,
        best_practice_ref=ref,
    ))

    test_patterns = [r"\btest\b", r"\bunittest\b", r"\bvitest\b", r"\bjest\b", r"\bpytest\b",
                      r"\bgo\s+test\b", r"npm\s+(run\s+)?test", r"pnpm\s+test",
                      r"yarn\s+test", r"rspec\b", r"phpunit\b"]
    has_test_step = any(re.search(p, combined, re.IGNORECASE) for p in test_patterns)
    if has_test_step:
        results.append(CheckResult(
            "ci-2", "CI/CD Pipeline", "Pipeline runs automated tests",
            "pass", "info",
            "CI configuration references a test command.",
            evidence=workflow_files,
            best_practice_ref=ref,
        ))
    else:
        results.append(CheckResult(
            "ci-2", "CI/CD Pipeline", "Pipeline runs automated tests",
            "fail", "critical",
            "CI configuration exists but no step appears to run the test suite.",
            "Add an explicit test step (e.g. `run: npm test` / `pytest`) to the "
            "workflow so regressions are caught before merge, not in production.",
            evidence=workflow_files,
            best_practice_ref=ref,
        ))

    lint_patterns = [r"\blint\b", r"eslint", r"ruff", r"flake8", r"pylint", r"tsc\b", r"typecheck"]
    has_lint_step = any(re.search(p, combined, re.IGNORECASE) for p in lint_patterns)
    results.append(CheckResult(
        "ci-3", "CI/CD Pipeline", "Pipeline runs lint / typecheck",
        "pass" if has_lint_step else "fail",
        "info" if has_lint_step else "medium",
        "CI runs a lint/typecheck step." if has_lint_step else
        "No lint or typecheck step detected in CI configuration.",
        "" if has_lint_step else "Add a lint/typecheck step (eslint/tsc, ruff/mypy, "
        "etc.) so style and type errors are caught pre-merge.",
        evidence=workflow_files,
        best_practice_ref=ref,
    ))

    triggers_on_pr = bool(re.search(r"pull_request", combined, re.IGNORECASE)) or "merge_request" in combined.lower()
    results.append(CheckResult(
        "ci-4", "CI/CD Pipeline", "Pipeline gates pull requests",
        "pass" if triggers_on_pr else "fail",
        "info" if triggers_on_pr else "high",
        "Pipeline triggers on pull/merge requests." if triggers_on_pr else
        "No pull_request/merge_request trigger found — CI may only run after merge, "
        "which doesn't block bad code from landing on main.",
        "" if triggers_on_pr else "Add `on: pull_request` (or equivalent) so CI runs "
        "before code merges, not just after.",
        evidence=workflow_files,
        best_practice_ref=ref,
    ))

    has_deploy_step = bool(re.search(r"deploy|vercel|docker\s+push|kubectl|helm|ecs|render\.com", combined, re.IGNORECASE))
    results.append(CheckResult(
        "ci-5", "CI/CD Pipeline", "Automated deployment step defined",
        "pass" if has_deploy_step else "warn",
        "info" if has_deploy_step else "low",
        "A deployment step/integration was detected in CI config." if has_deploy_step else
        "No deployment step found in CI config (deployment may be handled by an "
        "external platform e.g. Vercel/Netlify git integration — verify manually).",
        evidence=workflow_files,
        best_practice_ref=ref,
    ))

    return results


def check_test_scripts_defined(repo: Repo) -> CheckResult:
    ref = "https://12factor.net/"
    pkg = repo.package_json()
    scripts = pkg.get("scripts", {}) if pkg else {}
    if any(k in scripts for k in ("test",)):
        return CheckResult(
            "ci-6", "CI/CD Pipeline", "Test command defined in project manifest",
            "pass", "info",
            f"package.json defines a `test` script: `{scripts.get('test')}`.",
            best_practice_ref=ref,
        )
    req = repo.requirements_text()
    has_pytest = bool(repo.find_any(["pytest.ini", "setup.cfg", "pyproject.toml"])) and "pytest" in req.lower()
    if has_pytest:
        return CheckResult(
            "ci-6", "CI/CD Pipeline", "Test command defined in project manifest",
            "pass", "info",
            "pytest configuration detected in project manifest.",
            best_practice_ref=ref,
        )
    if pkg:
        return CheckResult(
            "ci-6", "CI/CD Pipeline", "Test command defined in project manifest",
            "fail", "high",
            "package.json exists but does not define a `test` script.",
            "Add a `test` script to package.json so `npm test`/CI has a stable "
            "entry point regardless of the underlying test runner.",
            best_practice_ref=ref,
        )
    return CheckResult(
        "ci-6", "CI/CD Pipeline", "Test command defined in project manifest",
        "warn", "medium",
        "Could not determine project manifest / test entry point.",
        "Ensure the project has a documented, single-command way to run tests.",
        best_practice_ref=ref,
    )


LOGGING_LIBS = [
    "pino", "winston", "bunyan", "log4js",
    "structlog", "loguru", "python-json-logger",
    "zerolog", "logrus", "zap",
    "@opentelemetry/api", "serilog",
]

APM_LIBS = [
    "sentry", "@sentry", "sentry-sdk", "datadog", "dd-trace",
    "newrelic", "new-relic", "opentelemetry", "@vercel/otel",
    "rollbar", "bugsnag", "honeycomb", "@axiomhq", "logtail",
]


def check_structured_logging(repo: Repo) -> list[CheckResult]:
    ref = "https://sre.google/sre-book/monitoring-distributed-systems/"
    results = []
    pkg = repo.package_json()
    deps_blob = json.dumps(pkg.get("dependencies", {}) | pkg.get("devDependencies", {})) if pkg else ""
    req = repo.requirements_text()
    haystack = (deps_blob + "\n" + req).lower()

    matched_logging_libs = [lib for lib in LOGGING_LIBS if lib.lower() in haystack]
    if matched_logging_libs:
        results.append(CheckResult(
            "log-1", "Structured Logging & Observability", "Structured logging library configured",
            "pass", "info",
            f"Structured logging dependency detected: {', '.join(matched_logging_libs)}.",
            best_practice_ref=ref,
        ))
    else:
        # Count raw console/print calls as a proxy for unstructured logging reliance.
        console_hits = repo.grep(r"console\.(log|error|warn|info|debug)\s*\(")
        print_hits = repo.grep(r"(?<!def )\bprint\s*\(")
        total_raw = len(console_hits) + len(print_hits)
        results.append(CheckResult(
            "log-1", "Structured Logging & Observability", "Structured logging library configured",
            "fail", "high",
            f"No structured logging library found in dependencies. Detected "
            f"~{total_raw} raw console/print call(s) across the codebase instead.",
            "Adopt a structured logger (pino/winston for Node, structlog/loguru "
            "for Python) emitting JSON logs with level, timestamp, request/trace "
            "ID, and context fields. Unstructured console/print logs can't be "
            "reliably queried, alerted on, or correlated across services in production.",
            evidence=[f"{f}: {line}" for f, line in (console_hits + print_hits)[:8]],
            best_practice_ref=ref,
        ))

    matched_apm = [lib for lib in APM_LIBS if lib.lower() in haystack]
    if matched_apm:
        results.append(CheckResult(
            "log-2", "Structured Logging & Observability", "Error tracking / APM configured",
            "pass", "info",
            f"Error tracking / observability dependency detected: {', '.join(sorted(set(matched_apm)))}.",
            best_practice_ref=ref,
        ))
    else:
        results.append(CheckResult(
            "log-2", "Structured Logging & Observability", "Error tracking / APM configured",
            "fail", "critical",
            "No error-tracking or APM SDK (Sentry, Datadog, OpenTelemetry, etc.) "
            "found in dependencies.",
            "Without exception tracking, production errors are only visible if a "
            "user reports them. Add Sentry (or an equivalent APM) with server AND "
            "client-side capture, plus alerting on error-rate thresholds.",
            best_practice_ref=ref,
        ))

    health_paths = repo.find_any([
        "*/api/health/*", "*/api/health.*", "*/healthz*", "*/health.*",
        "app/api/health/route.*", "pages/api/health.*",
    ])
    if health_paths:
        results.append(CheckResult(
            "log-3", "Structured Logging & Observability", "Health-check endpoint exposed",
            "pass", "info",
            f"Health-check endpoint found: {', '.join(health_paths)}.",
            best_practice_ref=ref,
        ))
    else:
        results.append(CheckResult(
            "log-3", "Structured Logging & Observability", "Health-check endpoint exposed",
            "fail", "medium",
            "No /health or /healthz endpoint found.",
            "Expose a lightweight health-check route that verifies critical "
            "dependencies (DB, cache, third-party APIs) so load balancers, "
            "container orchestrators, and uptime monitors can detect failures "
            "and auto-restart or fail over.",
            best_practice_ref=ref,
        ))

    correlation_hits = repo.grep(r"(request[-_]?id|correlation[-_]?id|trace[-_]?id|x-request-id)")
    if correlation_hits:
        results.append(CheckResult(
            "log-4", "Structured Logging & Observability", "Request/correlation ID propagation",
            "pass", "info",
            f"Found {len(correlation_hits)} reference(s) to request/trace/correlation IDs.",
            best_practice_ref=ref,
        ))
    else:
        results.append(CheckResult(
            "log-4", "Structured Logging & Observability", "Request/correlation ID propagation",
            "warn", "low",
            "No request/correlation/trace ID handling detected.",
            "Propagate a request/trace ID through logs and downstream calls so "
            "a single user-facing error can be traced across services.",
            best_practice_ref=ref,
        ))

    return results


SECRET_PATTERNS = [
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
    (r"sk_live_[0-9a-zA-Z]{16,}", "Stripe live secret key"),
    (r"sk-[a-zA-Z0-9]{20,}", "OpenAI/Anthropic-style API key"),
    (r"-----BEGIN (RSA|EC|OPENSSH|PRIVATE) KEY-----", "Embedded private key"),
    (r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*[\"'][A-Za-z0-9_\-\/+=]{20,}[\"']", "Hardcoded credential-like literal"),
]


def redact(token: str) -> str:
    """Keep a 4-char head and tail as a fingerprint; hide the rest."""
    token = token.strip().strip("\"'")
    if len(token) <= 8:
        return "****"
    return f"{token[:4]}…{token[-4:]}"


def check_secrets_management(repo: Repo) -> list[CheckResult]:
    ref = "https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html"
    results = []

    env_example = repo.exists(".env.example", ".env.sample", ".env.template", "env.example")
    results.append(CheckResult(
        "sec-1", "Secrets & Environment Management", "Environment variable template committed",
        "pass" if env_example else "fail",
        "info" if env_example else "medium",
        f"Found {env_example}." if env_example else
        "No .env.example / .env.sample template found.",
        "" if env_example else "Commit a .env.example listing required variable "
        "names (no real values) so new environments/contributors can be "
        "provisioned without guessing configuration.",
        best_practice_ref=ref,
    ))

    gitignore = repo.read(".gitignore")
    ignores_env = bool(re.search(r"^\.env", gitignore, re.MULTILINE))
    results.append(CheckResult(
        "sec-2", "Secrets & Environment Management", ".gitignore excludes env files",
        "pass" if ignores_env else "fail",
        "info" if ignores_env else "critical",
        "`.gitignore` excludes .env* files." if ignores_env else
        "`.gitignore` does not exclude .env files — real secrets could be "
        "committed accidentally.",
        "" if ignores_env else "Add `.env*` (with an explicit `!.env.example` "
        "allow-rule) to .gitignore immediately.",
        best_practice_ref=ref,
    ))

    tracked_env_files = [
        f for f in repo.git_files()
        if re.match(r"^(.*/)?\.env(\.[\w-]+)?$", f)
        and not re.search(r"\.(example|sample|template)$", f)
    ]
    if tracked_env_files:
        results.append(CheckResult(
            "sec-3", "Secrets & Environment Management", "No real .env files committed to git",
            "fail", "critical",
            f"Found tracked env file(s) that are not templates: {', '.join(tracked_env_files)}.",
            "Remove these from version control (`git rm --cached`), rotate any "
            "secrets they contained, and confirm .gitignore now excludes them. "
            "Treat any previously-committed secret as compromised.",
            evidence=tracked_env_files,
            best_practice_ref=ref,
        ))
    else:
        results.append(CheckResult(
            "sec-3", "Secrets & Environment Management", "No real .env files committed to git",
            "pass", "info",
            "No non-template .env files are tracked by git.",
            best_practice_ref=ref,
        ))

    secret_hits = []
    scan_files = sorted({
        f for f in repo.git_files() + repo.untracked_files()
        if Path(f).suffix in SECRET_SCAN_EXTS or Path(f).name.startswith(".env")
    })
    for pattern, label in SECRET_PATTERNS:
        rx = re.compile(pattern)
        for f, lineno, line in repo.grep(pattern, paths=scan_files, flags=0, skip_comments=False, with_lineno=True):
            m = rx.search(line)
            token = m.group(0) if m else ""
            secret_hits.append((f, lineno, label, redact(token)))
    if secret_hits:
        results.append(CheckResult(
            "sec-4", "Secrets & Environment Management", "No hardcoded secrets in source",
            "fail", "critical",
            f"Found {len(secret_hits)} potential hardcoded secret(s) in source code.",
            "Move all secrets to environment variables or a secrets manager "
            "(Vercel/Doppler/AWS Secrets Manager/Vault). Rotate any credential "
            "that was ever committed, even if later removed — it remains in git history.",
            # Never put the matched line in the report: it would carry the secret
            # into JSON, Markdown, CI artifacts, and the agent's context.
            evidence=[f"{f}:{lineno} [{label}] {fp}" for f, lineno, label, fp in secret_hits[:10]],
            best_practice_ref=ref,
        ))
    else:
        results.append(CheckResult(
            "sec-4", "Secrets & Environment Management", "No hardcoded secrets in source",
            "pass", "info",
            f"No obvious hardcoded secret patterns in {len(scan_files)} tracked + untracked "
            "code/config files (pattern-based scan of the working tree only — not git "
            "history; not a substitute for gitleaks/truffleHog).",
            best_practice_ref=ref,
        ))

    env_specific_hits = repo.find_any([
        "*.env.production", "*.env.staging", "*.env.development",
        "config/production*", "config/staging*",
    ])
    vercel_env_ref = bool(re.search(r"VERCEL_ENV", repo.read("vercel.json") + repo.read("next.config.ts") + repo.read("next.config.js")))
    platform_env_mgmt = env_specific_hits or vercel_env_ref
    results.append(CheckResult(
        "sec-5", "Secrets & Environment Management", "Environment-specific configuration separation",
        "pass" if platform_env_mgmt else "warn",
        "info" if platform_env_mgmt else "medium",
        "Environment-specific config or platform env branching (e.g. VERCEL_ENV) detected."
        if platform_env_mgmt else
        "No clear separation between dev/staging/production configuration was found.",
        "" if platform_env_mgmt else "Confirm staging and production use distinct "
        "secrets/config (not just different .env values on the same box), managed "
        "via your deploy platform's environment dashboard or a secrets manager — "
        "never share production credentials with lower environments.",
        best_practice_ref=ref,
    ))

    return results


def check_resilience_and_runbooks(repo: Repo) -> list[CheckResult]:
    ref = "https://sre.google/sre-book/postmortem-culture/"
    results = []

    runbook_files = repo.find_any([
        "*RUNBOOK*", "*runbook*", "docs/runbook*", "docs/**/runbook*",
        "*DISASTER_RECOVERY*", "*disaster-recovery*", "*INCIDENT*",
        "docs/**/incident*", "docs/**/on-call*", "*ONCALL*",
    ])
    if runbook_files:
        results.append(CheckResult(
            "res-1", "Resilience & Failover", "Runbook / incident-response docs present",
            "pass", "info",
            f"Found operational doc(s): {', '.join(runbook_files[:5])}.",
            evidence=runbook_files,
            best_practice_ref=ref,
        ))
    else:
        results.append(CheckResult(
            "res-1", "Resilience & Failover", "Runbook / incident-response docs present",
            "fail", "high",
            "No runbook, incident-response, or disaster-recovery documentation found.",
            "Document what to do when the service degrades or fails: who's paged, "
            "how to roll back a deploy, how to fail over the database, and how to "
            "communicate status. Without this, an outage becomes a fire drill "
            "instead of a checklist.",
            best_practice_ref=ref,
        ))

    readme = repo.read("README.md")
    mentions_rollback = bool(re.search(r"rollback|roll back|revert deploy|backup and restore", readme, re.IGNORECASE))
    results.append(CheckResult(
        "res-2", "Resilience & Failover", "Rollback/backup procedure documented",
        "pass" if mentions_rollback else "warn",
        "info" if mentions_rollback else "medium",
        "README references rollback/backup procedures." if mentions_rollback else
        "No rollback or backup procedure documented in README.",
        "" if mentions_rollback else "Document how to roll back a bad deploy and "
        "how database backups/restores work, including RTO/RPO expectations.",
        best_practice_ref=ref,
    ))

    rate_limit_hits = repo.grep(r"rate[-_]?limit|@upstash/ratelimit|express-rate-limit|throttle")
    results.append(CheckResult(
        "res-3", "Resilience & Failover", "Rate limiting / throttling implemented",
        "pass" if rate_limit_hits else "fail",
        "info" if rate_limit_hits else "medium",
        f"Found {len(rate_limit_hits)} rate-limiting reference(s)." if rate_limit_hits else
        "No rate limiting or throttling mechanism detected.",
        "" if rate_limit_hits else "Add rate limiting on public/authenticated API "
        "routes to prevent abuse, runaway costs (especially for LLM/API-billed "
        "endpoints), and cascading overload during traffic spikes.",
        best_practice_ref=ref,
    ))

    migration_dirs = repo.find_any([
        "prisma/migrations/*", "migrations/*", "drizzle/*", "convex/schema.*",
        "alembic/versions/*", "db/migrate/*",
    ])
    results.append(CheckResult(
        "res-4", "Resilience & Failover", "Schema migration tooling in place",
        "pass" if migration_dirs else "warn",
        "info" if migration_dirs else "low",
        f"Found {len(migration_dirs)} migration/schema file(s)." if migration_dirs else
        "No formal migration tooling detected — schema changes may be applied ad hoc.",
        "" if migration_dirs else "Adopt versioned, reversible schema migrations "
        "so production database changes are repeatable and auditable, and can be "
        "rolled back if a deploy fails.",
        best_practice_ref=ref,
    ))

    cron_files = repo.find_any(["**/crons.*", "**/cron/*", "**/*scheduled*"])
    if cron_files:
        # Registration-only files (e.g. Convex's crons.ts) wire a schedule to a
        # target function but don't contain the job logic itself — checking
        # THEM for try/catch is a false signal. Split into "registrars" vs
        # files that likely hold real job logic, and only apply the
        # error-handling heuristic to the latter.
        registrar_pattern = re.compile(r"cronJobs\s*\(|export\s+default\s+crons\b")
        registrar_files, logic_files = [], []
        for f in cron_files:
            content = repo.read(f)
            if registrar_pattern.search(content):
                registrar_files.append(f)
            else:
                logic_files.append(f)

        if logic_files:
            logic_content = "\n".join(repo.read(f) for f in logic_files)
            has_error_handling = bool(re.search(r"try\s*{|except\s|catch\s*\(|\.catch\(", logic_content))
            results.append(CheckResult(
                "res-5", "Resilience & Failover", "Scheduled jobs have error handling",
                "pass" if has_error_handling else "fail",
                "info" if has_error_handling else "medium",
                "Scheduled job code includes try/catch or exception handling." if has_error_handling
                else f"Scheduled job file(s) found ({', '.join(logic_files)}) with no visible error handling.",
                "" if has_error_handling else "Wrap scheduled/cron job logic in error "
                "handling with alerting on failure — a silently-failing cron job is a "
                "common source of undetected production data drift.",
                evidence=logic_files,
                best_practice_ref=ref,
            ))
        elif registrar_files:
            # Only a registrar was found — the actual job implementations live in
            # the functions it references. Flag as informational, not a failure,
            # but point the auditor at the files to check by hand.
            results.append(CheckResult(
                "res-5", "Resilience & Failover", "Scheduled jobs have error handling",
                "info", "info",
                f"Found cron schedule registration file(s) ({', '.join(registrar_files)}) "
                "that reference target job functions elsewhere in the codebase. This tool "
                "cannot statically resolve those target functions, so error handling in "
                "the actual job logic was not verified automatically.",
                "Manually confirm each scheduled job function wraps its logic in "
                "try/catch (or equivalent) with failure alerting — a silently-failing "
                "cron job is a common source of undetected production data drift.",
                evidence=registrar_files,
                best_practice_ref=ref,
            ))

    return results


DESTRUCTIVE_MIGRATION_PATTERN = re.compile(
    r"DROP\s+TABLE|DROP\s+COLUMN|TRUNCATE\s+TABLE|ALTER\s+TABLE\s+\w+\s+DROP|DELETE\s+FROM\s+\w+\s*;",
    re.IGNORECASE,
)


def check_multi_surface_deployment(repo: Repo, fp: StackFingerprint) -> list[CheckResult]:
    """First-class check for the 'paired rollback trap': when a deploy ships
    more than one independently-rollback-able surface (e.g. a frontend host +
    a backend/BaaS, or a docker-compose stack with its own migration step),
    rolling back only one surface can silently desync the system. This used
    to be a single generic bullet inside Resilience & Failover — split out
    because it's a distinct failure mode with its own severity, not a
    sub-case of "no rollback docs".
    """
    ref = "https://vercel.com/docs/deployments/rollback-production-deployment"
    results = []

    if not fp.multi_surface:
        results.append(CheckResult(
            "ms-1", "Multi-Surface Deployment & Coordinated Rollback",
            "Multi-surface deployment risk",
            "pass", "info",
            "Single deploy surface detected " +
            (f"({', '.join(fp.deploy_surfaces)}). " if fp.deploy_surfaces else "(no deploy platform config found). ") +
            "Standard rollback documentation (see Resilience & Failover) is sufficient — "
            "there is no second surface that can drift out of sync.",
            best_practice_ref=ref,
        ))
    else:
        results.append(CheckResult(
            "ms-1", "Multi-Surface Deployment & Coordinated Rollback",
            "Multi-surface deployment risk",
            "fail", "high",
            "Multiple independently-deployable surfaces detected: " + " | ".join(fp.multi_surface_evidence),
            "Rolling back one surface without an explicit, matching plan for the others "
            "(schema/data compatibility, which one rolls back first) can leave the system "
            "in a half-rolled-back state that's worse than the original incident.",
            evidence=fp.deploy_surfaces,
            best_practice_ref=ref,
        ))

        runbook_files = repo.find_any([
            "*RUNBOOK*", "*runbook*", "docs/runbook*", "docs/**/runbook*",
            "*DISASTER_RECOVERY*", "*disaster-recovery*", "README.md",
        ])
        combined_text = "\n".join(repo.read(f) for f in runbook_files).lower()
        surface_mentions = sum(1 for s in fp.deploy_surfaces if s.replace("-", " ") in combined_text or s in combined_text)
        mentions_coordination = bool(re.search(r"rollback|roll back|revert", combined_text)) and surface_mentions >= 2
        results.append(CheckResult(
            "ms-2", "Multi-Surface Deployment & Coordinated Rollback",
            "Coordinated rollback procedure documented",
            "pass" if mentions_coordination else "fail",
            "info" if mentions_coordination else "high",
            "Runbook/README references rollback across multiple named surfaces." if mentions_coordination else
            f"No documentation found that addresses rollback across all detected surfaces "
            f"({', '.join(fp.deploy_surfaces)}) together. A generic 'how to roll back' note for "
            "just one platform is not sufficient here.",
            "" if mentions_coordination else "Document, for this specific stack, which surface "
            "rolls back first, how to verify the other surface(s) are still compatible with the "
            "rolled-back version, and what breaks if only one side is reverted.",
            evidence=runbook_files[:5],
            best_practice_ref=ref,
        ))

    # Irreversible-migration safety is checked regardless of multi-surface status —
    # a single-surface app can still lose data permanently from a destructive migration
    # that a code rollback cannot undo.
    migration_paths = repo.find_any([
        "prisma/migrations/**/*.sql",
        "drizzle/*.sql", "**/drizzle/*.sql", "drizzle/**/*.sql", "**/drizzle/**/*.sql",
        "alembic/versions/*.py", "**/alembic/versions/*.py",
        "db/migrate/*.rb", "**/db/migrate/*.rb",
    ])
    destructive_hits = []
    for f in migration_paths:
        content = repo.read(f)
        if DESTRUCTIVE_MIGRATION_PATTERN.search(content):
            destructive_hits.append(f)
    if migration_paths:
        results.append(CheckResult(
            "ms-3", "Multi-Surface Deployment & Coordinated Rollback",
            "Irreversible migrations flagged",
            "fail" if destructive_hits else "pass",
            "critical" if destructive_hits else "info",
            f"{len(destructive_hits)} migration file(s) contain destructive operations "
            f"(DROP/TRUNCATE/DELETE) that cannot be undone by redeploying an older app version: "
            f"{', '.join(destructive_hits[:5])}." if destructive_hits else
            f"Scanned {len(migration_paths)} migration file(s) — no destructive SQL patterns detected.",
            "" if not destructive_hits else "For each destructive migration, confirm a tested backup "
            "exists from immediately before it ran, and document the actual recovery step (restore from "
            "backup — not 'redeploy old code', which does not undo a schema/data change already applied).",
            evidence=destructive_hits,
            best_practice_ref=ref,
        ))

    return results


def check_testing_quality_gates(repo: Repo) -> list[CheckResult]:
    ref = "https://martinfowler.com/testing/"
    results = []

    test_files = repo.find_any([
        "**/*.test.*", "**/*.spec.*", "**/__tests__/*", "**/test_*.py", "**/*_test.py", "tests/**",
    ])
    results.append(CheckResult(
        "test-1", "Testing & Quality Gates", "Automated test files exist",
        "pass" if test_files else "fail",
        "info" if test_files else "critical",
        f"Found {len(test_files)} test file(s)." if test_files else
        "No test files found anywhere in the repository.",
        "" if test_files else "Add automated tests before production release — "
        "at minimum, cover critical business logic, payment/billing paths, and "
        "auth flows. Zero test coverage is a direct release blocker.",
        evidence=test_files[:10],
        best_practice_ref=ref,
    ))

    test_config = repo.exists(
        "jest.config.js", "jest.config.ts", "vitest.config.ts", "vitest.config.js",
        "pytest.ini", "playwright.config.ts", "cypress.config.ts", "phpunit.xml",
    )
    results.append(CheckResult(
        "test-2", "Testing & Quality Gates", "Test runner configured",
        "pass" if test_config else "warn",
        "info" if test_config else "low",
        f"Found test runner config: {test_config}." if test_config else
        "No explicit test runner configuration file found.",
        best_practice_ref=ref,
    ))

    coverage_cfg = bool(re.search(r"coverage", repo.read(test_config or "") + json.dumps(repo.package_json())))
    results.append(CheckResult(
        "test-3", "Testing & Quality Gates", "Coverage tracking configured",
        "pass" if coverage_cfg else "warn",
        "info" if coverage_cfg else "low",
        "Coverage configuration detected." if coverage_cfg else
        "No test coverage configuration/threshold detected.",
        "" if coverage_cfg else "Track coverage (even informally) so you know "
        "which critical paths are untested before shipping.",
        best_practice_ref=ref,
    ))

    tsconfig = repo.read("tsconfig.json")
    strict_ts = bool(re.search(r'"strict"\s*:\s*true', tsconfig))
    mypy_cfg = repo.exists("mypy.ini", "setup.cfg") and "mypy" in repo.requirements_text().lower()
    if tsconfig:
        results.append(CheckResult(
            "test-4", "Testing & Quality Gates", "Static type checking enforced",
            "pass" if strict_ts else "warn",
            "info" if strict_ts else "medium",
            "tsconfig.json has strict mode enabled." if strict_ts else
            "tsconfig.json exists but `strict` mode is not enabled.",
            "" if strict_ts else "Enable `\"strict\": true` in tsconfig.json to "
            "catch null/undefined and type errors before runtime.",
            best_practice_ref=ref,
        ))
    elif mypy_cfg:
        results.append(CheckResult(
            "test-4", "Testing & Quality Gates", "Static type checking enforced",
            "pass", "info", "mypy configuration detected for Python type checking.",
            best_practice_ref=ref,
        ))

    return results


def check_dependency_security(repo: Repo) -> list[CheckResult]:
    ref = "https://docs.github.com/en/code-security/dependabot"
    results = []

    lockfile = repo.exists(
        "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lockb",
        "poetry.lock", "Pipfile.lock", "go.sum", "Cargo.lock",
    )
    results.append(CheckResult(
        "dep-1", "Dependency & Supply-chain Security", "Dependency lockfile committed",
        "pass" if lockfile else "fail",
        "info" if lockfile else "high",
        f"Found lockfile: {lockfile}." if lockfile else "No dependency lockfile found.",
        "" if lockfile else "Commit a lockfile so builds are reproducible across "
        "environments — without one, production can silently pull different "
        "dependency versions than what was tested.",
        best_practice_ref=ref,
    ))

    bot_cfg = repo.exists(".github/dependabot.yml", ".github/dependabot.yaml", "renovate.json", ".renovaterc")
    results.append(CheckResult(
        "dep-2", "Dependency & Supply-chain Security", "Automated dependency updates configured",
        "pass" if bot_cfg else "warn",
        "info" if bot_cfg else "low",
        f"Found {bot_cfg}." if bot_cfg else "No Dependabot/Renovate configuration found.",
        "" if bot_cfg else "Enable Dependabot or Renovate so security patches for "
        "dependencies land automatically instead of accumulating silently.",
        best_practice_ref=ref,
    ))

    workflow_files = repo.find_any([".github/workflows/*.yml", ".github/workflows/*.yaml"])
    combined = "\n".join(repo.read(f) for f in workflow_files)
    has_audit_step = bool(re.search(r"npm audit|pip-audit|trivy|snyk|osv-scanner|cargo audit", combined, re.IGNORECASE))
    results.append(CheckResult(
        "dep-3", "Dependency & Supply-chain Security", "CI runs a dependency vulnerability scan",
        "pass" if has_audit_step else "warn",
        "info" if has_audit_step else "medium",
        "CI includes a dependency vulnerability scan step." if has_audit_step else
        "No dependency vulnerability scan (npm audit / pip-audit / Trivy / Snyk) "
        "found in CI.",
        "" if has_audit_step else "Add an automated vulnerability scan step to CI "
        "so known-CVE dependencies are flagged before release.",
        best_practice_ref=ref,
    ))

    return results


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------

CATEGORY_META = [
    ("AI Agent Context", "AI Agent Context",
     "Documentation that lets AI coding agents and human contributors operate "
     "safely and consistently on the codebase.",
     "https://docs.claude.com/en/docs/claude-code/memory"),
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
    categories = {key: Category(key, title, desc, ref) for key, title, desc, ref in CATEGORY_META}

    categories["AI Agent Context"].checks.append(check_claude_md(repo))
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
            if c.id in skips:
                c.status, c.severity = "n/a", "info"
                why = ("Project type not determined; insufficient evidence to apply this check. Re-run with --profile."
                       if fingerprint.profile == "unknown" else f"Not applicable to a {fingerprint.profile} project.")
                c.detail = f"{why} {c.detail}"
                c.recommendation = ""

    return list(categories.values()), fingerprint


# --------------------------------------------------------------------------
# Report rendering
# --------------------------------------------------------------------------

def overall_score(categories: list[Category]) -> int:
    scored = [c for c in categories if c.applicable]
    if not scored:
        return 0
    return round(sum(c.score for c in scored) / len(scored))


def grade_for(score: int, critical_count: int = 0) -> str:
    # A category average can hide a release blocker. Any critical fail caps
    # the grade at D regardless of the numeric score.
    if critical_count > 0:
        return "D — Release blockers present" if score >= 40 else "F — Release blockers, little else in place"
    if score >= 90:
        return "A — Strong evidence of controls"
    if score >= 75:
        return "B — Minor gaps"
    if score >= 60:
        return "C — Notable gaps"
    if score >= 40:
        return "D — Major gaps"
    return "F — Few controls found"


def render_markdown(categories: list[Category], repo_name: str, fp: Optional[StackFingerprint] = None,
                     product_context: str = "") -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    score = overall_score(categories)
    all_checks = [c for cat in categories for c in cat.checks]
    blocking = [c for c in all_checks if c.status == "fail" and c.severity == "critical"]
    grade = grade_for(score, len(blocking))
    high = [c for c in all_checks if c.status == "fail" and c.severity == "high"]

    lines = []
    lines.append(f"# Production Readiness Audit — {repo_name}")
    lines.append("")
    lines.append(f"_Generated {now} by prod_audit.py_")
    lines.append("")

    if fp is not None:
        lines.append("## Detected Stack")
        lines.append("")
        lines.append(
            "This section is produced by deterministic static analysis (manifests, lockfiles, deploy "
            "configs) — re-running against the same commit always yields the same result. It drives "
            "which stack-specific reference material gets applied on top of this report."
        )
        lines.append("")
        lines.append(f"- **Languages:** {', '.join(fp.languages) or '_none detected_'}")
        lines.append(f"- **Package manager(s):** {', '.join(fp.package_managers) or '_none detected_'}")
        lines.append(f"- **Frameworks:** {', '.join(fp.frameworks) or '_none detected_'}")
        lines.append(f"- **Deploy surface(s):** {', '.join(fp.deploy_surfaces) or '_none detected_'}")
        lines.append(f"- **Runtime(s):** {', '.join(fp.runtimes) or '_none detected_'}")
        lines.append(f"- **Migration tooling:** {', '.join(fp.migration_tooling) or '_none detected_'}")
        lines.append(f"- **Multi-surface deployment:** {'YES — see Multi-Surface category below' if fp.multi_surface else 'No'}")
        if fp.adapters_matched:
            lines.append(
                f"- **Stack adapter reference(s) to apply:** {', '.join(fp.adapters_matched)} "
                f"(`references/stacks/<name>.md` in this skill)"
            )
        lines.append("")

    if product_context:
        lines.append("## Product Context (as provided)")
        lines.append("")
        lines.append(
            f"> {product_context}"
        )
        lines.append("")
        lines.append(
            "_This does not change the deterministic severity scores below — it's used to reprioritize "
            "which findings matter most when this report is translated into a fix plan (e.g. a 'medium' "
            "backups finding is functionally critical for an app holding irreplaceable user data)._"
        )
        lines.append("")

    if fp is not None:
        lines.append(f"**Profile:** `{fp.profile}` ({fp.profile_source}). Checks that do not apply to this "
                     "profile are marked n/a and left out of the score. Wrong profile? Re-run with `--profile`.")
        lines.append("")
    lines.append(f"## Repository Controls Score: {score}/100 — {grade}")
    lines.append("")
    lines.append("_This is a static scan of files and config. It measures which production controls "
                 "have evidence in the repo. It does not run the app and cannot prove the product works._")
    lines.append("")
    if blocking:
        lines.append(f"**{len(blocking)} CRITICAL blocking issue(s)** must be resolved before a stable, "
                      f"scalable production release.")
    else:
        lines.append("No CRITICAL blocking issues detected — review HIGH/MEDIUM findings below before release.")
    lines.append("")

    lines.append("| Category | Score | Critical | High | Failing Checks |")
    lines.append("|---|---|---|---|---|")
    for cat in categories:
        fails = [c for c in cat.checks if c.status == "fail"]
        crit = sum(1 for c in fails if c.severity == "critical")
        hi = sum(1 for c in fails if c.severity == "high")
        lines.append(f"| {cat.title} | {cat.score}/100 | {crit} | {hi} | {len(fails)} |")
    lines.append("")

    if blocking:
        lines.append("## 🔴 Release Blockers (Critical)")
        lines.append("")
        for c in blocking:
            lines.append(f"### {c.title} ({c.category})")
            lines.append(f"- **Issue:** {c.detail}")
            if c.recommendation:
                lines.append(f"- **Fix:** {c.recommendation}")
            if c.evidence:
                lines.append(f"- **Evidence:** {', '.join(c.evidence[:5])}")
            if c.best_practice_ref:
                lines.append(f"- **Best practice reference:** [{c.best_practice_ref}]({c.best_practice_ref})")
            lines.append("")

    if high:
        lines.append("## 🟠 High-Priority Gaps")
        lines.append("")
        for c in high:
            lines.append(f"### {c.title} ({c.category})")
            lines.append(f"- **Issue:** {c.detail}")
            if c.recommendation:
                lines.append(f"- **Fix:** {c.recommendation}")
            if c.evidence:
                lines.append(f"- **Evidence:** {', '.join(c.evidence[:5])}")
            if c.best_practice_ref:
                lines.append(f"- **Best practice reference:** [{c.best_practice_ref}]({c.best_practice_ref})")
            lines.append("")

    lines.append("## Full Findings by Category")
    lines.append("")
    for cat in categories:
        lines.append(f"### {cat.title}")
        lines.append(f"_{cat.description}_")
        lines.append("")
        lines.append(f"Best practice reference: [{cat.best_practice_ref}]({cat.best_practice_ref})")
        lines.append("")
        lines.append("| Check | Status | Severity | Detail |")
        lines.append("|---|---|---|---|")
        for c in sorted(cat.checks, key=lambda x: SEVERITY_ORDER.get(x.severity, 9)):
            status_icon = {"pass": "✅", "fail": "❌", "warn": "⚠️", "info": "ℹ️", "n/a": "➖"}.get(c.status, "")
            detail = c.detail.replace("|", "\\|")
            status_text = f"{status_icon} {c.status}" + (" (text match — verify by hand)" if c.confidence == "weak" else "")
            lines.append(f"| {c.title} | {status_text} | {SEVERITY_LABEL.get(c.severity, c.severity)} | {detail} |")
        # Recommendations for any non-pass checks
        recs = [c for c in cat.checks if c.status != "pass" and c.recommendation]
        if recs:
            lines.append("")
            lines.append("**Recommendations:**")
            for c in recs:
                lines.append(f"- **{c.title}:** {c.recommendation}")
        lines.append("")

    lines.append("## Methodology")
    lines.append("")
    lines.append(
        "This tool performs static analysis of the repository working tree "
        "(via `git ls-files` where available) — no code execution, no network "
        "calls, no dependency installation. Secret detection uses pattern "
        "matching and is not a substitute for a dedicated secret-scanning tool "
        "(e.g. gitleaks/truffleHog) run against full git history. Re-run after "
        "remediation to confirm fixes and track score over time."
    )
    lines.append("")
    lines.append("Best-practice sources used to define these checks:")
    lines.append("- [The Twelve-Factor App](https://12factor.net/)")
    lines.append("- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)")
    lines.append("- [Google SRE Book](https://sre.google/sre-book/table-of-contents/)")
    lines.append("- [GitHub Actions documentation](https://docs.github.com/en/actions/learn-github-actions)")
    lines.append("- [GitHub Dependabot documentation](https://docs.github.com/en/code-security/dependabot)")
    lines.append("- [Martin Fowler on Testing](https://martinfowler.com/testing/)")
    lines.append("")

    return "\n".join(lines)


def render_json(categories: list[Category], repo_name: str, fp: Optional[StackFingerprint] = None,
                 product_context: str = "") -> dict:
    return {
        "repo": repo_name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_score": overall_score(categories),
        "grade": grade_for(overall_score(categories), sum(c.blocking_count for c in categories)),
        "stack_fingerprint": asdict(fp) if fp is not None else None,
        "product_context": product_context or None,
        "categories": [
            {
                "key": cat.key,
                "title": cat.title,
                "score": cat.score,
                "checks": [asdict(c) for c in cat.checks],
            }
            for cat in categories
        ],
    }


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Production-readiness audit tool for a project repository.")
    parser.add_argument("--repo", required=True, help="Path to the repository to audit.")
    parser.add_argument("--output", default=None, help="Path to write the Markdown report (default: prints to stdout).")
    parser.add_argument("--json", default=None, help="Optional path to also write a JSON report.")
    parser.add_argument("--fail-on", choices=["critical", "high", "none"], default="none",
                         help="Exit non-zero if any failing check at/above this severity is found (for CI gating).")
    parser.add_argument("--context", default="",
                         help="Optional one-line product context (e.g. 'what's the worst case if this loses "
                              "data or goes down for a day') used downstream to reprioritize findings. Does "
                              "not change the deterministic scores.")
    parser.add_argument("--profile", choices=PROFILES, default=None,
                         help="What kind of project this is. Checks that do not apply are marked n/a and "
                              "skipped in scoring. Guessed from the stack when omitted (strict when unsure).")
    args = parser.parse_args()

    repo_path = Path(args.repo)
    if not repo_path.exists():
        print(f"error: repo path does not exist: {repo_path}", file=sys.stderr)
        sys.exit(2)

    categories, fingerprint = run_audit(repo_path, args.profile)
    md = render_markdown(categories, repo_path.resolve().name, fingerprint, args.context)

    if args.output:
        Path(args.output).write_text(md, encoding="utf-8")
        print(f"Markdown report written to {args.output}")
    else:
        print(md)

    if args.json:
        Path(args.json).write_text(
            json.dumps(render_json(categories, repo_path.resolve().name, fingerprint, args.context), indent=2),
            encoding="utf-8")
        print(f"JSON report written to {args.json}")

    if args.fail_on != "none":
        all_checks = [c for cat in categories for c in cat.checks]
        threshold = ["critical", "high"] if args.fail_on == "high" else ["critical"]
        blocking = [c for c in all_checks if c.status == "fail" and c.severity in threshold]
        if blocking:
            print(f"\n{len(blocking)} check(s) at or above '{args.fail_on}' severity failed.", file=sys.stderr)
            sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
