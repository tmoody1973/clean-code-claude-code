# Review Rubric

Use the relevant sections for the code under review. Do not force every section onto every file.

## 1. Correctness and behavior

- Does the implementation match its stated contract and callers' expectations?
- Are boundary cases, invalid states, async failures, and partial operations handled deliberately?
- Could a cleanup change a public API, evaluation order, strictness, mutation behavior, or side effect?

Correctness findings outrank design preferences.

## 2. Security and privacy

- Look for embedded secrets, unsafe input handling, missing authorization, injection paths, insecure defaults, and sensitive logging.
- Check whether trust boundaries are visible and validated.
- Never reproduce secret values in the report.

Only make claims supported by code or configured tools. Recommend a dedicated security review for high-risk systems.

## 3. Names and domain language

- Names should communicate purpose at their scope.
- Prefer the vocabulary used by the product and its users.
- Short conventional names can be appropriate in small scopes or language idioms.
- Flag vague names when they create real ambiguity, not merely because they are short.

## 4. Responsibility and cohesion

- A function or module should have a coherent reason to change.
- Flag unrelated responsibilities, tangled boundaries, or hidden side effects.
- Do not split cohesive code solely because it exceeds a line threshold.
- Avoid helper fragmentation that makes a reader jump through files to understand one idea.

## 5. Control flow and data flow

- Prefer visible, unsurprising flow and manageable nesting.
- Flag duplicated decisions, invalid states that are easy to construct, and mutation that is hard to track.
- Early returns, tables, composition, or polymorphism are options, not automatic answers.

## 6. Interfaces and dependencies

- Keep public interfaces small, stable, and explicit.
- Introduce dependency injection when it improves substitution, testing, or boundary control.
- Do not add abstractions before there is evidence of variation or coupling.
- Watch for breaking changes hidden inside renames or file moves.

## 7. Errors and observability

- Errors should preserve useful context and follow ecosystem conventions.
- Empty catches and silently ignored failures require justification.
- Avoid logging secrets or noisy internal details.
- Exceptions, result types, and error returns are all valid when idiomatic for the stack.

## 8. Tests and change safety

- Test important behavior, business rules, boundaries, and regressions.
- Evaluate whether the tests would catch the proposed failure, not merely whether a test file exists.
- Prefer characterization tests before risky behavior-preserving refactors of untested code.
- Do not require a unit test for trivial pass-through code when higher-level coverage is clearer.

## 9. Structure and framework fit

- Follow the detected framework's conventions and the repository's established architecture.
- Keep related code discoverable; colocated and mirrored tests can both be correct.
- Flag structure when it obscures ownership, creates dependency cycles, or makes common changes scatter widely.

## 10. Automation and consistency

- Prefer configured formatters, linters, type checkers, and build tools over manual style opinions.
- Report a missing tool as a tooling opportunity, not automatically as the highest-severity defect.
- Separate tool output from findings that require human judgment.

## Common smells worth investigating

- Duplicated business rules
- Modules with unrelated responsibilities
- Long or unstable public parameter lists
- Deep nesting that hides outcomes
- Misleading names
- Commented-out or unreachable code
- Unexplained domain values
- Boolean flags that create multiple modes
- Temporal coupling or required call order
- Abstractions with only one speculative implementation

Each smell is a prompt to inspect context, not proof that the code is bad.
