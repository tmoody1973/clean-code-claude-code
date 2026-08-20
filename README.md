# prod-readiness-coach

A Claude Code skill that audits a repo for production gaps and explains the results in plain English.

It runs a static-analysis script over the repo, then turns the findings into two documents: one a beginner can read, and one you can paste into Claude Code to do the fixes in order.

## What it checks

- CI/CD pipeline (does anything test your code before it ships)
- Structured logging and error tracking
- Secrets and environment handling
- A `CLAUDE.md` or `AGENTS.md` for AI agents
- Runbooks, health checks, rollback notes
- Multi-surface deploys (for example Vercel plus Convex) where rolling back one side leaves the other out of sync
- Irreversible database migrations
- Test files and quality gates
- Lockfiles and dependency update bots

The script detects the stack (Next.js, Convex, Fly, Netlify, Cloudflare Workers) and loads a matching reference file with real platform facts, such as what `vercel rollback` does not undo.

## What you get

1. `AUDIT_PLAIN_ENGLISH.md`. Each finding with what was checked, what was found, why it matters, and a short lesson on the concept.
2. `FIX_BRIEF_FOR_CLAUDE_CODE.md`. Fixes grouped into phases by severity. Each phase has acceptance criteria and a gate: re-run the audit before moving on. Anything an AI agent should not do alone (interactive wizards, paid-tier features, destructive choices) goes on a separate manual list.
3. Optional raw report as Markdown or JSON.

## When to run it

Run the audit the day a project first goes live. Not before: while you are still sketching, tests change daily and a robot checking sketches slows you down. Not after: the moment a real person or a scheduled job depends on the app, a broken push has real cost. A simple trigger is "the same day you connect Vercel." Run it again before any launch, any schema change, and whenever you hand the repo to someone else.

## Install

Copy this folder into your Claude Code skills directory:

```bash
git clone https://github.com/tmoody1973/prod-readiness-coach.git ~/.claude/skills/prod-readiness-coach
```

Then ask Claude Code something like "audit this repo for production readiness."

## Run the script on its own

No dependencies beyond Python 3.

```bash
python3 scripts/prod_audit.py --repo /path/to/repo --output report.md --json report.json
```

Useful flags:

- `--context "..."` passes a one-line note about what is at stake (used to shape the prose, never the score)
- `--profile cli` tells the tool what kind of project this is (see Profiles)
- `--fail-on critical` exits non-zero if any critical finding remains, so you can use it in CI

## Scoring

Each category starts at 100 and loses points per failing check. The overall score is the average. The penalty weights are inherited, not calibrated (see `docs/decisions/004`), so treat the number as a progress meter for one repo, not a way to compare two repos. The letter grade is capped at D whenever a critical finding exists, so a repo with no CI and no error tracking cannot show as "nearly ready" just because its other categories are clean.

## Profiles

Not every check fits every repo. A command-line tool has no health endpoint. Pass `--profile` with one of `web-app`, `api`, `worker`, `cli`, or `library`. Checks that do not apply are marked `n/a` and left out of the score. If you omit the flag the tool guesses from the stack and prints its guess at the top of the report. When the guess is unsure it picks `web-app`, the strictest profile, because a false failure is cheaper than a skipped real check.

## Confidence

Every check carries a `confidence` value. `verified` means a file, config, or dependency exists. `weak` means the tool only matched text, such as the word `rate_limit` in a source file. A weak pass shows as "verify by hand" in the report. It is a clue, not proof. Comment lines are skipped, so a TODO does not count as an implementation.

## Limits

The script reads files. It does not run your app. Secret detection is a conservative regex over tracked and untracked code and config files in the working tree. It does not read git history, so it is not a replacement for gitleaks or truffleHog. The destructive-migration check catches common SQL patterns, not every way a migration can lose data.

## Tests

```bash
python3 -m unittest discover tests
```

## Layout

```
SKILL.md                         instructions Claude follows
scripts/prod_audit.py            the audit tool
references/plain-english-glossary.md
references/report-templates.md
references/stacks/               per-platform facts and agent-safety notes
tests/
```

## License

MIT. See [LICENSE](LICENSE).
