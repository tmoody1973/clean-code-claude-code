---
name: product-readiness-review
description: "Perform a read-only, evidence-based assessment of whether an AI-assisted or early-stage product is ready for users, production, technical due diligence, or developer handoff. Use when the user asks whether a product is production-ready, wants a product audit, wants to improve more than code style, or asks what must be fixed before launch or handoff. Use for user journeys and product behavior. For broad production-readiness requests, run prod-readiness-coach first for the repository-controls scan, then this review for product judgment."
---

# Product Readiness Review

Assess the product as a working system, not merely as a collection of clean files. Do not edit files unless the user separately asks to address findings.

## Workflow

1. Ask one question first: which milestone is this for, and what happens if it goes wrong? "Ready for my first ten users" and "ready for a paying customer" are different reviews, and the report format asks you to judge against a milestone you were never told.
2. If the user has not already run `prod-readiness-coach`, run it now and read its JSON. It covers the repository controls (CI, secrets, rollback, tests) deterministically, so this review can spend its attention on what a script cannot judge: whether the product works for the people using it. Do not re-derive its findings by hand.
3. Infer the product purpose, intended users, primary journeys, stack, and deployment model from repository evidence.
4. State important unknowns rather than silently assuming them.
5. Define milestone-specific acceptance checks for the product's primary journeys. For an agent, plugin, or developer tool, include discovery, representative invocation, safety boundaries, and generated artifacts.
6. Run configured tests and read-only analyzers. "Safe" means it does not write into the user's repository, does not deploy, and does not touch a live service. A build usually writes artifacts (`.next/`, `dist/`, `*.tsbuildinfo`), so either run it in a copy or skip it and say you skipped it. Never guess at a result you did not run.
7. Scope honestly. On a large repository you will not read everything. Say what you sampled and what you did not, and pick by risk: the paths that handle money, identity, or someone else's data first.
8. Evaluate the relevant dimensions in [references/readiness-rubric.md](references/readiness-rubric.md).
9. Separate launch blockers, handoff blockers, and later improvements.
10. Report in chat by default; write a file only to a path the user names. Produce an evidence-based report using [references/report-format.md](references/report-format.md).

## Rules

- User-visible correctness, security, privacy, and recoverability outrank code aesthetics.
- Do not claim production readiness from a successful build alone.
- Do not expose secret values found during inspection.
- Do not invent requirements. Clearly label inferred product expectations.
- Adapt depth to the product: a prototype, internal tool, healthcare product, and payment system have different risk profiles.
- Recommend specialist review where legal, compliance, safety, or deep security expertise is required.

## Relationship to other tools

- Use `prod-readiness-coach` first for the repeatable, script-backed scan of CI, logging, secrets, rollback, and tests, with plain-English teaching and a phased fix brief. This review is the judgment layer on top of it.
- Use `clean-code-review` for implementation quality within code.
- Use `developer-handoff` to create the documentation package for an incoming engineer.
- Use `/code-smells` for a fast maintainability scan.
