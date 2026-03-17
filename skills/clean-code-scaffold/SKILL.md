---
name: clean-code-scaffold
description: Scaffold a clean project structure organized by concern. Use this skill when the user asks to set up a new project, organize a messy codebase, create a project structure, restructure files, or says things like "set up the project," "organize this code," "create a clean folder structure," or "scaffold this project." Guides users through creating a well-organized codebase following Clean Code Pattern 7 (Clean Project Structure).
---

# Clean Code Scaffold Skill

Use this skill to create or reorganize a project into a clean structure following the Clean Code Handbook's Pattern 7: Clean Project Structure.

## Scaffold Workflow

1. Ask the user what kind of project they're building (web app, API, CLI, library, etc.)
2. Ask what language/framework they're using
3. Propose a structure based on the patterns below
4. Create the directories and any starter files after user confirms

---

## Structure Principles

- **Organize by concern**, not by file type
- **Separate source from tests** -- mirror the source structure in a tests directory
- **Keep related code together** -- a feature's components, services, and utils live near each other
- **Flat over nested** -- avoid directories more than 3 levels deep unless the project demands it

---

## Recommended Structures by Project Type

### Web Application (React / Next.js / Vue)

```
project/
├── src/
│   ├── components/      # Reusable UI components
│   ├── pages/           # Route-level components
│   ├── services/        # API calls, business logic
│   ├── utils/           # Pure helper functions
│   ├── hooks/           # Custom hooks (React) or composables (Vue)
│   ├── types/           # Type definitions
│   └── constants/       # Named constants and config
├── tests/
│   ├── components/
│   ├── services/
│   └── utils/
├── public/              # Static assets
└── package.json
```

### API / Backend (Express / FastAPI / Django)

```
project/
├── src/
│   ├── routes/          # Route definitions
│   ├── controllers/     # Request handlers
│   ├── services/        # Business logic
│   ├── models/          # Data models / schemas
│   ├── middleware/       # Request middleware
│   ├── utils/           # Helper functions
│   └── config/          # Configuration and constants
├── tests/
│   ├── routes/
│   ├── services/
│   └── utils/
└── package.json
```

### CLI Tool

```
project/
├── src/
│   ├── commands/        # Individual CLI commands
│   ├── services/        # Core logic
│   ├── utils/           # Helpers (formatting, validation)
│   └── config/          # Defaults and constants
├── tests/
│   ├── commands/
│   └── services/
└── package.json
```

### Library / Package

```
project/
├── src/
│   ├── core/            # Main library logic
│   ├── utils/           # Internal helpers
│   └── types/           # Public type definitions
├── tests/
│   ├── core/
│   └── utils/
├── examples/            # Usage examples
└── package.json
```

---

## What Goes Where

| Directory | Contains | Example |
|-----------|----------|---------|
| `components/` | Reusable UI pieces | `Button.tsx`, `Modal.tsx` |
| `services/` | Business logic, API calls | `userService.ts`, `emailService.ts` |
| `utils/` | Pure functions, small helpers | `formatDate.ts`, `validateEmail.ts` |
| `models/` | Data shapes, schemas | `User.ts`, `Order.ts` |
| `config/` | Constants, environment | `constants.ts`, `database.ts` |
| `tests/` | Mirrors src/ structure | `tests/services/userService.test.ts` |

---

## Anti-Patterns to Avoid

- **Everything in one folder** -- `src/` with 50 files and no subdirectories
- **Organizing by file type** -- `src/interfaces/`, `src/classes/`, `src/functions/`
- **Deeply nested** -- `src/modules/users/services/internal/helpers/`
- **Tests next to source** -- mixing `.test.ts` files alongside source files (unless framework convention)
- **Catch-all `helpers/` or `misc/`** -- if you can't name it, it needs to be split up
