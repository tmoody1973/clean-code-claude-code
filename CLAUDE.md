# Clean Code Toolkit Repository

This repository packages Claude Code skills, commands, templates, and scripts for AI-assisted product builders.

## Product goal

Help a vibe coder build software that works, understand the risks in it, and hand it to a developer without forcing generic clean-code dogma onto every framework.

## Repository rules

- Keep read-only review, local cleanup, structural refactoring, product assessment, and handoff as distinct workflows.
- `templates/CLAUDE.md` is the canonical always-on standards block. Installers reference it directly.
- Follow current Claude Code plugin conventions in `.claude-plugin/`.
- Keep skill frontmatter valid and quote descriptions containing colons.
- Keep core `SKILL.md` files concise; place detailed rubrics and output templates in `references/`.
- Every example must obey the safety rule it demonstrates.
- Never describe a change as behavior-preserving without considering public names, strictness, order, mutation, errors, and side effects.
- Update README and docs whenever tools, routing, or installation changes.

## Validation

Run `./scripts/validate-toolkit.sh` before committing. Runtime-test the installer in a temporary directory after changing it.
