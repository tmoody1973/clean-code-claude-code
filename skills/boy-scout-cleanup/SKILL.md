---
name: boy-scout-cleanup
description: "Make 3–5 small, local, behavior-preserving improvements to existing code. Use when the user asks to tidy a file, clean up code while working nearby, remove local clutter, or make a module easier to read. Do not use for a read-only review, public API changes, file moves, broad rewrites, or feature work."
---

# Boy Scout Cleanup

Leave the requested code a little easier to understand without changing its observable behavior.

## Safety check

Before editing:

1. Read repository guidance and inspect the working tree so user changes are preserved.
2. Identify the file's callers, exports, tests, and configured checks.
3. Decide what evidence can verify behavior: focused tests, type checks, lint, build, or careful call-site inspection.
4. If a proposed change could affect behavior and verification is weak, either add a characterization test with the user's approval or leave the change as a recommendation.

No edit is literally zero-risk. Unused imports may have side effects, comments may preserve important context, and renames may cross public boundaries. Inspect before removing or renaming.

## Good cleanup candidates

- Clarify a local variable without changing an external name.
- Remove proven unreachable code or a proven-unused import.
- Reduce nesting while preserving the exact conditions and evaluation order.
- Extract a domain value whose meaning is otherwise unclear.
- Use the project's formatter or import organizer.
- Improve a misleading comment or delete one that demonstrably restates the code.

## Out of scope

- Public API, schema, protocol, or behavior changes
- Moving files or splitting modules
- New validation, error handling, features, or dependencies
- Speculative abstractions
- Repository-wide style rewrites

Use `/refactor` for structural work and `clean-code-review` for read-only assessment.

## Workflow

1. Choose at most 3–5 related improvements.
2. Apply the smallest possible patches; do not rewrite the whole file.
3. Preserve strictness, ordering, side effects, mutation, exceptions, and public names.
4. Run the narrowest relevant checks, followed by broader configured checks when practical.
5. If a check fails, diagnose whether the edit caused it. Reverse only your own offending hunk; never discard unrelated user changes.
6. Summarize what changed, why it is behavior-preserving, and what verification ran.

## Example

Before:

```javascript
function proc(d) {
  let r = [];
  for (let i = 0; i < d.length; i++) {
    if (d[i].active === true) {
      if (d[i].age >= 18) {
        r.push(d[i]);
      }
    }
  }
  return r;
}
```

Safer local cleanup:

```javascript
const MINIMUM_AGE = 18;

function proc(users) {
  const eligibleUsers = [];

  for (let index = 0; index < users.length; index++) {
    const user = users[index];

    if (user.active === true && user.age >= MINIMUM_AGE) {
      eligibleUsers.push(user);
    }
  }

  return eligibleUsers;
}
```

The externally visible function name and strict boolean check remain unchanged. Rename `proc` only after proving it is private or updating and verifying every caller.
