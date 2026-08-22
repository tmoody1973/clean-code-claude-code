"""Checks about the app while it runs: logging, secrets, resilience, rollback."""
import fnmatch
import json
import re
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from .model import (MIN_DOC_WORDS, TODO_LINE_RX, CheckResult, has_substance)
from .repo import SECRET_SCAN_EXTS, Repo
from .fingerprint import StackFingerprint

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
    reads_env = bool(repo.grep(r"process\.env\.|os\.environ|os\.getenv|import\.meta\.env|Deno\.env|System\.getenv|ENV\[|os\.Getenv")) \
        or bool(repo.untracked_files() and any(f.startswith(".env") for f in repo.untracked_files()))
    if not reads_env and not env_example:
        results.append(CheckResult(
            "sec-1", "Secrets & Environment Management", "Environment variable template committed",
            "n/a", "info",
            "No environment-variable reads detected, so a template is not required.",
            best_practice_ref=ref,
        ))
    else:
      results.append(CheckResult(
        "sec-1", "Secrets & Environment Management", "Environment variable template committed",
        "pass" if env_example else "fail",
        "info" if env_example else "medium",
        f"Found {env_example}." if env_example else
        "The code reads environment variables but no .env.example / .env.sample template was found.",
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
    with_content = [f for f in runbook_files if has_substance(repo.read(f))]
    if with_content:
        results.append(CheckResult(
            "res-1", "Resilience & Failover", "Runbook / incident-response docs present",
            "pass", "info",
            f"Found operational doc(s) with real content: {', '.join(with_content[:5])}.",
            evidence=with_content,
            best_practice_ref=ref,
        ))
    elif runbook_files:
        results.append(CheckResult(
            "res-1", "Resilience & Failover", "Runbook / incident-response docs present",
            "fail", "high",
            f"Found {', '.join(runbook_files[:5])}, but it is empty or under "
            f"{MIN_DOC_WORDS} words. A placeholder is not a runbook.",
            "Fill it in: how you notice the failure, how you re-run or roll back, "
            "and how you turn it off if it keeps failing.",
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
    rollback_lines = [l.strip() for l in readme.splitlines()
                      if re.search(r"rollback|roll back|revert deploy|backup and restore", l, re.IGNORECASE)
                      and not TODO_LINE_RX.search(l)]
    mentions_rollback = bool(rollback_lines)
    results.append(CheckResult(
        "res-2", "Resilience & Failover", "Rollback/backup procedure documented",
        "pass" if mentions_rollback else "warn",
        "info" if mentions_rollback else "medium",
        "README references rollback/backup procedures." if mentions_rollback else
        "No rollback or backup procedure documented in README.",
        "" if mentions_rollback else "Document how to roll back a bad deploy and "
        "how database backups/restores work, including RTO/RPO expectations.",
        evidence=rollback_lines[:3],
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


