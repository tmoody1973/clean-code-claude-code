# Changelog

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
