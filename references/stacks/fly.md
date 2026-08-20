# Stack adapter: Fly.io

_last_verified: 2026-08-20_. Platform facts below were checked against vendor docs on this date.

Load this file when `stack_fingerprint.adapters_matched` includes `fly`.

## There is no `fly rollback` command

This is the single most important fact for this adapter, and it directly contradicts what an
LLM might assume by analogy to Vercel/Cloudflare. Multiple Fly.io community threads confirm no
dedicated rollback command exists
([#2082](https://community.fly.io/t/rollback/2082),
[#4586](https://community.fly.io/t/manual-rollback-to-earlier-version/4586),
[#24312](https://community.fly.io/t/how-to-delete-old-releases/24312)). A third-party wrapper
CLI ([fly-rollback-cli](https://github.com/sudhanshug16/fly-rollback-cli)) exists specifically
to fill this gap — its existence is itself evidence that the platform gap is real and commonly
felt.

**Never write a fix brief or manual-steps list that says "run `fly rollback`."** That command
does not exist and an agent or human following the brief will hit an error.

## The actual rollback procedure

Per [Fly's own rollback guide](https://fly.io/docs/blueprints/rollback-guide/):

1. `fly releases --image` — lists previous release image hashes for the app.
2. `fly deploy -i <image-name>` — redeploys that exact previous image.

This is a full redeploy of an old image, not an instant routing-layer switch like Vercel's
rollback. Write fix briefs and runbook recommendations using this exact two-step procedure,
not a generic "roll back to the previous deploy" instruction.

## Migrations are not undone by redeploying an old image

Fly apps commonly run schema migrations via `release_command` in `fly.toml`, executed once per
deploy before the new release goes live. Redeploying an older image via the procedure above
does **not** reverse a migration that already ran against the database — the database state
stays at whatever the most recent `release_command` left it at. If this repo's
`stack_fingerprint.migration_tooling` shows any migration tool alongside a `fly` deploy
surface, treat this as a first-class multi-surface risk: the "surfaces" here are the app
release and the database schema, and they do not roll back together. Cite this explicitly
rather than folding it into a generic "document your rollback procedure" note.

## Agentic-safety notes for this stack

- `fly deploy` and `fly releases` require an authenticated `flyctl` session. In CI/agentic
  contexts, authenticate via the `FLY_API_TOKEN` environment variable, not an interactive
  `fly auth login` (which opens a browser flow).
- Before recommending `fly deploy -i <image>` as an automated remediation step, confirm the
  target image hash actually exists in `fly releases --image` output for this app — don't
  fabricate or guess an image reference.
