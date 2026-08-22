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
2. **When there is no evidence, say so and ask.** An empty directory has nothing to detect, so anything you pick comes from the user's sentence and your own habits, not from the repository. Name the stack you would choose, name the one real alternative, and get an answer before creating files. Never present a guess in the voice of a detection.
3. Identify the product's primary domains or features and the code that changes together.
4. Preserve an established, coherent repository pattern unless the user explicitly requests a migration.
5. Propose the smallest structure that clarifies ownership and dependency direction.
6. For a new project, propose the layout and the reason for it, wait for a yes, then create the scaffold and starter files. "Agreed" means the user said yes to this layout, not that they asked for a project.
7. For an existing project, show the proposed moves and risks before moving files or changing imports.
8. **Run it.** Not "checks": run the thing you just created, exactly as your own README tells the user to run it, from a clean shell. A scaffold that errors on first command is worse than no scaffold, and it is the most common way this step fails. Then run the tests you created, and the project's formatter, linter, or type checker if you configured one.
9. If the first run needs anything the README does not say, either fix the layout so it does not, or put the missing step in the README. A Python `src/` layout, for example, is not importable until the package is installed or `PYTHONPATH` is set; say which one you chose and why.

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
