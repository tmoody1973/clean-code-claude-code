# How the Toolkit Works

The toolkit separates always-on guidance, read-only assessment, focused edits, and handoff documentation. That separation keeps a request to “review” from unexpectedly rewriting a repository.

## The workflow

```text
Understand product intent
        ↓
Read-only assessment
        ↓
Choose the smallest justified change
        ↓
Verify behavior and product outcome
        ↓
Document what the next developer needs
```

## Always-on standards

`templates/CLAUDE.md` is the canonical standards block installed by `/add-clean-code` or `scripts/add-clean-code.sh`.

It is intentionally concise because project instructions consume context in every session. It covers product intent, framework fit, clarity, correctness, tests, existing-code safety, and handoff hygiene.

The installer:

- creates `CLAUDE.md` when it does not exist;
- appends without overwriting existing project instructions;
- skips a previously installed managed section;
- stops on a legacy clean-code section so migration is deliberate.

## Read-only assessment

### `clean-code-review`

Use for implementation quality. It reviews relevant code for correctness, security, names, cohesion, control flow, interfaces, errors, tests, structure, and automation. Thresholds are clues, not verdicts.

### `prod-readiness-coach`

Runs a dependency-free Python script that scans the repository for production gaps (CI, structured logging, error tracking, secrets, runbooks, multi-surface rollback, irreversible migrations, tests, dependency security), detects the stack, and loads matching platform notes. Claude then writes two documents: a plain-English audit that teaches each concept, and a phase-gated fix brief for a coding agent with a separate manual-steps list. Same repo, same findings every run; `--fail-on critical` makes it usable in CI. Run it first, then `product-readiness-review` for product judgment.

### `product-readiness-review`

Use for the whole product. It considers user journeys, functional behavior, security and privacy, accessibility, reliability, performance, delivery, operations, and handoff readiness.

### `/code-smells`

Use for a faster maintainability scan. It uses configured deterministic tools when available and then applies contextual judgment. It changes nothing.

## Editing workflows

### `boy-scout-cleanup`

Use for 3–5 small local improvements. It checks callers, public boundaries, tests, and tooling before editing. It avoids file moves, public API changes, new features, and speculative abstractions.

### `/refactor`

Use for a focused structural change. It defines the design problem, identifies behavior-preservation evidence, makes the smallest credible change, and verifies afterward.

### `clean-code-scaffold`

Use for new projects or deliberate reorganizations. It detects the actual language and framework before proposing a tree and asks before moving existing files.

## Developer handoff

`developer-handoff` inspects the repository and creates or updates a concise handoff covering:

- product purpose and main user journeys;
- verified setup, run, test, and build commands;
- architecture, data, and integrations;
- environment-variable names without secret values;
- deployment, rollback, logs, and operational ownership;
- test status, known issues, decisions, and recommended next work;
- unknowns that must be answered by the owner.

The handoff links to authoritative files instead of duplicating the repository.

## Tool routing

| User intent | Tool | Changes files? |
|---|---|---:|
| “How healthy is this code?” | `clean-code-review` | No |
| “Audit my repo for production readiness” | `prod-readiness-coach` | No |
| “Is the product ready to launch?” | `product-readiness-review` | No |
| “Give me a quick smell scan.” | `/code-smells` | No |
| “Tidy this file safely.” | `boy-scout-cleanup` | Yes, locally |
| “Restructure this module.” | `/refactor` | Yes |
| “Set up this project.” | `clean-code-scaffold` | Yes |
| “Help another developer take over.” | `developer-handoff` | Documentation only |

## What the toolkit deliberately avoids

- Universal folder structures
- Automatic failure based on line counts
- Requiring dependency injection or polymorphism everywhere
- Claiming that the presence of tests proves safety
- Rewriting existing code during a review
- Treating a successful build as proof of product readiness
- Filling documentation gaps with guessed facts
