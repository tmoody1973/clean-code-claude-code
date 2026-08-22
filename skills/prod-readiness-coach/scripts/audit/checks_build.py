"""Checks about how code gets built and shipped: agent context, CI, test wiring."""
import re
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from .model import CheckResult, runs_a_test_suite
from .repo import Repo

# --------------------------------------------------------------------------
# Individual checks, each returns a CheckResult
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
            f"{path} exists but is very short ({word_count} words), may be a stub.",
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
            "Cannot verify test execution, no CI pipeline exists.",
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

    has_test_step = runs_a_test_suite(combined)
    if has_test_step:
        results.append(CheckResult(
            "ci-2", "CI/CD Pipeline", "Pipeline runs automated tests",
            "pass", "info",
            "CI runs a real test runner, not just a step with the word test in it.",
            evidence=workflow_files,
            best_practice_ref=ref,
        ))
    else:
        results.append(CheckResult(
            "ci-2", "CI/CD Pipeline", "Pipeline runs automated tests",
            "fail", "critical",
            "CI configuration exists but no step invokes a test runner. A step that only "
            "prints the word test does not count.",
            "Add an explicit test step (e.g. `run: npm test` / `pytest`) to the "
            "workflow so regressions are caught before merge, not in production.",
            evidence=workflow_files,
            best_practice_ref=ref,
        ))

    # A lint step is a lint step in any language. The first version of this list
    # only knew the Node and Python names, so a CI running `mypy app` was told it
    # had no typecheck step at all.
    lint_patterns = [
        r"\blint\b", r"typecheck", r"\btsc\b",
        r"eslint", r"biome\s+(?:check|lint)", r"oxlint", r"prettier\s+--check",
        r"\bruff\b", r"flake8", r"pylint", r"\bmypy\b", r"pyright", r"\bblack\s+--check",
        r"golangci-lint", r"\bgo\s+vet\b", r"\bgofmt\b", r"staticcheck",
        r"rubocop", r"\bclippy\b", r"cargo\s+fmt", r"dotnet\s+format",
        r"ktlint", r"detekt", r"checkstyle", r"\bphpstan\b", r"psalm",
    ]
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
        "No pull_request/merge_request trigger found, CI may only run after merge, "
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
        "external platform e.g. Vercel/Netlify git integration, verify manually).",
        evidence=workflow_files,
        best_practice_ref=ref,
    ))

    return results


def check_test_scripts_defined(repo: Repo) -> CheckResult:
    ref = "https://12factor.net/"
    pkg = repo.package_json()
    scripts = pkg.get("scripts", {}) if pkg else {}
    if "test" in scripts:
        cmd = str(scripts.get("test", ""))
        if runs_a_test_suite(cmd):
            return CheckResult(
                "ci-6", "CI/CD Pipeline", "Test command defined in project manifest",
                "pass", "info",
                f"package.json defines a `test` script that runs a test runner: `{cmd}`.",
                evidence=[f"package.json scripts.test: {cmd}"],
                best_practice_ref=ref,
            )
        return CheckResult(
            "ci-6", "CI/CD Pipeline", "Test command defined in project manifest",
            "fail", "high",
            f"package.json has a `test` script, but it does not run a test runner: `{cmd}`. "
            "A script that only prints a message and exits 0 makes CI green while testing nothing.",
            "Point the `test` script at a real runner (vitest, jest, pytest, `node --test`), "
            "so a green pipeline means the suite actually ran.",
            evidence=[f"package.json scripts.test: {cmd}"],
            best_practice_ref=ref,
        )
    req = repo.requirements_text()
    has_pytest = bool(repo.find_any(["pytest.ini", "setup.cfg", "pyproject.toml"])) and "pytest" in req.lower()
    if has_pytest:
        return CheckResult(
            "ci-6", "CI/CD Pipeline", "Test command defined in project manifest",
            "pass", "info",
            "pytest configuration detected in project manifest.",
            evidence=[repo.find_any(["pytest.ini", "setup.cfg", "pyproject.toml"])[0]],
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
        "No test entry point was found. This check reads a `test` script in package.json "
        "or a pytest configuration; it has no rules for other ecosystems, so a Go, Rust or "
        "Ruby project will land here even when its test command is fine.",
        "Ensure the project has a documented, single-command way to run tests, and check "
        "the CI findings above, which do look at every ecosystem.",
        evidence=["scope: checked package.json scripts.test and pytest configuration"],
        best_practice_ref=ref,
    )





