# Contributing

Contributions should make AI-assisted product development safer, more understandable, or easier to hand off.

## Principles

- Framework conventions beat universal style rules.
- Correctness, security, and user impact beat aesthetics.
- Read-only review and file-changing workflows must have clear boundaries.
- Every editing workflow explains how behavior will be verified.
- Examples must obey the rules they teach.
- Guidance for beginners uses plain language without hiding real risk.

## Adding or changing a skill

1. Give the skill folder and frontmatter `name` the same lowercase hyphenated name.
2. Quote YAML descriptions that contain punctuation such as colons.
3. Put trigger context and tool boundaries in the description.
4. Keep `SKILL.md` focused on workflow. Put detailed rubrics and templates one level down in `references/`.
5. Use imperative instructions and link every supporting reference from `SKILL.md`.
6. Test the skill on a realistic request without leaking the expected answer.

## Editing safety

An editing skill or command must:

- inspect repository guidance and current user changes;
- identify public boundaries and relevant callers;
- distinguish tests that exist from tests that cover the behavior;
- preserve unrelated work;
- report checks run and remaining uncertainty.

Avoid “zero risk,” “always,” and “never” unless the statement is a genuine safety invariant.

## Documentation and installation

- `templates/CLAUDE.md` is the canonical always-on standards block.
- The installer must read the template rather than embed a second copy.
- Update the README and `docs/how-it-works.md` when tool names or boundaries change.
- Keep secret values out of examples and fixtures.

## Before opening a pull request

Run:

```bash
./scripts/validate-toolkit.sh
```

Then review the diff for duplicated instructions, stale tool routing, unverified claims, and examples that could change behavior.

For a release, also complete [docs/release-checklist.md](docs/release-checklist.md).
