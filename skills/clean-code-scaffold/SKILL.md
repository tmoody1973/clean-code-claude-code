---
name: clean-code-scaffold
description: "Create or propose a project structure that follows the detected language and framework conventions. Use when the user asks to start a project, scaffold an application, organize a new feature, or restructure a messy repository. Inspect the stack before proposing directories and get confirmation before moving existing files."
---

# Clean Code Scaffold

Create a structure that makes common product changes easy to locate and safe to implement.

## Framework conventions win

Inspect `package.json`, lockfiles, framework configuration, `pyproject.toml`, `go.mod`, `Cargo.toml`, build files, and existing source layout. When current framework documentation is required, fetch it before proposing a structure.

Do not impose `components/services/utils/tests` on every stack. Next.js, Django, Rails, Go, Rust, mobile frameworks, monorepos, and libraries each have useful conventions.

## Workflow

1. Determine the product type, language, framework, runtime, package manager, and deployment target from repository evidence.
2. Identify the product's primary domains or features and the code that changes together.
3. Preserve an established, coherent repository pattern unless the user explicitly requests a migration.
4. Propose the smallest structure that clarifies ownership and dependency direction.
5. For a new project, create the agreed scaffold and starter files.
6. For an existing project, show the proposed moves and risks before moving files or changing imports.
7. Run framework checks after implementation.

## Principles

- Keep related behavior discoverable.
- Prefer feature or domain boundaries when they match how the product changes.
- Separate reusable infrastructure from product-specific logic.
- Avoid catch-all `helpers`, `misc`, or `common` directories without a clear ownership rule.
- Avoid deep nesting that adds navigation but no boundary.
- Colocate or separate tests according to ecosystem convention.
- Add abstraction only when it protects a real boundary or repeated variation.
- Document non-obvious directory responsibilities near the project entry point.

## Deliverable

Explain:

- the detected conventions;
- the proposed tree;
- what belongs in each important directory;
- dependency-direction rules;
- files moved or created;
- verification performed;
- migration work deliberately left out.
