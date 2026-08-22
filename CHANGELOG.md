# Changelog

## 3.5.2

A developer-experience audit of the toolkit itself: install it fresh, run the CLI, break it on purpose, read every doc link. Four things it found.

**An empty folder used to get a grade.** Pointed at a directory with nothing in it, the tool reported "Repository Controls Score: 65/100, D, release blockers present" with four CRITICAL findings, and never said the folder was empty. A mistyped path produced a confident report about nothing, which is the same failure 3.5.1 shipped three fixes for. It now refuses: it says what is wrong, says to pass `--repo .` instead, and exits 2. **This is a behavior change.** A pipeline pointed at a path with no files used to exit 0 and now exits 2. See `docs/decisions/008`.

**A folder that is not a git repository now says so, at the top of the report.** The scan still runs, because there are real files and the findings mean something, but `git ls-files` is unavailable, so `.gitignore` is not applied and `node_modules` or build output can be read as source. That caveat now appears above the score instead of nowhere.

**The toolkit shipped ten files its own linter rejects.** `check_report.py` refuses em and en dashes in generated documents. Eight shipped files contained em dashes, including `plain-english-glossary.md`, the file that defines the plain-English house style, and all five stack reference files. Two contained en dashes. The 3.5.0 entry claiming em dashes were "gone from every skill, command and template" was true of those three directories and never covered `references/`. All ten are fixed, and `validate-toolkit.sh` now enforces the rule, so it cannot come back. The rule was previously enforced only on documents the tool generated, never on the documents it ships.

**`add-clean-code.sh --help` was a dead end.** It printed "Unknown option: --help" and exited 64. The usage text already existed as a comment at the top of the same file and was never printed. `--help` and `-h` now print it and exit 0, and an unknown flag prints it too.

Tests: 92.

## 3.5.1

Five defects, and one thing underneath all of them: the engine only really knew Node. Two of these were saying something false about any repository a user ran them on today.

**`auth-2` was wrong about half the time it spoke.** On a live application it reported "18 of 25 request handlers never mention an auth check" as a HIGH finding. At least 14 of the flagged files were authenticated, by three mechanisms a word search could not see: middleware that guards every route not on a public list, webhook routes that verify a cryptographic signature because the caller is a machine and cannot hold a browser session, and routes that compare a shared secret from the environment. The check now recognizes all three. When it finds request middleware it stops asserting the handlers are unguarded and instead reports, at LOW, that they rely on the middleware, naming the file and listing the public route patterns it found so a person can confirm the matcher in about a minute. On the same application the finding is now 9 of 25, and each of the 9 is genuinely middleware-dependent. `auth-3`, which found a real fail-open owner check, is unchanged. See `docs/decisions/006`.

**`package_json()` broke every repository that is not JavaScript.** A monorepo change in 3.2.3 made it always return a dict of empty sections, and that dict is truthy, so all seven `if pkg:` callers thought a manifest existed. A Go project was reported as `languages: ['go', 'javascript']` and told, at HIGH, "package.json exists but does not define a `test` script", about a file that was not there. It now returns nothing when there is no manifest and no workspace members.

**Python and Go fixtures, and the two failures they found immediately.** Every meaningful fixture in the suite was a JavaScript repository, which is why none of the above was caught. Adding a FastAPI service and a Go service surfaced two more on the first run: dependencies declared PEP 621 style in `pyproject.toml`, quoted inside an array, were parsed as nothing, so `fastapi-users` was invisible and the service was told it had no authentication at all. Both call sites now share one dependency-name parser. And a health route declared in code, `@app.get("/health")` or `r.Get("/health", ...)`, which is how every framework except Next.js declares one, was invisible to a check that only globbed file paths. It now reads code declarations too, marked as weak evidence because a path in a string is not proof the route answers.

**Lint and typecheck steps outside Node.** `ci-3` knew `eslint`, `ruff`, `flake8`, `pylint`, `tsc` and `typecheck`. A pipeline running `mypy app` was told it had no lint or typecheck step. Added: `mypy`, `pyright`, `black --check`, `golangci-lint`, `go vet`, `gofmt`, `staticcheck`, `rubocop`, `clippy`, `cargo fmt`, `dotnet format`, `ktlint`, `detekt`, `checkstyle`, `phpstan`, `psalm`, `biome`, `oxlint`, `prettier --check`.

**The "any language" claim is retired.** `SKILL.md` said "It works on any git repo regardless of language/framework." Repository-level checks do. Stack-specific ones are strongest on Node and Next.js, good on Python, and have no rules for Go, Rust, Ruby, Java, PHP or C#. Both `SKILL.md` and `README.md` now say which is which and name the four specific gaps. This toolkit's whole thesis is that a tool must not overstate what it checked; that sentence was the tool overstating where it looked. See `docs/decisions/007`.

**The two readiness skills are distinguishable at a glance.** Both descriptions used to open with audit and production-readiness language, and a tester reported that Claude could not reliably choose between them. They now open with the actual split: `prod-readiness-coach` scans repository controls and scripts, `product-readiness-review` judges user journeys and product behavior. The coach's description also lists Access Control, which has been one of its nine categories since 3.5.0 and was missing from the list.

**Tests now have to prove a check stays quiet.** Every one of the 68 existing tests asked only "does this check fire". None asked "does it stay silent when it should", which is precisely the hole `auth-2` fell through. Borrowed from KICS, which refuses a rule that ships without a negative fixture, and from Checkov, which requires both a passing and a failing case. `auth-2` now has four silence tests: middleware-protected, signature-verified, shared-secret, and correctly-fired.

Tests: 86.

## 3.5.0

3.4.0 made the engine honest about what it found. This release is about what it was never looking at, and about the toolkit holding together as one thing.

**Access Control, a new category. The tool shipped three versions with no authentication check at all.**
- `auth-1`: is there an authentication mechanism, and which one.
- `auth-2`: do request handlers consult an identity, or serve anyone who reaches the URL. Reported as a text match, because mentioning a guard is not the same as being guarded.
- `auth-3`: does a permission check grant access when its own environment variable is unset. Real code rarely tests the variable inline, so the check learns the local names first, then looks for the fail-open branch on them.
- Why it matters: this was written the same afternoon an independent review of a live application found a send endpoint reachable by any signed-in user and an owner check returning true when its variable was unset. The audit had graded that repository "A, strong evidence of controls". It now quotes the exact line and grades it D.

**Warnings cost points.** Eight checks reported as `warn` with a severity badge and subtracted nothing, so a repository could display three MEDIUM findings and still score 100 in those categories: 55 points shown but not counted. A warning now costs half of the same finding failing. Less certain, never free.

**The installer can deliver a correction.** `/add-clean-code` printed "already installed" and exited 0 without comparing anything, so the going-live rule corrected in 3.2.1 could never reach anyone who installed before it. The managed block now carries a version; a re-run diffs it and exits 3 when an update is available; `--update` replaces only the block between the markers; `--check` reports without touching anything. The dangling "that day" left in the template by the 3.2.1 edit is fixed.

**The editing skill now says what its verification is worth.** `boy-scout-cleanup` claimed "behavior-preserving" while `/refactor`, its sibling with the same risk, carried the discipline that makes such a claim meaningful. A mutation test showed three of four real behavior changes passing a green suite. The skill now requires an undo to exist, requires checking that the suite covers the behavior being touched, and requires saying which evidence was used.

**Every skill was run once against a real repository by an independent tester, and every one came back "partly works".**
- `clean-code-scaffold` invented a stack on an empty directory without saying it was guessing, and produced a scaffold that failed on first run. It now asks when there is nothing to detect, and runs what it built the way its own README says to.
- `developer-handoff` scoped verification to setup commands, and its template's empty sections pulled toward filling them. It now marks each statement as ran it, read it, or told to me, and deletes sections with no referent.
- `product-readiness-review` promised in its description to run the coach first and never mentioned it in the workflow, called builds "safe" when they write into the repository, and judged against a milestone it never asked for. All three fixed.
- `clean-code-review` never said where the review goes.

**House style.** Em dashes are gone from every skill, command and template, so the report linter no longer rejects text this toolkit ships.

Tests: 68.

## 3.4.0

An audit of the auditor. A deliberately hollow repo, every control a costume, scored 78 out of 100 with nine passing checks, five of them false. Fixing that exposed more.

**Confidence now follows evidence, structurally.**
- A pass with an empty evidence list can no longer claim to be `verified`. The downgrade is automatic, so the hand-maintained `WEAK_PASS_IDS` set no longer has to be remembered when a check is added.
- Checks that always had real evidence now carry it: `log-1` and `log-2` cite the matched dependency, `dep-1` the lockfile, `ci-6` the script, `res-2` the matching line. `sec-3`, `sec-4` and `ms-1` cite the scope they searched, which is the honest evidence for a proof of absence.

**Existence is not function.** Six checks passed on controls that existed in name only.
- `ci-2` (critical) was satisfied by a CI step of `echo "test skipped"`. It now requires a real test-runner invocation, with string literals stripped first.
- `ci-6` was satisfied by a `test` script of `echo "no tests yet" && exit 0`.
- `res-1` was satisfied by an empty `runbook.md`. It now requires 50 words of prose.
- `res-2` was satisfied by an unchecked `- [ ] figure out rollback` TODO box.
- `ms-2` was a bag-of-words test marked verified; it is now labelled a text match.
- `log-1`/`log-2` matched substrings of a serialized dependency blob, so `@types/pino` scored a verified pass. They now match package names, excluding type stubs.

**Security: the waiver file is untrusted input.** `.prod-audit-waivers.json` lives in the audited repo, and its text was written into the Markdown report unescaped. A crafted `reason` field forged a second `## Repository Controls Score: 100/100` heading in the report. Waiver text is now flattened to a single length-capped line with pipes escaped and leading markup stripped, at the point it is loaded rather than at each render site.

**The generated documents are now linted.** `scripts/check_report.py` checks a finished audit against the JSON it was written from: a quoted file path must appear in the scan, a `weak` pass must not be written up as a win, every `critical` must be addressed in the fix brief, a waived finding must stay visible, no placeholders, no em dashes. The skill runs it before sharing. Run against real generated documents that had already been reviewed by hand, it found six problems.

**Refactor.** `prod_audit.py` was 1836 lines, more than twice this project's own 800-line ceiling, with three hand-maintained tables far from the checks they described. It is now an `audit/` package of eight modules, largest 503 lines, plus a thin entry point that re-exports the public names so every documented command and import keeps working. 77 unused imports removed.

**House style.** Em dashes are gone from every generated string, so the report linter no longer rejects the documents this toolkit produces.

Tests: 59, up from 37.

Known and not yet fixed: `claude plugin eval` is in early access and could not be run, so the five prompt-only skills still have no automated coverage. Each was tested once by hand against a real repository; the findings are tracked for 3.5.0.

## 3.3.0

Two verified defects in how the coach treats evidence, and the trap they created in the fix brief.

- **Waivers.** A control can live outside the repository (an org-level pipeline, a platform dashboard, a vault). Before this, `--fail-on critical` could never reach 0 for such a repo, so the phase gate demanded something impossible and quietly rewarded faking the fix. `.prod-audit-waivers.json` now records a human's dated, evidenced acceptance of a real finding. Every field is required, rejected entries are printed, waivers expire after 180 days, and every report lists what was waived and who accepted it. Claude is instructed never to write this file itself.
- **A text match can no longer be celebrated as a win.** A category whose only pass rested on a grep hit could score 100 and be written up under "What's already solid." Categories now carry `has_weak_evidence`, the report table marks them "(text match only)", and the template routes them to a separate "Looks fine, but only from a text match" section.
- **Conflicting signals are now reported.** New `contradictions` array names pairs where one check's pass is undercut by another's failure: a clean secret scan with no `.gitignore` guard, request IDs with no logger, test files no pipeline runs, a rollback doc that does not cover every surface. The fix brief must resolve these before its phases.
- Tests: 37.

## 3.2.3

- Bug fix from a real repo: monorepos were read as if only the root `package.json` existed. Workspace members (`apps/*`, `packages/*`, `services/*`) now contribute dependencies, scripts, and platform config (`vercel.json`, `fly.toml`, `netlify.toml`, `wrangler.*`, `render.yaml`, `Procfile`, `convex/schema.*`).
- A Dockerfile inside one workspace member no longer blocks the Vercel inference for a Next.js app in another.
- Found on `tmoody1973/annotated`: before, frameworks `[]` and no adapters; after, Next.js + Convex + Fastify, surfaces Vercel + Fly + Convex, all three adapters, multi-surface rollback finding raised.
- Tests: 27.

## 3.2.2

- Consistency patch, no new features.
- A category whose checks are all n/a now reports `score: null` and shows `N/A`, never 100/100; the template only counts applicable categories as wins.
- `.env.example` is required only when the code reads environment variables; otherwise the check is n/a.
- Every remaining "add CI on launch day" phrase updated to "before the first shared or live deployment."
- Profile docs and the code comment now match the code: language alone is `unknown`.
- Example no longer says "no CI of any kind" or that a red check "cannot go live."
- Fix-brief rule: existing paths must be verified; new paths are allowed, labeled as new, and justified by repo conventions.
- Skill-level README reduced to a pointer so there is one place for user-facing docs.
- Tests: 25.

## 3.2.1

- Accuracy pass, no new features.
- Example report: claims now match what the scanner proved ("no obvious secret patterns in scanned files; history not checked"), and the audited commit SHA is recorded.
- SKILL.md: the JSON is the record of what the scanner observed, not "ground truth." Surprising critical/high findings must be verified; a finding may be downgraded only with named evidence.
- A detected language with no framework or deploy surface is now `unknown`, not `web-app`.
- The scanner requires Python 3.9+ and says so instead of failing silently.
- README: CI wording no longer overpromises ("passing CI raises confidence; branch protection is what blocks"), and the timing rule is "before the first shared or live deploy, earlier with tests or collaborators."
- Skill descriptions carry explicit routing between `prod-readiness-coach` and `product-readiness-review`.
- Skill README license link fixed.

## 3.2.0

- Security: the secret scanner no longer copies the matching line into reports. Evidence is now `file:line [type] AKIA…MNOP`.
- Security: the scanner refuses to read through symlinks that resolve outside the repository.
- The coach treats the audited repository as untrusted data; instructions found inside it are never followed.
- Reports are written to a scratch location by default, not into the user's repo.
- Grade labels no longer say "Production Ready." The top grade is "Strong evidence of controls" and the heading is "Repository Controls Score."
- New `unknown` profile: when no stack is recognized, runtime checks report "insufficient evidence" instead of failing as a web app.
- Tests: 22 (secret redaction, symlink containment, unknown profile).

## 3.1.0

- Add `prod-readiness-coach`: a script-backed production-readiness scan with stack detection, project profiles, confidence labels on text-match findings, a plain-English audit, and a phase-gated fix brief. Moved in from `tmoody1973/prod-readiness-coach` with history.
- Add a "Going live" section to the always-on template: add CI the day a project goes live, prove it with a failing test, require the check via branch protection.
- Document the split between `prod-readiness-coach` (repeatable repo scan, run first) and `product-readiness-review` (product judgment, run after).
- Run the coach's unit tests in continuous validation.

## 3.0.0

- Package the repository as a Claude Code plugin and GitHub marketplace.
- Replace the invalid, universal 12-pattern reviewer with a compact contextual review workflow and supporting rubric.
- Add `product-readiness-review` for user, launch, security, reliability, and operational risk.
- Add `developer-handoff` for verified onboarding and technical transfer documentation.
- Make the always-on template prioritize product intent, framework conventions, behavior safety, and handoff hygiene.
- Make the installer use the canonical template and run portably on macOS and Linux.
- Correct the Boy Scout example so it preserves public names and strict boolean behavior.
- Treat line counts, parameter counts, and similar thresholds as investigation prompts rather than automatic failures.
- Align commands, skills, onboarding, and routing documentation.
- Add continuous validation for skills, manifests, and installer behavior on GitHub.
- Add a clean-checkout release checklist and document supported runtime requirements.
- Make installer writes atomic so interruption cannot leave a partially appended instructions file.

## 2.0.0

- Separate read-only review, local cleanup, and structural refactoring.
- Add test-safety gates, framework-aware guidance, deterministic-first scanning, and vibe-coder onboarding.
