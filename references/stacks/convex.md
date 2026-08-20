# Stack adapter: Convex

Load this file when `stack_fingerprint.adapters_matched` includes `convex` (the `convex`
deploy surface alone is sufficient to match).

## Two runtimes, and they are not interchangeable

Convex ships two distinct execution runtimes:

- **Default runtime:** a custom V8-isolate sandbox (the same runtime family as Cloudflare
  Workers) with **no Node.js built-ins**. Every query and mutation runs here, always, with no
  opt-out. Actions also run here by default
  ([Convex runtimes docs](https://docs.convex.dev/functions/runtimes)).
- **Opt-in Node.js runtime:** enabled only by putting the `"use node"` directive at the very
  top of an *action* file. Queries and mutations can **never** use `"use node"` — that
  directive is action-only ([Convex actions docs](https://docs.convex.dev/functions/actions)).

Implication for the audit: if the Structured Logging & Observability category recommends a
Node-native logging or APM SDK (pino, `@sentry/node`, most classic Node instrumentation),
that recommendation is only valid for action files that have opted into `"use node"`. It is
categorically invalid for any query, mutation, or default-runtime action — those need a
fetch-based or edge-compatible transport instead. Don't let a generic "add a Node logger"
recommendation pass through unqualified for a Convex repo.

## The cost of moving to Node-runtime actions

Node-runtime actions lose direct database access — no `ctx.db` calls. They must instead go
through `ctx.runQuery` / `ctx.runMutation`, which round-trips back into the default runtime and
adds overhead. Convex's own best-practices guidance explicitly warns against overusing
`runAction` for this reason. Treat "just add `"use node"` everywhere" as a bad fix
recommendation — it should be scoped narrowly to the specific actions that actually need a
Node-only dependency.

Node-runtime actions also require a matching Node version — the default is Node 20
([Convex local deployments docs](https://docs.convex.dev/cli/local-deployments)). If a fix
brief adds a Node-only dependency to an action, note the Node version constraint so it doesn't
silently break in a different local dev environment.

## Rollback and the paired-surface trap

Convex does not have a single documented CLI "rollback deployment" command equivalent to
`vercel rollback` in the same sense — a `convex deploy` pushes both function code and any
schema changes together. When Convex is paired with a frontend host (most commonly Vercel —
see the `nextjs-vercel` adapter, and note this repo's own `vercel.json` typically runs
`npx convex deploy` as part of the Vercel build step), rolling back the frontend via
`vercel rollback` does **not** roll back whatever the Convex deploy already applied to the
backend schema/functions. This is the canonical instance of the "paired rollback trap" that
the Multi-Surface Deployment & Coordinated Rollback category is designed to catch — when
writing that category's narrative for a Convex+Vercel repo, be specific: state that a Vercel
rollback reverts the frontend to an older version that may now be calling a Convex schema/API
shape that no longer matches, and that the coordinated procedure must address which side moves
first and what compatibility window is required between them.

## Agentic-safety notes for this stack

- `npx convex deploy` (and the dev-time `npx convex dev`) can prompt for project selection on
  first run in an unconfigured environment. In CI/agentic contexts, ensure `CONVEX_DEPLOY_KEY`
  (or the equivalent deploy key env var for the target deployment) is set so the command runs
  non-interactively rather than assuming it will proceed unattended.
- Do not assume a Convex project is on a paid tier with extended log retention, scheduled
  function limits, or other quota-gated features when writing recommendations — Convex's free
  tier has real limits on things like function execution time and scheduled job frequency;
  flag tier-dependent recommendations as needing confirmation rather than presenting them as
  unconditionally available.
