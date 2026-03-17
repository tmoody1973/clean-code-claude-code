# How to Use Clean Code Standards with Claude Code

This toolkit gives you multiple tools for enforcing clean code principles in your Claude Code projects. They work differently and serve different purposes.

---

## What's in This Package

```
clean-code-claude-code/
├── templates/
│   └── CLAUDE.md                    # Rules loaded every conversation
├── scripts/
│   └── add-clean-code.sh            # Bash script to install CLAUDE.md in any project
├── commands/
│   ├── add-clean-code.md            # Slash command to install CLAUDE.md
│   ├── refactor.md                  # Structured refactoring workflow
│   └── code-smells.md               # Quick code smell detection
├── skills/
│   ├── clean-code-review/
│   │   └── SKILL.md                 # Deep 12-pattern review reference
│   ├── clean-code-scaffold/
│   │   └── SKILL.md                 # Clean project structure setup
│   └── boy-scout-cleanup/
│       └── SKILL.md                 # Incremental code cleanup
└── docs/
    └── how-it-works.md              # This file
```

---

## Tool 1: CLAUDE.md -- The Always-On Rulebook

### What it does

`CLAUDE.md` is a special file that Claude Code reads automatically at the start of every conversation. Think of it as project-level instructions that Claude always follows -- like a `.editorconfig` or `.prettierrc` but for Claude's behavior.

Anything you put in `CLAUDE.md` becomes part of Claude's working context for that project. It doesn't need to be triggered or asked for. It's just *there*, shaping every line of code Claude writes.

### Why clean code rules belong here

Clean code principles aren't situational. You don't want Claude to write clean code *sometimes* -- you want it every time. That makes `CLAUDE.md` the right home for the distilled, actionable rules.

### How to install it

```bash
cp templates/CLAUDE.md /path/to/your-project/CLAUDE.md
```

Or use the `/add-clean-code` command or `add-clean-code.sh` script.

### Tips

- **Keep it concise.** Claude reads this every time, so shorter is better.
- **It stacks.** If you already have a `CLAUDE.md`, the installer appends the clean code section.
- **Project-specific overrides.** Tweak rules per project as needed.
- **Global option.** Use `~/.claude/CLAUDE.md` for rules across ALL projects.

---

## Tool 2: Skills -- Deep References on Demand

### clean-code-review

The full 12-pattern Clean Code Handbook. Triggers when you say things like "review this code," "refactor this," "make this cleaner," or "check code quality."

When triggered, Claude:
1. Scores the code against all 12 clean code patterns
2. Identifies the 3 most impactful improvements
3. Provides refactored code with before/after comparisons
4. Lists remaining minor issues as a checklist

### clean-code-scaffold

Project structure templates organized by concern. Triggers when you say "set up a project," "organize this code," or "scaffold this project."

Provides recommended structures for:
- Web applications (React / Next.js / Vue)
- APIs and backends (Express / FastAPI / Django)
- CLI tools
- Libraries and packages

### boy-scout-cleanup

Incremental cleanup following the Boy Scout Rule. Triggers when you say "clean this up," "this file needs some love," or "improve this code."

Works through a structured checklist: names, dead code, function length, conditionals, magic values, and formatting. Fixes 3-5 things per pass without changing behavior.

### How to install skills

```bash
# Global (all projects)
cp -r skills/clean-code-review ~/.claude/skills/
cp -r skills/clean-code-scaffold ~/.claude/skills/
cp -r skills/boy-scout-cleanup ~/.claude/skills/

# Per-project
cp -r skills/ /path/to/your-project/.claude/skills/
```

---

## Tool 3: Commands -- One-Step Actions

### /add-clean-code

Installs the Clean Code Standards section into a project's CLAUDE.md. Handles both new and existing CLAUDE.md files, with duplicate detection.

### /refactor

Structured refactoring using six techniques from the handbook: Extract Method, Rename Variable, Simplify Conditionals, Inline Temp, Replace Conditional with Polymorphism, and Remove Dead Code.

### /code-smells

Quick scan against the 8 most common code smells: duplicated logic, god objects, long parameter lists, nested conditionals, long methods, vague names, commented-out code, and magic numbers. Read-only -- reports issues without modifying code.

### How to install commands

```bash
# Global (all projects)
cp commands/*.md ~/.claude/commands/

# Per-project
mkdir -p /path/to/your-project/.claude/commands
cp commands/*.md /path/to/your-project/.claude/commands/
```

---

## Tool 4: add-clean-code.sh -- Terminal-First Setup

A bash script that installs the CLAUDE.md rules from your terminal:

```bash
chmod +x scripts/add-clean-code.sh

# Current directory
./scripts/add-clean-code.sh

# Specific project
./scripts/add-clean-code.sh /path/to/project

# Multiple projects
for dir in ~/projects/app1 ~/projects/app2; do
    ./scripts/add-clean-code.sh "$dir"
done
```

Safe to run repeatedly -- detects duplicates and skips if already installed.

---

## How All Tools Work Together

| Tool | Type | When it runs | What it does |
|------|------|-------------|--------------|
| `CLAUDE.md` | Config file | Every conversation, automatically | Enforces clean code while writing |
| `clean-code-review` | Skill | "Review this code" | Deep 12-pattern analysis |
| `clean-code-scaffold` | Skill | "Set up project structure" | Organizes by concern |
| `boy-scout-cleanup` | Skill | "Clean this up" | Incremental improvement |
| `/add-clean-code` | Command | When you type it | Installs CLAUDE.md rules |
| `/refactor` | Command | When you type it | Structured refactoring |
| `/code-smells` | Command | When you type it | Quick smell detection |
| `add-clean-code.sh` | Script | From terminal | Same install, outside Claude Code |

**Typical workflow:**

1. Start a new project -- run `/add-clean-code` or the bash script
2. Scaffold the structure -- say "set up a clean project structure"
3. Write code -- CLAUDE.md rules shape every response automatically
4. Need a deep review -- say "review this code"
5. Quick smell check -- type `/code-smells`
6. Touching existing code -- say "clean this up" for Boy Scout Rule
7. Targeted refactoring -- type `/refactor`

---

## Customizing

All files are plain Markdown or bash. Edit freely:

- **Add language-specific rules** to the CLAUDE.md template
- **Add your team's conventions** to any file
- **Remove patterns** that don't apply to your stack
- **Add new patterns** -- all files are designed to be extended

---

## Credits

Based on the [Clean Code Handbook](https://www.freecodecamp.org/news/the-clean-code-handbook/) by freeCodeCamp.
