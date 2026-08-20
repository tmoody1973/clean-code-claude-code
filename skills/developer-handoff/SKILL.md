---
name: developer-handoff
description: "Create or update a concise developer handoff for an existing product by documenting setup, architecture, user flows, data, integrations, environment variables, testing, deployment, decisions, known issues, and next steps. Use when a vibe coder wants to give a project to a developer, onboard an engineer, prepare technical due diligence, or make a repository easier for someone else to understand."
---

# Developer Handoff

Produce a factual map that lets an incoming developer become productive without reverse-engineering the entire repository.

## Workflow

1. Read repository guidance and existing documentation before creating anything.
2. Detect the stack, entry points, package manager, environments, core product flows, domain modules, persistence, integrations, test commands, build, deployment, and CI.
3. Run safe commands needed to verify setup instructions when practical. Do not install, deploy, or mutate external systems without authorization.
4. Identify unknowns and stale documentation. Do not fill gaps with guesses.
5. Redact values for secrets, credentials, private URLs, tokens, and personal information. Document variable names and purpose only.
6. Follow the repository's documentation convention. If none exists, create `DEVELOPER_HANDOFF.md` at the project root using [references/handoff-template.md](references/handoff-template.md).
7. Keep the handoff concise and link to authoritative files instead of duplicating their contents.
8. Report what was verified, what remains unknown, and the highest-risk handoff gaps.

## Quality bar

An incoming developer should be able to answer:

- What does this product do, and for whom?
- How do I run and test it safely?
- Where does each important user journey enter the code?
- Where is data stored and which external systems are involved?
- How is it deployed and rolled back?
- What is fragile, unfinished, or intentionally deferred?
- What should I work on first, and why?

Do not call a generated handoff complete if critical sections are based on assumptions.
