# Stack adapter: Cloudflare Workers

Load this file when `stack_fingerprint.adapters_matched` includes `cloudflare-workers`.

## Rollback mechanics

- `wrangler rollback [version-id]` rolls back a Worker; omitting the version ID defaults to
  the previous deployment
  ([Cloudflare rollback docs](https://developers.cloudflare.com/workers/versions-and-deployments/rollbacks/)).
- Up to 100 previous versions are retained for rollback, increased from 10 in September 2025
  ([Cloudflare changelog](https://developers.cloudflare.com/changelog/post/2025-09-11-increased-version-rollback-limit/)).
  If the audit is being run against an older mirror of these docs or a repo with tooling
  written before that change, don't assume only 10 versions are available — the current limit
  is 100.

## The gap: `wrangler.toml` config is not covered by rollback

`wrangler rollback` reverts the Worker's **code** at the edge. It does **not** revert changes
to `wrangler.toml` — routes, bindings (KV namespaces, D1 databases, R2 buckets, environment
variables, etc.) are not part of what gets rolled back
([Cloudflare docs](https://developers.cloudflare.com/workers/versions-and-deployments/rollbacks/),
confirmed in
[this community thread](https://community.cloudflare.com/t/worker-routes-in-wrangler-toml-not-included-in-worker-rollback/647173)
about routes specifically). If a bad deploy changed a binding or route alongside the code, a
`wrangler rollback` alone leaves that change in place. Any coordinated-rollback narrative for
this stack needs to explicitly call out config/binding drift as a second thing that must be
manually reverted — it is not automatic.

## Agentic-safety notes for this stack

- Authenticate CI/agentic `wrangler` invocations via the `CLOUDFLARE_API_TOKEN` environment
  variable. `wrangler login` opens an interactive browser OAuth flow and will hang or fail in
  a non-interactive environment.
- Before recommending `wrangler rollback` as an automated remediation step, confirm the
  deployment has version history to roll back to (a first deploy has nothing to roll back to).
