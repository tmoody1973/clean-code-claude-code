# Contributing

Thanks for your interest in improving Clean Code for Claude Code.

## What We're Looking For

### New slash commands

Ideas for commands that help enforce clean code:
- `/clean-naming` - Audit variable and function names
- `/test-audit` - Check test coverage against clean code testing standards
- `/format-check` - Verify consistent formatting

### Language-specific CLAUDE.md templates

The default template uses JavaScript examples. We'd love templates for:
- Python (PEP 8 + clean code)
- TypeScript (strict types + clean code)
- Go (idiomatic Go + clean code)
- Rust (ownership patterns + clean code)
- Java (Spring conventions + clean code)

### New skills

Skills that deepen specific clean code patterns:
- Dependency injection patterns by framework
- Testing strategies by language
- Project structure templates by stack

## How to Contribute

1. Fork this repo
2. Create a branch: `feat/your-addition`
3. Add your files to the correct directory
4. Update the README if you add a new tool
5. Open a PR with a clear description

## File Formats

### Commands

Plain Markdown in `commands/`. Include:
- What the command does (one sentence)
- Step-by-step instructions for Claude to follow
- The content to insert or analyze

### Skills

A folder in `skills/` containing `SKILL.md` with:
```yaml
---
name: skill-name
description: When this skill triggers and what it does
---
```
Followed by the skill content in Markdown.

### Templates

Plain Markdown in `templates/`. Keep them concise -- under 100 lines -- since they load into context every conversation.
