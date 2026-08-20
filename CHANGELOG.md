# Changelog

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
