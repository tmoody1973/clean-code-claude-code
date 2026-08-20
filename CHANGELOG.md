# Changelog

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
