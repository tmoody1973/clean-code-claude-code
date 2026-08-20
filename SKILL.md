---
name: prod-readiness-coach
description: "Audits any code repository for production-readiness gaps (CI/CD pipeline, structured logging, error tracking, secrets management, CLAUDE.md/AGENTS.md, resilience/runbooks, multi-surface deployment and coordinated rollback risk, irreversible migrations, test coverage, dependency security) and produces two plain-English documents: a beginner-friendly audit explainer and a phase-gated Claude Code fix brief. Detects the repo's stack (frameworks, deploy platforms, runtimes) and loads matching stack-specific reference material so advice reflects real platform gotchas instead of generic checklist language. Use when a user asks to audit, check, or review a repo for production readiness, best practices, or launch-blockers, or asks to turn code-quality/DevOps findings into something a non-expert or self-taught (\"vibe coder\") developer can understand and act on."
license: MIT
metadata:
  version: '2.3'
  author: tarikmoody
---

# Production Readiness Coach

## When to Use This Skill

Use this whenever someone wants to know if their project is ready for
production, or wants a code-quality/DevOps audit translated into language a
self-taught or AI-assisted ("vibe coding") developer can actually learn
from — not just a checklist of jargon. Typical requests this matches:

- "Audit my repo for production readiness"
- "Is my app ready to launch? What am I missing?"
- "Check my CI/CD, logging, and secrets setup"
- "Explain what's wrong with my repo like I'm new to this"
- "Turn this audit into something I can hand to Claude Code"
- "Will rolling back a bad deploy actually undo everything?"

The goal is **two things at once**: an accurate technical audit, AND a
teaching moment. Every finding should leave the user understanding the
underlying concept, not just told to fix it.

## What This Skill Produces

1. **`AUDIT_PLAIN_ENGLISH.md`** — the findings explained in plain English:
   what was checked, what was found, why it actually matters in practice,
   and a short teaching explanation of the underlying concept. No
   unexplained jargon.
2. **`FIX_BRIEF_FOR_CLAUDE_CODE.md`** — an execution-ready brief the user
   can paste into Claude Code (or any AI coding agent) inside their repo.
   Split into severity phases with explicit acceptance criteria and a
   mandatory re-audit gate before the next phase starts, plus a separate
   "manual steps for a human" list for anything an AI agent should not
   attempt unattended.
3. (Optional, on request) **`audit-report.json` / `audit-report.md`** — the
   raw technical report from the underlying tool, for users who want the
   unfiltered file-level evidence, best-practice citations, and detected
   stack fingerprint.

## Step-by-Step Workflow

### 1. Ask the product-context question

Before running anything, ask (in your own words, one short question):
*"If this app lost data or went down for a full day, what's actually at
stake — mostly an inconvenience, or something with real consequences
(money, safety, someone's only copy of something)?"*

Skip this only if the user already volunteered enough context unprompted
(e.g. "this handles patient intake data"), explicitly says to skip it, or
no user is present to answer (autonomous run) — in that case omit
`--context` and say so in the audit's short version.
Store their answer verbatim — it gets passed to the audit tool via
`--context` and used in step 6 to decide which findings get emphasized in
the prose. **It never changes the deterministic score** — a `critical`
finding is `critical` regardless of context; the context only changes how
hard you lean on it in the writeup (e.g. a "no backups documented" finding
that's `medium` by default reads very differently once you know the app
holds people's only copy of their resume).

### 2. Identify the target repository

Ask (if not already clear from context):
- Which repo? Accept a local path, a `git clone`-able URL, or (if a GitHub
  connector/CLI is available) an `owner/repo` slug.
- If it's remote and not already checked out locally, clone it into the
  workspace first (shallow clone is fine — `git clone --depth 1`).

Don't ask about output format or tone — plain English + Claude Code brief
is this skill's whole point, always produce both unless the user
explicitly says they only want one.

### 3. Run the audit tool

The bundled script does all the technical detection AND the stack
fingerprinting — never hand-roll detection logic in prose; run the real
tool and translate its real output.

```bash
python3 {skill_dir}/scripts/prod_audit.py --repo /path/to/repo \
  --output /tmp/audit-<repo-name>.md --json /tmp/audit-<repo-name>.json \
  --context "{{the user's answer from step 1, verbatim, or omit the flag if skipped}}"
```

Read the JSON file (use the repo name in the path so parallel audits don't clash).

The tool guesses a **profile** (`web-app`, `api`, `worker`, `cli`,
`library`) from the stack and reports it in `stack_fingerprint.profile`
with `profile_source` (`guessed` or `given`). Checks that don't apply to
that profile come back as `status: "n/a"` and are left out of the score.
If the guess looks wrong for what the user described (e.g. they said
"it's a CLI" but the profile is `web-app`), re-run with
`--profile <kind>` before writing anything. Never list an `n/a` check as
a finding or a win. When unsure, the tool picks the stricter profile. Top-level fields that matter:
- `stack_fingerprint` — see step 4, this drives which adapter files to load.
- `product_context` — echoes back whatever you passed via `--context`.
- `categories` → each has `key`, `title`, `score`, and `checks`; each check has `id`, `title`, `status`
  (`pass`/`fail`/`warn`/`info`), `severity`, `detail`, `recommendation`,
  `evidence` (file paths/line snippets), `best_practice_ref` (a
  citation URL), and `confidence` (`verified` or `weak`). A `weak` pass
  means the tool only found matching text — write it up as "looks like
  this may exist; confirm by hand," never as a confirmed win.

This structured data is the ground truth for everything you write next —
never invent a finding that isn't in this JSON, and never soften a
`critical` into something less urgent regardless of `product_context`.

If the repo doesn't look like it matches any check's expectations well
(e.g. an unusual stack), spot-check a couple of surprising failures by
reading the actual files before writing them up — the tool is pattern-based
static analysis, not infallible.

### 4. Load fingerprint-matched stack adapters

Read `stack_fingerprint.adapters_matched` from the JSON — a list of stack
names like `["nextjs-vercel", "convex"]`. For each name in that list, read
`references/stacks/<name>.md`. Available adapters: `nextjs-vercel`,
`convex`, `fly`, `cloudflare-workers`, `netlify`.

These files sharpen and sometimes override the generic checklist language
with real platform facts: exact rollback commands, which config a rollback
does *not* cover, runtime-specific logging gotchas, and named "paired
rollback trap" patterns (e.g. Vercel+Convex, Netlify+its managed database)
where fixing one surface silently leaves the other out of sync. Use these
facts specifically in the **Multi-Surface Deployment & Coordinated
Rollback** category writeup and anywhere else they contradict or refine a
generic finding.

- If `adapters_matched` is empty, skip this step entirely — write the
  generic findings as-is. Don't guess at platform facts that aren't in an
  adapter file or in the JSON evidence.
- Never load an adapter that isn't in `adapters_matched` for this repo,
  even if you recognize the stack from the file list — the fingerprint is
  the single source of truth for what applies here.
- Each adapter file also has an "Agentic-safety notes" section — fold
  those directly into the fix brief's phase gates and the manual-steps
  list in step 7, don't leave them as trivia.

### 5. Load the writing references

Before drafting either document, read:
- `references/plain-english-glossary.md` — the term-by-term translation
  table and tone rules. Use it for every technical term that appears in
  the JSON `detail`/`recommendation` fields, including the newer
  multi-surface/rollback/migration terms.
- `references/report-templates.md` — the exact structure for both output
  documents, including the phase-gated fix-brief structure.

### 6. Write `AUDIT_PLAIN_ENGLISH.md`

Follow the Document 1 template in `references/report-templates.md`
exactly. Substance rules:
- Translate every finding through the glossary — a reader with zero DevOps
  background should understand every sentence without looking anything up.
- Lead with what's already working, named specifically and warmly, before
  the gaps — this is a coach, not an inspector.
- Order gaps critical → high → medium → low. For each, explain the real
  consequence (not "poses a risk" — say what actually happens) and teach
  the underlying concept in a short paragraph.
- Weave in `product_context` (step 1) when it changes how much a finding
  matters — name the actual stakes the user told you about, don't just
  restate the generic finding.
- Close with a "next-lesson roadmap": 3-6 ordered, achievable steps framed
  as skills to learn, not chores to finish.
- Calibrate urgency honestly — don't inflate a `low`/`warn` finding into
  something scary just because the product context sounds high-stakes.
  Part of the lesson is learning to triage; the JSON severity is the
  floor, the product context can only shift emphasis, not invent urgency.

### 7. Write `FIX_BRIEF_FOR_CLAUDE_CODE.md`

Follow the Document 2 template in `references/report-templates.md`
exactly — it's phase-gated by severity (Phase 1 = critical, Phase 2 =
high, Phase 3 = medium/low), each phase with acceptance criteria and a
hard gate ("re-run the audit and confirm zero remaining findings at this
severity before starting the next phase"). Substance rules:
- The "what to ask Claude Code to do" block per finding can and should use
  precise technical language and real file paths pulled from the JSON
  `evidence` field — that part is FOR the AI agent executing it.
- Everything else (the framing, the "why," the "what you'll learn") stays
  in the same plain-English voice as Document 1.
- Include a verification step for every fix so the user learns to confirm
  fixes rather than assume they worked.
- **Agentic-environment safety — apply these to every instruction you
  write, not just ones an adapter file happens to mention:**
  - Never write an instruction that runs an interactive setup wizard (a
    CLI that prompts for input, opens a browser for OAuth, etc.) as an
    unattended step. If a tool's only official setup path is interactive
    (e.g. Sentry's `@sentry/wizard`), either give the hand-written config
    equivalent or move it to the manual-steps list.
  - Before an instruction references a specific file path, config key, or
    command, confirm it actually exists in this repo's evidence/tree —
    never assume a file exists because it's conventional for the stack.
  - Never assume a paid-tier or plan-gated platform feature (private-repo
    branch protection, arbitrary-deployment rollback on Vercel Hobby,
    etc.) is available — either confirm the plan first or flag it as a
    manual, plan-dependent item.
  - Anything requiring a human judgment call with real consequences
    (choosing to run a destructive migration's "fix," deciding whether to
    restore from backup vs. redeploy) goes on the manual-steps list, never
    into a phase an agent might execute unattended.
- Name the detected stack from `stack_fingerprint` (not by re-guessing from
  package.json prose) so tool recommendations match reality.

### 8. Review both documents before sharing

- Scan for any leftover jargon that isn't immediately explained — if you
  used a technical term, either the glossary already covers it or you
  need to add a one-clause explanation inline.
- Confirm severity ordering and phase grouping matches the JSON (critical
  items must appear first, in Phase 1, and be unambiguous about urgency).
- Confirm every file path/evidence snippet quoted was actually present in
  the JSON output — never fabricate a file path.
- Confirm the manual-steps list actually captures everything flagged
  agentic-unsafe in steps 4 and 7 — this list existing and being accurate
  matters as much as the phases themselves.
- **Name the source of every fact that isn't in the JSON.** Plan tiers
  ("you're on Vercel Pro"), team size, traffic, who uses the app — if it
  came from the user, write "you told me"; if you read it from a file,
  name the file. Never state a platform or plan fact as if the tool found
  it when it didn't. If a fix depends on such a fact (e.g. rollback target
  range depends on plan), say so next to the fix.
- **If you upgrade a `weak` pass to a confirmed win, name the command you
  ran.** "I checked your full git history" must be backed by something
  like `git log --all -- .env` or `git grep` over history that you
  actually executed in this session. If you didn't run it, say the tool's
  scan was pattern-based and leave it at that. A claim of work is a
  finding; it gets the same evidence bar as any other.
- Never instruct the agent to open a real secrets file. If variable names
  are needed from `.env.local`, use `grep -o '^[A-Z_][A-Z0-9_]*' .env.local`
  so values never enter the agent's context.

### 9. Deliver

Share both markdown files. Mention the raw technical report/JSON exists
and offer it if the user wants file-level detail, the full stack
fingerprint, or wants to wire the tool into their own CI (`--fail-on
critical` exit code makes it CI-gateable).

## Notes on the underlying tool

`scripts/prod_audit.py` is a dependency-free Python 3 script (stdlib only)
that performs static analysis — no code execution, no network calls. It
first computes a **stack fingerprint** (languages, package managers,
frameworks, deploy surfaces + evidence, runtimes, migration tooling,
`multi_surface` flag + evidence, `adapters_matched`), then runs checks
across eight categories: AI Agent Context, CI/CD Pipeline, Structured
Logging & Observability, Secrets & Environment Management, Resilience &
Failover, **Multi-Surface Deployment & Coordinated Rollback**, Testing &
Quality Gates, and Dependency & Supply-chain Security.

The Multi-Surface category is the generalized version of the "paired
rollback trap" (e.g. Vercel+Convex, Netlify+its managed DB, a
docker-compose stack with a dedicated migration service): it flags when a
repo has more than one independently-rollback-able surface, checks whether
a coordinated rollback procedure is actually documented across all of
them, and separately flags irreversible-migration risk (destructive SQL
with no documented reverse procedure) — that last check runs for every
repo regardless of surface count, since a single-surface app can still
lose data permanently to a migration that a code rollback can't undo.

It works on any git repo regardless of language/framework — repos with no
recognized deploy platform still get a clean fingerprint (empty surfaces,
`multi_surface: false`) rather than a crash. See its own `--help` output
for CLI flags; the ones that matter here are `--json` (for this skill's
translation step), `--context` (for the product-context calibration in
step 1 — stored verbatim, never alters the score), and `--fail-on
critical` (for CI gating, worth mentioning to the user as a follow-up).

Secret detection is regex-based and intentionally conservative — always
tell the user it's not a substitute for a dedicated secret scanner
(gitleaks/truffleHog) run against full git history if any hardcoded-secret
finding shows up. Same caveat applies to the destructive-migration regex
in the Multi-Surface category — it catches common patterns
(`DROP TABLE`, `DROP COLUMN`, `TRUNCATE`, destructive `ALTER TABLE`), not
every way a migration can be irreversible.
