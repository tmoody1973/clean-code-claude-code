"""Checks about tests and dependencies."""
import json
import re
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from .model import CheckResult
from .repo import Repo

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
        "" if test_files else "Add automated tests before production release, "
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
        "environments, without one, production can silently pull different "
        "dependency versions than what was tested.",
        evidence=[lockfile] if lockfile else [],
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


