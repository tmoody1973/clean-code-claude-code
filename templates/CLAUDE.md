<!-- BEGIN CLEAN CODE STANDARDS -->
# Clean Code Standards

Build software that is correct, safe to change, and understandable to the next developer. Apply these rules to new code. In existing code, report broader problems instead of rewriting them unless the user asks.

## Start with product intent

- Confirm the user-visible outcome and acceptance criteria when the request is ambiguous.
- Preserve existing behavior unless a behavior change is part of the request.
- Prefer the smallest complete solution over speculative infrastructure.

## Framework conventions win

- Detect the language, framework, and existing repository patterns before changing structure or style.
- Follow current ecosystem conventions when they conflict with generic advice.
- Use the project's configured formatter, linter, type checker, and test runner.

## Clarity

- Use names that communicate intent at their scope and match product vocabulary.
- Keep responsibilities cohesive. Readability beats arbitrary function-length or parameter-count limits.
- Comments explain decisions, business rules, constraints, or non-obvious techniques—not syntax.
- Avoid abstraction until it protects a real boundary or repeated variation.

## Correctness and safety

- Validate input at trust boundaries and fail with actionable, ecosystem-appropriate errors.
- Never silently swallow failures.
- Preserve evaluation order, strictness, side effects, and public contracts during cleanup.
- Never place secrets in source, logs, examples, or committed configuration. Use environment variables or a secret manager.

## Tests and verification

- Test important behavior, business rules, boundaries, and regressions—not every trivial line.
- Before risky changes to untested code, add a characterization test or explain the risk and ask how to proceed.
- Run the narrowest relevant checks after edits and report what ran.

## Existing code

- Keep diffs focused and preserve unrelated user changes.
- Make small cleanup passes; do not combine feature work with broad aesthetic rewrites.
- Do not rename public interfaces or move files without checking callers and migration impact.

## Going live

- The day a project first goes live, add CI the same day. "Live" means a real person, a scheduled job, or another service now depends on it; connecting a deploy platform counts.
- Before that day, do not add CI ceremony to a sketch.
- On that day, or whenever a live repo has no CI: add a workflow that runs typecheck, tests, and build on every pull request and push to `main`. Prove it by breaking one test, watching it fail, then reverting. Then require that check via branch protection, which is a manual settings step for the human.
- Before a launch, schema change, or handoff, offer the `prod-readiness-coach` skill.
- Never merge over a failing check "just this once."

## Developer handoff

- Keep setup, run, test, and deployment instructions accurate when those workflows change.
- Document new environment-variable names without recording secret values.
- Record non-obvious architecture decisions, operational risks, and known limitations.
<!-- END CLEAN CODE STANDARDS -->
