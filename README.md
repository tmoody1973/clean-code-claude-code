# Clean Code for Claude Code

A toolkit that brings clean code principles into every Claude Code session. Based on the 12 patterns from the [Clean Code Handbook](https://www.freecodecamp.org/news/the-clean-code-handbook/) by freeCodeCamp.

Stop hoping your AI writes clean code. Make it automatic.

---

## What's Inside

| Tool | Type | What It Does |
|------|------|-------------|
| `CLAUDE.md` template | Config file | Enforces clean code rules in every conversation automatically |
| `clean-code-review` | Skill | Deep 12-pattern code review with scoring and refactored examples |
| `clean-code-scaffold` | Skill | Scaffolds clean project structure organized by concern |
| `boy-scout-cleanup` | Skill | Applies the Boy Scout Rule when touching existing files |
| `/add-clean-code` | Command | Installs the CLAUDE.md rules into any project |
| `/refactor` | Command | Structured refactoring using extract, rename, simplify techniques |
| `/code-smells` | Command | Quick scan for the 8 most common code smells |
| `add-clean-code.sh` | Script | Terminal-based installer for CLAUDE.md rules |

---

## Quick Start

### 1. Install the CLAUDE.md rules (pick one method)

**Option A: Slash command (inside Claude Code)**
```bash
# Copy the command to your global commands
mkdir -p ~/.claude/commands
cp commands/add-clean-code.md ~/.claude/commands/

# Then in any project, type:
/add-clean-code
```

**Option B: Bash script (from terminal)**
```bash
chmod +x scripts/add-clean-code.sh
./scripts/add-clean-code.sh /path/to/your-project
```

**Option C: Manual copy**
```bash
cp templates/CLAUDE.md /path/to/your-project/CLAUDE.md
```

### 2. Install the skills

```bash
# Global (all projects)
cp -r skills/clean-code-review ~/.claude/skills/clean-code-review
cp -r skills/clean-code-scaffold ~/.claude/skills/clean-code-scaffold
cp -r skills/boy-scout-cleanup ~/.claude/skills/boy-scout-cleanup

# Or per-project
cp -r skills/ /path/to/your-project/.claude/skills/
```

### 3. Install the commands

```bash
# Global (all projects)
cp commands/*.md ~/.claude/commands/

# Or per-project
mkdir -p /path/to/your-project/.claude/commands
cp commands/*.md /path/to/your-project/.claude/commands/
```

### 4. Start coding

Claude Code now follows clean code principles automatically. When you need a deep review, just ask: "review this code."

---

## How It Works

The toolkit has two layers:

**Always-on rules** (`CLAUDE.md`) load at the start of every conversation. They shape every line of code Claude writes without you asking. Think of it like a `.prettierrc` for Claude's behavior.

**On-demand tools** (skills and commands) activate when you need them:
- Say "review this code" and the `clean-code-review` skill loads the full 12-pattern handbook
- Type `/refactor` to walk through a structured refactoring
- Type `/code-smells` for a quick scan
- Say "set up a clean project structure" and the scaffold skill activates

For the complete guide, see [docs/how-it-works.md](docs/how-it-works.md).

---

## The 12 Clean Code Patterns

These are the patterns enforced by this toolkit, drawn from the [Clean Code Handbook](https://www.freecodecamp.org/news/the-clean-code-handbook/):

1. **Meaningful Names** - Every name communicates intent
2. **Single Responsibility** - Each function does one thing
3. **Thoughtful Comments** - Explain why, not what
4. **Readability** - Code reads like a story
5. **Testing** - Every function with logic gets tested
6. **Dependency Injection** - Pass dependencies, don't hardcode them
7. **Clean Project Structure** - Organize by concern
8. **Consistent Formatting** - Automated, uniform style
9. **No Hardcoded Values** - Named constants and config
10. **Short Functions** - Under 20 lines, delegate to helpers
11. **The Boy Scout Rule** - Leave code cleaner than you found it
12. **Open/Closed Principle** - Extend, don't modify

---

## Project Structure

```
clean-code-claude-code/
├── README.md                        # This file
├── CLAUDE.md                        # Project context for this repo
├── CONTRIBUTING.md                  # How to contribute
├── LICENSE                          # MIT License
├── .gitignore                       # Standard ignores
│
├── commands/                        # Claude Code slash commands
│   ├── add-clean-code.md            # Install CLAUDE.md rules in a project
│   ├── refactor.md                  # Structured refactoring workflow
│   └── code-smells.md               # Quick code smell detection
│
├── skills/                          # Claude Code skills (on-demand)
│   ├── clean-code-review/
│   │   └── SKILL.md                 # Deep 12-pattern review
│   ├── clean-code-scaffold/
│   │   └── SKILL.md                 # Clean project structure setup
│   └── boy-scout-cleanup/
│       └── SKILL.md                 # Boy Scout Rule enforcement
│
├── scripts/                         # Shell scripts
│   └── add-clean-code.sh            # Bash installer for CLAUDE.md
│
├── templates/                       # Copyable config templates
│   └── CLAUDE.md                    # Clean code standards for any project
│
└── docs/                            # Documentation
    └── how-it-works.md              # Complete usage guide
```

---

## Customizing

All files are plain Markdown or bash. Edit freely:

- **Add language-specific rules** to the CLAUDE.md template (Python, Rust, Go conventions)
- **Add your team's conventions** (commit formats, PR standards)
- **Remove patterns** that don't apply to your stack
- **Add new patterns** -- all files are designed to be extended

---

## Credits

This toolkit is based on the [Clean Code Handbook](https://www.freecodecamp.org/news/the-clean-code-handbook/) published by [freeCodeCamp](https://www.freecodecamp.org/). The handbook distills clean code principles into 12 actionable patterns with real-world examples. This project adapts those patterns into tools that work natively with [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

**Author:** Tarik Moody

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on adding new skills, commands, and language-specific templates.

---

## License

MIT
