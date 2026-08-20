---
description: Run a quick, read-only scan for maintainability smells using configured tools and contextual review.
---

Perform a read-only smell scan on the file, directory, or pasted code the user identifies.

1. Read repository guidance and detect the language, framework, and configured linter or analyzer.
2. Run the narrowest safe configured tool when practical. Do not install dependencies or rewrite files.
3. Inspect for duplicated business rules, unrelated responsibilities, confusing interfaces, deep nesting, misleading names, dead code, unexplained domain values, hidden side effects, and speculative abstractions.
4. Treat counts such as 20 lines, four parameters, or three nesting levels as prompts to inspect context—not automatic failures.
5. Report only actionable findings with file, line, evidence, impact, and a concrete recommendation.
6. Separate deterministic tool output from judgment-based findings and avoid duplicating the same issue.
7. If no linter is configured, note it as a tooling opportunity only when a linter would materially help this project. Do not automatically rank it above code defects.

Do not modify files. Do not invent smells to complete a checklist. Prioritize correctness and security risks over style concerns.
