# Clean Code Toolkit for Claude Code

Practical guardrails for people building products with AI-assisted coding. The toolkit helps you improve implementation quality, find out whether the repo and the product are actually ready, and prepare a repository for an incoming developer.

[![Validate toolkit](https://github.com/tmoody1973/clean-code-claude-code/actions/workflows/validate.yml/badge.svg)](https://github.com/tmoody1973/clean-code-claude-code/actions/workflows/validate.yml)

Clean code is not a score or a rigid set of line limits. In this toolkit, correctness, security, framework conventions, product behavior, and evidence from tests come first.

## What is included

| Tool | Mode | Use it when you want to… |
|---|---|---|
| `clean-code-review` | Read-only skill | Review correctness, clarity, maintainability, tests, and handoff gaps |
| `prod-readiness-coach` | Read-only skill + script | Scan a repo for CI, logging, secrets, rollback, and test gaps; get a plain-English audit and a phased fix brief |
| `product-readiness-review` | Read-only skill | Judge whether the product works for its users, launch, production, or due diligence |
| `developer-handoff` | Documentation skill | Create a factual guide for an incoming developer |
| `boy-scout-cleanup` | Editing skill | Make 3–5 small, behavior-preserving improvements |
| `clean-code-scaffold` | Editing skill | Structure a project using its real framework conventions |
| `/code-smells` | Read-only command | Run a quick contextual maintainability scan |
| `/refactor` | Editing command | Make a focused structural change with verification |
| `/add-clean-code` | Setup command | Add concise always-on rules to a project's `CLAUDE.md` |

## Install from GitHub

In Claude Code, add this repository as a marketplace and install the plugin:

```text
/plugin marketplace add tmoody1973/clean-code-claude-code
/plugin install clean-code-toolkit@clean-code-toolkit
```

To test a local clone before publishing:

```bash
claude --plugin-dir /absolute/path/to/clean-code-claude-code
```

Claude Code discovers the bundled skills and commands from the plugin.

The plugin targets Claude Code **2.1.89 or newer**. The `/add-clean-code` command requires Bash and standard Unix tools, so it is supported on macOS and Linux. Contributors also need Python 3.9 or newer to run the repository validator.

## Start using it

Begin with a read-only tool:

```text
Review this repository and explain the important findings in plain English.
```

```text
Is this product ready to hand to a developer and launch to early users?
```

```text
Prepare a developer handoff for this repository. Verify every command you can and clearly list unknowns.
```

Use `/add-clean-code` when you want the concise standards applied automatically in a project. It appends the managed section without overwriting existing instructions.

See [Start Here for Vibe Coders](docs/start-here-vibe-coders.md) for a plain-English workflow and [How It Works](docs/how-it-works.md) for tool boundaries.

## Design principles

- **Product intent first:** understand the user-visible outcome before optimizing internals.
- **Read-only before editing:** assess risk before changing files.
- **Evidence over confidence:** use tests, types, linters, builds, and repository facts.
- **Framework conventions win:** generic advice never outranks the stack's real conventions.
- **Thresholds are prompts:** line counts and parameter counts trigger inspection, not automatic failure.
- **Focused diffs:** preserve behavior and unrelated user work.
- **Honest handoffs:** unknowns remain unknown instead of becoming plausible AI guesses.

## Repository structure

```text
.
├── .claude-plugin/          # Claude Code plugin and marketplace manifests
├── .github/workflows/       # Continuous validation
├── commands/                # Explicit slash commands
├── skills/                  # On-demand workflows and references
├── scripts/                 # Portable installer and validation
├── templates/CLAUDE.md      # Canonical always-on standards
└── docs/                    # User guidance
```

The root `CLAUDE.md` contains contributor instructions for this repository. It is not plugin context; user-facing behavior lives in the skills, commands, and installable template.

## Manual standards installation

From a cloned repository:

```bash
./scripts/add-clean-code.sh /path/to/project
```

The script creates or appends to `CLAUDE.md`. It refuses to overwrite a legacy section that cannot be migrated safely.

Maintainers should follow the [release checklist](docs/release-checklist.md) before tagging a version.

## Scope

This toolkit improves engineering judgment and communication; it does not replace specialist security, accessibility, legal, compliance, or production-operations review for high-risk products.

## Credits and license

Inspired by the [freeCodeCamp Clean Code Handbook](https://www.freecodecamp.org/news/the-clean-code-handbook/) and adapted for AI-assisted product development by Tarik Moody.

MIT License. See [LICENSE](LICENSE).
