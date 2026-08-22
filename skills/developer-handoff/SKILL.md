---
name: developer-handoff
description: "Create or update a concise developer handoff for an existing product by documenting setup, architecture, user flows, data, integrations, environment variables, testing, deployment, decisions, known issues, and next steps. Use when a vibe coder wants to give a project to a developer, onboard an engineer, prepare technical due diligence, or make a repository easier for someone else to understand."
---

# Developer Handoff

Produce a factual map that lets an incoming developer become productive without reverse-engineering the entire repository.

## Workflow

1. Read repository guidance and existing documentation before creating anything.
2. Detect the stack, entry points, package manager, environments, core product flows, domain modules, persistence, integrations, test commands, build, deployment, and CI.
3. Verify by running, not by reading. Run the setup and test commands, and then go further: the defects that hurt an incoming developer are in the claims a README makes about *integrations*, not in its install line. Check that a service the docs name is the service actually called, that a documented cost or limit still matches, and that a documented capability exists. Do not install, deploy, or mutate external systems without authorization.
4. Mark every statement with where it came from: **ran it**, **read it in a file**, or **told to me**. A command transcribed from a README and never executed is "read it in a file". This single distinction is the difference between a handoff and a plausible story.
5. Identify unknowns and stale documentation. Do not fill gaps with guesses.
6. **Delete template sections that have no referent.** If there is no database, the "Data and integrations" heading must not survive with prose under it. An empty heading pulls you toward filling it, and that is how a handoff acquires fiction. Write "no database" once, or remove the section.
7. Redact values for secrets, credentials, private URLs, tokens, and personal information. Document variable names and purpose only.
8. Ask where it should go. If the repository has a `docs/` convention, offer that path; otherwise offer `DEVELOPER_HANDOFF.md` at the project root. Write outside the repository if the user prefers. Create `DEVELOPER_HANDOFF.md` at the project root by default using [references/handoff-template.md](references/handoff-template.md).
9. Keep the handoff concise and link to authoritative files instead of duplicating their contents.
10. Close with three lists, using the template's own section names: what was verified by running it, what remains unknown, and the known issues that carry the most risk for whoever picks this up.

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
