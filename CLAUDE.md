# Clean Code for Claude Code

This repository is a Claude Code toolkit that enforces clean code principles. It contains skills, commands, scripts, and templates based on the freeCodeCamp Clean Code Handbook.

## Project Overview

- **Owner:** Tarik Moody
- **Purpose:** Shareable clean code rules and tools for Claude Code users
- **Source:** Based on https://www.freecodecamp.org/news/the-clean-code-handbook/

## Structure

- `commands/` - Claude Code slash commands (add-clean-code, refactor, code-smells)
- `skills/` - On-demand skills (clean-code-review, clean-code-scaffold, boy-scout-cleanup)
- `scripts/` - Bash scripts for terminal-based setup
- `templates/` - CLAUDE.md template for any project
- `docs/` - Complete usage documentation

## Audience

Claude Code users who want clean code principles enforced automatically in their projects. This is a documentation and tooling repo -- there is no application code to run.

## When editing this repo

- Keep all examples in JavaScript (matching the handbook)
- Every pattern must have a Bad and Good code example
- Skills use YAML frontmatter with name, description
- Commands are plain Markdown with step-by-step instructions
- Credit freeCodeCamp in any new documentation
