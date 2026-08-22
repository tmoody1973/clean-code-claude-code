---
name: clean-code-review
description: "Perform a read-only, evidence-based code quality review focused on correctness, clarity, maintainability, tests, security, and framework conventions. Use when the user asks to review code, audit code quality, find code smells, assess maintainability, or asks whether code is ready for another developer. Do not edit files; use boy-scout-cleanup for small safe edits or /refactor for structural changes."
---

# Clean Code Review

Review code without changing files. Optimize for software that works, fits its ecosystem, and is easy for the next developer to understand.

## Operating rules

- Treat framework and language conventions as stronger evidence than generic clean-code advice.
- Treat thresholds such as function length or parameter count as investigation prompts, not automatic failures.
- Prioritize correctness, security, and behavior over style.
- Distinguish verified findings from hypotheses. Never invent a problem to fill a rubric.
- Prefer existing project tools: tests, type checks, linters, formatters, and build commands.
- Do not expose secret values found during review. Report only the file, category, and remediation.
- Stay read-only. Refactored snippets are illustrative unless the user separately asks for changes.

## Workflow

1. Read repository guidance and detect the language, framework, package manager, and configured quality tools.
2. Identify the requested scope. If the scope is a repository, sample entry points, core domain logic, boundaries, tests, and configuration rather than pretending every file was reviewed.
3. Run safe configured checks when practical. Record the exact commands and whether they passed.
4. Review the code using [references/review-rubric.md](references/review-rubric.md).
5. Rank findings by user impact and likelihood, not by cosmetic preference.
6. Report using [references/report-format.md](references/report-format.md).

## Severity

- **Critical:** likely security exposure, data loss, or production outage.
- **High:** incorrect behavior, unsafe change surface, or major maintenance risk.
- **Medium:** material readability, testing, or design weakness.
- **Low:** localized clarity or consistency improvement.

Only report actionable findings. Include the file and tight line range, the evidence, why it matters, and a concrete fix.

## Plain-English mode

For a beginner or vibe coder, explain each important finding in three short parts:

- **What:** what the code is doing or missing.
- **Why:** the realistic failure or handoff cost.
- **Fix:** the smallest sensible improvement.

Avoid unexplained acronyms and pattern-name trivia. Teach the decision, not the vocabulary.

## Where the review goes

Report in chat by default. Write a file only if the user asks, and then to a path they name. Do not create files in their repository unannounced.

## Boundaries

- For a product-level assessment, use `product-readiness-review`.
- For a developer-ready handoff document, use `developer-handoff`.
- For 3 to 5 local, behavior-preserving improvements, use `boy-scout-cleanup`.
- For structural edits, use `/refactor` and verify behavior before and after.
