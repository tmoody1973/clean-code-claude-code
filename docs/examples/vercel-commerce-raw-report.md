> Example output. Generated 2026-08-20 by `prod_audit.py` against a shallow clone of [vercel/commerce](https://github.com/vercel/commerce) at that date. No product context was given, so no profile flag was passed; the tool inferred `web-app` and the `nextjs-vercel` adapter. Findings reflect that snapshot, not the project today.

# Production Readiness Audit — commerce

_Generated 2026-08-20 19:21 UTC by prod_audit.py_

## Detected Stack

This section is produced by deterministic static analysis (manifests, lockfiles, deploy configs) — re-running against the same commit always yields the same result. It drives which stack-specific reference material gets applied on top of this report.

- **Languages:** typescript
- **Package manager(s):** pnpm
- **Frameworks:** nextjs
- **Deploy surface(s):** vercel
- **Runtime(s):** node
- **Migration tooling:** _none detected_
- **Multi-surface deployment:** No
- **Stack adapter reference(s) to apply:** nextjs-vercel (`references/stacks/<name>.md` in this skill)

**Profile:** `web-app` (guessed). Checks that do not apply to this profile are marked n/a and left out of the score. Wrong profile? Re-run with `--profile`.

## Repository Controls Score: 76/100 — D — Release blockers present

_This is a static scan of files and config. It measures which production controls have evidence in the repo. It does not run the app and cannot prove the product works._

**4 CRITICAL blocking issue(s)** must be resolved before a stable, scalable production release.

| Category | Score | Critical | High | Failing Checks |
|---|---|---|---|---|
| AI Agent Context | 82/100 | 0 | 1 | 1 |
| CI/CD Pipeline | 40/100 | 2 | 0 | 2 |
| Structured Logging & Observability | 42/100 | 1 | 1 | 3 |
| Secrets & Environment Management | 100/100 | 0 | 0 | 0 |
| Resilience & Failover | 72/100 | 0 | 1 | 2 |
| Multi-Surface Deployment & Coordinated Rollback | 100/100 | 0 | 0 | 0 |
| Testing & Quality Gates | 70/100 | 1 | 0 | 1 |
| Dependency & Supply-chain Security | 100/100 | 0 | 0 | 0 |

## 🔴 Release Blockers (Critical)

### CI configuration exists (CI/CD Pipeline)
- **Issue:** No CI/CD pipeline configuration found (checked GitHub Actions, GitLab CI, CircleCI, Azure Pipelines, Jenkins, Buildkite).
- **Fix:** Add a CI workflow (e.g. .github/workflows/ci.yml) that runs on every pull request: install deps, lint, typecheck, run tests, and build. Without this, broken code can merge to main undetected.
- **Best practice reference:** [https://docs.github.com/en/actions/learn-github-actions](https://docs.github.com/en/actions/learn-github-actions)

### Pipeline runs automated tests (CI/CD Pipeline)
- **Issue:** Cannot verify test execution — no CI pipeline exists.
- **Fix:** See ci-1.
- **Best practice reference:** [https://docs.github.com/en/actions/learn-github-actions](https://docs.github.com/en/actions/learn-github-actions)

### Error tracking / APM configured (Structured Logging & Observability)
- **Issue:** No error-tracking or APM SDK (Sentry, Datadog, OpenTelemetry, etc.) found in dependencies.
- **Fix:** Without exception tracking, production errors are only visible if a user reports them. Add Sentry (or an equivalent APM) with server AND client-side capture, plus alerting on error-rate thresholds.
- **Best practice reference:** [https://sre.google/sre-book/monitoring-distributed-systems/](https://sre.google/sre-book/monitoring-distributed-systems/)

### Automated test files exist (Testing & Quality Gates)
- **Issue:** No test files found anywhere in the repository.
- **Fix:** Add automated tests before production release — at minimum, cover critical business logic, payment/billing paths, and auth flows. Zero test coverage is a direct release blocker.
- **Best practice reference:** [https://martinfowler.com/testing/](https://martinfowler.com/testing/)

## 🟠 High-Priority Gaps

### CLAUDE.md / AGENTS.md present (AI Agent Context)
- **Issue:** No CLAUDE.md or AGENTS.md found at the repository root.
- **Fix:** Add a CLAUDE.md (or AGENTS.md) documenting build/test/lint commands, architecture conventions, and guardrails so AI coding agents (and new engineers) operate consistently instead of re-deriving project context every session.
- **Best practice reference:** [https://docs.claude.com/en/docs/claude-code/memory](https://docs.claude.com/en/docs/claude-code/memory)

### Structured logging library configured (Structured Logging & Observability)
- **Issue:** No structured logging library found in dependencies. Detected ~7 raw console/print call(s) across the codebase instead.
- **Fix:** Adopt a structured logger (pino/winston for Node, structlog/loguru for Python) emitting JSON logs with level, timestamp, request/trace ID, and context fields. Unstructured console/print logs can't be reliably queried, alerted on, or correlated across services in production.
- **Evidence:** components/cart/actions.ts: console.error(e);, lib/shopify/index.ts: console.log(, lib/shopify/index.ts: console.log(`No collection found for \`${collection}\``);, lib/shopify/index.ts: console.log("Skipping getCollections - Shopify not configured");, lib/shopify/index.ts: console.log(`Skipping getMenu for '${handle}' - Shopify not configured`);
- **Best practice reference:** [https://sre.google/sre-book/monitoring-distributed-systems/](https://sre.google/sre-book/monitoring-distributed-systems/)

### Runbook / incident-response docs present (Resilience & Failover)
- **Issue:** No runbook, incident-response, or disaster-recovery documentation found.
- **Fix:** Document what to do when the service degrades or fails: who's paged, how to roll back a deploy, how to fail over the database, and how to communicate status. Without this, an outage becomes a fire drill instead of a checklist.
- **Best practice reference:** [https://sre.google/sre-book/postmortem-culture/](https://sre.google/sre-book/postmortem-culture/)

## Full Findings by Category

### AI Agent Context
_Documentation that lets AI coding agents and human contributors operate safely and consistently on the codebase._

Best practice reference: [https://docs.claude.com/en/docs/claude-code/memory](https://docs.claude.com/en/docs/claude-code/memory)

| Check | Status | Severity | Detail |
|---|---|---|---|
| CLAUDE.md / AGENTS.md present | ❌ fail | 🟠 HIGH | No CLAUDE.md or AGENTS.md found at the repository root. |

**Recommendations:**
- **CLAUDE.md / AGENTS.md present:** Add a CLAUDE.md (or AGENTS.md) documenting build/test/lint commands, architecture conventions, and guardrails so AI coding agents (and new engineers) operate consistently instead of re-deriving project context every session.

### CI/CD Pipeline
_Automated build/test/lint gates that block broken code from reaching production._

Best practice reference: [https://docs.github.com/en/actions/learn-github-actions](https://docs.github.com/en/actions/learn-github-actions)

| Check | Status | Severity | Detail |
|---|---|---|---|
| CI configuration exists | ❌ fail | 🔴 CRITICAL | No CI/CD pipeline configuration found (checked GitHub Actions, GitLab CI, CircleCI, Azure Pipelines, Jenkins, Buildkite). |
| Pipeline runs automated tests | ❌ fail | 🔴 CRITICAL | Cannot verify test execution — no CI pipeline exists. |
| Test command defined in project manifest | ✅ pass | ℹ️ INFO | package.json defines a `test` script: `pnpm prettier:check`. |

**Recommendations:**
- **CI configuration exists:** Add a CI workflow (e.g. .github/workflows/ci.yml) that runs on every pull request: install deps, lint, typecheck, run tests, and build. Without this, broken code can merge to main undetected.
- **Pipeline runs automated tests:** See ci-1.

### Structured Logging & Observability
_Structured, queryable logs plus error tracking so failures are visible before a customer reports them._

Best practice reference: [https://sre.google/sre-book/monitoring-distributed-systems/](https://sre.google/sre-book/monitoring-distributed-systems/)

| Check | Status | Severity | Detail |
|---|---|---|---|
| Error tracking / APM configured | ❌ fail | 🔴 CRITICAL | No error-tracking or APM SDK (Sentry, Datadog, OpenTelemetry, etc.) found in dependencies. |
| Structured logging library configured | ❌ fail | 🟠 HIGH | No structured logging library found in dependencies. Detected ~7 raw console/print call(s) across the codebase instead. |
| Health-check endpoint exposed | ❌ fail | 🟡 MEDIUM | No /health or /healthz endpoint found. |
| Request/correlation ID propagation | ⚠️ warn | 🔵 LOW | No request/correlation/trace ID handling detected. |

**Recommendations:**
- **Structured logging library configured:** Adopt a structured logger (pino/winston for Node, structlog/loguru for Python) emitting JSON logs with level, timestamp, request/trace ID, and context fields. Unstructured console/print logs can't be reliably queried, alerted on, or correlated across services in production.
- **Error tracking / APM configured:** Without exception tracking, production errors are only visible if a user reports them. Add Sentry (or an equivalent APM) with server AND client-side capture, plus alerting on error-rate thresholds.
- **Health-check endpoint exposed:** Expose a lightweight health-check route that verifies critical dependencies (DB, cache, third-party APIs) so load balancers, container orchestrators, and uptime monitors can detect failures and auto-restart or fail over.
- **Request/correlation ID propagation:** Propagate a request/trace ID through logs and downstream calls so a single user-facing error can be traced across services.

### Secrets & Environment Management
_Environment-specific configuration and secrets kept out of source control and rotated correctly._

Best practice reference: [https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)

| Check | Status | Severity | Detail |
|---|---|---|---|
| Environment-specific configuration separation | ⚠️ warn | 🟡 MEDIUM | No clear separation between dev/staging/production configuration was found. |
| Environment variable template committed | ✅ pass | ℹ️ INFO | Found .env.example. |
| .gitignore excludes env files | ✅ pass | ℹ️ INFO | `.gitignore` excludes .env* files. |
| No real .env files committed to git | ✅ pass | ℹ️ INFO | No non-template .env files are tracked by git. |
| No hardcoded secrets in source | ✅ pass (text match — verify by hand) | ℹ️ INFO | No obvious hardcoded secret patterns in 72 tracked + untracked code/config files (pattern-based scan of the working tree only — not git history; not a substitute for gitleaks/truffleHog). |

**Recommendations:**
- **Environment-specific configuration separation:** Confirm staging and production use distinct secrets/config (not just different .env values on the same box), managed via your deploy platform's environment dashboard or a secrets manager — never share production credentials with lower environments.

### Resilience & Failover
_Documented and mechanical safeguards (runbooks, rollback, rate limiting, migrations) for when something breaks in production._

Best practice reference: [https://sre.google/sre-book/postmortem-culture/](https://sre.google/sre-book/postmortem-culture/)

| Check | Status | Severity | Detail |
|---|---|---|---|
| Runbook / incident-response docs present | ❌ fail | 🟠 HIGH | No runbook, incident-response, or disaster-recovery documentation found. |
| Rollback/backup procedure documented | ⚠️ warn | 🟡 MEDIUM | No rollback or backup procedure documented in README. |
| Rate limiting / throttling implemented | ❌ fail | 🟡 MEDIUM | No rate limiting or throttling mechanism detected. |
| Schema migration tooling in place | ⚠️ warn | 🔵 LOW | No formal migration tooling detected — schema changes may be applied ad hoc. |

**Recommendations:**
- **Runbook / incident-response docs present:** Document what to do when the service degrades or fails: who's paged, how to roll back a deploy, how to fail over the database, and how to communicate status. Without this, an outage becomes a fire drill instead of a checklist.
- **Rollback/backup procedure documented:** Document how to roll back a bad deploy and how database backups/restores work, including RTO/RPO expectations.
- **Rate limiting / throttling implemented:** Add rate limiting on public/authenticated API routes to prevent abuse, runaway costs (especially for LLM/API-billed endpoints), and cascading overload during traffic spikes.
- **Schema migration tooling in place:** Adopt versioned, reversible schema migrations so production database changes are repeatable and auditable, and can be rolled back if a deploy fails.

### Multi-Surface Deployment & Coordinated Rollback
_Whether a bad deploy across more than one independently-rollback-able surface (frontend host, backend/BaaS, database migration step) can be reverted as one coordinated action instead of desyncing._

Best practice reference: [https://vercel.com/docs/deployments/rollback-production-deployment](https://vercel.com/docs/deployments/rollback-production-deployment)

| Check | Status | Severity | Detail |
|---|---|---|---|
| Multi-surface deployment risk | ✅ pass | ℹ️ INFO | Single deploy surface detected (vercel). Standard rollback documentation (see Resilience & Failover) is sufficient — there is no second surface that can drift out of sync. |

### Testing & Quality Gates
_Automated test coverage and static analysis that catch regressions pre-release._

Best practice reference: [https://martinfowler.com/testing/](https://martinfowler.com/testing/)

| Check | Status | Severity | Detail |
|---|---|---|---|
| Automated test files exist | ❌ fail | 🔴 CRITICAL | No test files found anywhere in the repository. |
| Test runner configured | ⚠️ warn | 🔵 LOW | No explicit test runner configuration file found. |
| Coverage tracking configured | ⚠️ warn | 🔵 LOW | No test coverage configuration/threshold detected. |
| Static type checking enforced | ✅ pass | ℹ️ INFO | tsconfig.json has strict mode enabled. |

**Recommendations:**
- **Automated test files exist:** Add automated tests before production release — at minimum, cover critical business logic, payment/billing paths, and auth flows. Zero test coverage is a direct release blocker.
- **Coverage tracking configured:** Track coverage (even informally) so you know which critical paths are untested before shipping.

### Dependency & Supply-chain Security
_Reproducible, patchable dependency management._

Best practice reference: [https://docs.github.com/en/code-security/dependabot](https://docs.github.com/en/code-security/dependabot)

| Check | Status | Severity | Detail |
|---|---|---|---|
| CI runs a dependency vulnerability scan | ⚠️ warn | 🟡 MEDIUM | No dependency vulnerability scan (npm audit / pip-audit / Trivy / Snyk) found in CI. |
| Automated dependency updates configured | ⚠️ warn | 🔵 LOW | No Dependabot/Renovate configuration found. |
| Dependency lockfile committed | ✅ pass | ℹ️ INFO | Found lockfile: pnpm-lock.yaml. |

**Recommendations:**
- **Automated dependency updates configured:** Enable Dependabot or Renovate so security patches for dependencies land automatically instead of accumulating silently.
- **CI runs a dependency vulnerability scan:** Add an automated vulnerability scan step to CI so known-CVE dependencies are flagged before release.

## Methodology

This tool performs static analysis of the repository working tree (via `git ls-files` where available) — no code execution, no network calls, no dependency installation. Secret detection uses pattern matching and is not a substitute for a dedicated secret-scanning tool (e.g. gitleaks/truffleHog) run against full git history. Re-run after remediation to confirm fixes and track score over time.

Best-practice sources used to define these checks:
- [The Twelve-Factor App](https://12factor.net/)
- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [Google SRE Book](https://sre.google/sre-book/table-of-contents/)
- [GitHub Actions documentation](https://docs.github.com/en/actions/learn-github-actions)
- [GitHub Dependabot documentation](https://docs.github.com/en/code-security/dependabot)
- [Martin Fowler on Testing](https://martinfowler.com/testing/)
