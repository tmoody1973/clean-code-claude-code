---
name: boy-scout-cleanup
description: Apply the Boy Scout Rule to existing code -- leave every file cleaner than you found it. Use this skill when the user is working in an existing codebase and asks to clean up code, improve existing files, apply the Boy Scout Rule, tidy up a module, or says things like "clean this up while you're in there," "this file needs some love," "improve this code," or "make this better." Performs incremental cleanup without changing behavior.
---

# Boy Scout Cleanup Skill

Use this skill to apply the Boy Scout Rule (Clean Code Pattern 11): leave every file cleaner than you found it. This is for incremental improvement, not full rewrites.

## Cleanup Workflow

1. Read the file(s) the user wants cleaned up
2. Identify cleanup opportunities using the checklist below
3. Categorize each by impact (HIGH / MEDIUM / LOW)
4. Apply HIGH and MEDIUM fixes
5. List LOW fixes as suggestions for the user to consider
6. Verify no behavior changed (if tests exist, run them)

---

## Boy Scout Cleanup Checklist

Work through each category in order:

### 1. Names (Pattern 1)

- [ ] Rename single-letter variables to descriptive names
- [ ] Rename vague functions (`handleData`, `processStuff`, `doWork`)
- [ ] Replace abbreviations with full words unless universally understood
- [ ] Ensure class names are nouns, function names are verbs

### 2. Dead Code

- [ ] Delete commented-out code (git remembers it)
- [ ] Remove unused variables and imports
- [ ] Remove unreachable code after return/throw statements
- [ ] Delete empty catch blocks or replace with proper handling

### 3. Function Length (Pattern 10)

- [ ] Extract functions longer than 20 lines into smaller helpers
- [ ] Each extracted function does exactly one thing
- [ ] Give extracted functions names that describe their purpose

### 4. Conditionals

- [ ] Replace 3+ levels of nesting with early returns
- [ ] Simplify `if (x === true)` to `if (x)`
- [ ] Replace growing if/else chains with lookup objects or polymorphism

### 5. Magic Values (Pattern 9)

- [ ] Extract hardcoded numbers into named constants
- [ ] Extract hardcoded strings into constants or config
- [ ] Move configuration values to a config file or environment variables

### 6. Formatting (Pattern 8)

- [ ] Add blank lines between logical sections
- [ ] Ensure consistent indentation
- [ ] Group related imports together

---

## Rules

- **Never change behavior.** This is cleanup, not refactoring. The code must do exactly what it did before.
- **Don't rewrite the file.** Fix 3-5 things per pass. Incremental improvement compounds.
- **Run tests after cleanup.** If any test fails, revert that specific change.
- **Don't add features.** Don't add error handling that wasn't there, validation that wasn't there, or types that weren't there. That's enhancement, not cleanup.
- **Respect existing patterns.** If the codebase uses a specific style (even if you disagree), stay consistent with it.

---

## Example

**Before:**
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
    // old filter logic
    // r = r.filter(x => x.score > 50);
    return r;
}
```

**After:**
```javascript
const MINIMUM_AGE = 18;

function filterEligibleUsers(users) {
    return users.filter(user => user.active && user.age >= MINIMUM_AGE);
}
```

**What changed:**
- Renamed `proc` to `filterEligibleUsers` (Pattern 1: Meaningful Names)
- Renamed `d` to `users`, `r` to return value (Pattern 1)
- Replaced nested loop with `.filter()` (Pattern 10: Short Functions)
- Simplified `=== true` to truthy check (Pattern 4: Readability)
- Extracted `18` to `MINIMUM_AGE` constant (Pattern 9: No Hardcoded Values)
- Deleted commented-out code (Pattern 11: Boy Scout Rule)
