# Stack adapter: Next.js on Vercel

Load this file when `stack_fingerprint.adapters_matched` includes `nextjs-vercel`
(requires both the `vercel` deploy surface AND the `nextjs` framework detected).
Use it to write accurate, stack-specific prose on top of the generic audit findings —
do not repeat the generic checklist language when this file has a more precise fact.

## Rollback mechanics

- The rollback command is `vercel rollback <deployment-url-or-id>`. It operates at the
  routing layer only — no rebuild — and typically completes in about 60 seconds
  ([Vercel CLI rollback docs](https://vercel.com/docs/cli/rollback)).
- **Plan gate:** Hobby plan can only roll back to the *immediately previous* production
  deployment. Pro/Enterprise can target any past deployment. Do not write a fix brief that
  assumes arbitrary-target rollback without confirming the plan tier first
  ([rollback production guide](https://vercel.com/docs/deployments/rollback-production-deployment)).
- `vercel promote <url>` undoes a rollback or promotes any deployment; add `--yes` to skip
  the interactive confirmation prompt when this needs to run non-interactively (CI, or an
  agent acting on the user's behalf).
- Because Instant Rollback does not rebuild, it does **not** refresh environment variables —
  the rolled-back deployment runs with whatever env vars were baked in at that deployment's
  *original* build time. If an env var was rotated since, the rolled-back version is running
  with the old value. Flag this explicitly if a fix brief mentions secret rotation.

## The critical gap: database/backend state is not rolled back

Vercel's rollback reverts **application code only**. It does not touch a database, a paired
BaaS (see the `convex` adapter if Convex is also detected), or any external service state
([documented explicitly here](https://salsadocs.vercel.app/docs/deployment/updates), under
"Database Migrations Are Not Rolled Back"). If the fingerprint shows `multi_surface: true`
with Vercel plus any backend surface, this is exactly the failure mode the Multi-Surface
Deployment & Coordinated Rollback category exists to catch — cite this fact directly in that
category's narrative rather than a generic "make sure your rollback plan is documented" line.

## Observability gotchas specific to this stack

- **Sentry's setup command is an interactive CLI wizard:** `npx @sentry/wizard@latest -i nextjs`
  ([Sentry Next.js docs](https://docs.sentry.io/platforms/javascript/guides/nextjs/)). It
  prompts for project/org selection. Never suggest running this command inside an agentic or
  CI pipeline step expecting it to complete unattended — it will hang waiting for input. If a
  fix brief needs Sentry added, either instruct a human to run the wizard interactively once,
  or hand-write the three runtime config files it would have generated (client, server, edge).
- Sentry's own SDK is edge-safe: it supports `enableLogs: true` across all three Next.js
  runtimes (client/server/edge) via separate config files
  ([Sentry logs docs](https://docs.sentry.io/platforms/javascript/guides/nextjs/logs/)). So
  "add Sentry" is a safe recommendation everywhere in a Next.js app, including middleware/edge
  routes.
- **Generic Node loggers (pino, winston) break in the Edge Runtime.** pino throws
  `TypeError: pino.transport is not a function`; winston fails because `process.nextTick` is
  unsupported in Edge Runtime
  ([Next.js GitHub discussion](https://github.com/vercel/next.js/discussions/67213)). Root
  cause: both rely on Node worker threads/streams that don't exist in Edge Runtime, and pino
  is often flaky even in standard Vercel serverless functions due to how it gets bundled
  ([debugging writeup](https://medium.com/@sibteali786/debugging-pino-logger-issues-in-a-next-js-4e0c3368ef14)).
  If the audit's Structured Logging check recommends "adopt pino/winston" and this repo has
  any edge middleware or edge-runtime routes, downgrade that specific recommendation to
  Sentry's own logging or a fetch-based transport instead — don't repeat the generic advice
  verbatim.

## Agentic-safety notes for this stack

- **GitHub branch protection requires a paid plan for private repos.** Free tier only grants
  branch protection on *public* repositories
  ([GitHub docs](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches),
  confirmed in [this community thread](https://github.com/orgs/community/discussions/190190)).
  Never assume a CI/CD or release-gating recommendation that depends on branch protection is
  achievable for a private repo without confirming the org's GitHub plan first — probe (`gh api`
  or ask) or list it as a manual, plan-dependent item rather than an automatable fix.
- Vercel CLI actions in CI should authenticate via `VERCEL_TOKEN`, not an interactive
  `vercel login` — the latter opens a browser flow that hangs non-interactively.
