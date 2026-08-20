---
description: Perform a focused structural refactor while preserving observable behavior and verifying the change.
---

Refactor the code or files identified by the user.

## Before editing

1. Read repository guidance, inspect the working tree, and preserve unrelated user changes.
2. Identify callers, exports, tests, public contracts, side effects, and configured checks.
3. State the structural problem and the intended boundary of the refactor.
4. Determine how behavior will be verified before and after. Existing tests are evidence only if they cover the affected behavior.
5. If verification is inadequate, propose a characterization test. Get explicit approval before adding tests that require a meaningful scope expansion or before proceeding with a behavior-adjacent refactor the user may not be able to verify.

## Refactor

- Prefer the smallest structural change that solves the identified problem.
- Preserve public APIs, schemas, evaluation order, strictness, side effects, and error behavior unless the user explicitly requests a migration.
- Use extract, rename, simplify, move, inline, composition, or polymorphism only when the context supports it.
- Do not apply arbitrary function-length, parameter-count, or nesting thresholds as rules.
- Do not mix unrelated cleanup or feature work into the diff.

## Verify and report

1. Run focused tests, then relevant type checks, linters, builds, or broader tests when practical.
2. If a check fails, diagnose it and reverse only your own offending hunk when necessary. Never discard unrelated user work.
3. Summarize the design problem, files changed, behavior-preservation evidence, commands run, and remaining risks.

Refactoring changes structure, not intended behavior. If intended behavior changes, name the work accurately as a feature or bug fix.
