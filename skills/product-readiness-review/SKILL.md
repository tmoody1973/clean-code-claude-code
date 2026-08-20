---
name: product-readiness-review
description: "Perform a read-only, evidence-based assessment of whether an AI-assisted or early-stage product is ready for users, production, technical due diligence, or developer handoff. Use when the user asks whether a product is production-ready, wants a product audit, wants to improve more than code style, or asks what must be fixed before launch or handoff."
---

# Product Readiness Review

Assess the product as a working system, not merely as a collection of clean files. Do not edit files unless the user separately asks to address findings.

## Workflow

1. Infer the product purpose, intended users, primary journeys, stack, and deployment model from repository evidence.
2. State important unknowns rather than silently assuming them.
3. Define milestone-specific acceptance checks for the product's primary journeys. For an agent, plugin, or developer tool, include discovery, representative invocation, safety boundaries, and generated artifacts.
4. Run safe configured tests, builds, analyzers, and repository checks when practical.
5. Evaluate the relevant dimensions in [references/readiness-rubric.md](references/readiness-rubric.md).
6. Separate launch blockers, handoff blockers, and later improvements.
7. Produce an evidence-based report using [references/report-format.md](references/report-format.md).

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
