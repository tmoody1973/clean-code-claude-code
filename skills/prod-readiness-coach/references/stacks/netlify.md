# Stack adapter: Netlify

_last_verified: 2026-08-20_. Platform facts below were checked against vendor docs on this date.

Load this file when `stack_fingerprint.adapters_matched` includes `netlify`.

## Rollback mechanics

- **Dashboard:** Deploys tab → select a previous successful deploy → "Publish deploy" button.
  Instant, no rebuild
  ([Netlify docs](https://docs.netlify.com/deploy/manage-deploys/manage-deploys-overview/)).
- **CLI/API:** there is no dedicated `netlify rollback` command. The documented mechanism is
  the generic escape-hatch API call: `netlify api restoreSiteDeploy --site-id=... --deploy-id=...`.
  If a fix brief needs a scriptable rollback step for Netlify, use this exact command form, don't invent a `netlify rollback` subcommand that doesn't exist.

## Important nuance: a failed build has nothing to roll back

If the most recent deploy attempt failed to build, it never went live. The previous good
deploy is still serving traffic. In that case there is nothing to "roll back": the correct
action is to fix the failing build, not to publish an older deploy that's already live
([Netlify deploy skill reference](https://tessl.io/registry/skills/github/netlify/context-and-tools/netlify-deploy)).
Don't recommend a rollback procedure as the fix for a failed-build incident, diagnose the
build failure instead.

## The paired rollback trap, Netlify edition

If this repo uses Netlify's managed database (Netlify DB), publishing a previous deploy does
**not** automatically restore the database from a backup, reverting the app's deployed code
and reverting its data are two separate actions
([Netlify backup/recovery docs](https://docs.netlify.com/build/data-and-storage/netlify-database/backup-and-recovery/)).
This is the same failure pattern as the Vercel+Convex trap covered in the `convex` and
`nextjs-vercel` adapters. If `stack_fingerprint.multi_surface` is true because Netlify is
paired with any backend/database surface, name this specific gap in the Multi-Surface
category narrative rather than a generic "make sure backups exist" line.

## Agentic-safety notes for this stack

- CI/agentic Netlify CLI usage should authenticate via the `NETLIFY_AUTH_TOKEN` environment
  variable, not an interactive `netlify login`.
- Confirm a deploy actually succeeded (reached "Published" state) before treating it as a
  valid rollback target, don't assume the most recent entry in deploy history was live.
