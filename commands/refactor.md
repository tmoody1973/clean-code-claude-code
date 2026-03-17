Perform a structured refactoring on the code the user provides or the file they specify.

Follow these steps exactly:

1. Read the code to be refactored. If the user specified a file, read that file. If they pasted code, use that.

2. Analyze the code against these refactoring techniques (from the Clean Code Handbook):

   **Extract Method** - Are there blocks of logic that should be their own named functions?
   **Rename Variable** - Are there names that don't clearly communicate their purpose?
   **Simplify Conditionals** - Are there nested if/else chains that could use early returns or be flattened?
   **Inline Temp** - Are there single-use variables that add no clarity?
   **Replace Conditional with Polymorphism** - Are there growing if/else or switch chains that should be classes?
   **Remove Dead Code** - Is there commented-out code, unused variables, or unreachable branches?

3. For each issue found, categorize its impact:
   - HIGH: Makes the code significantly harder to understand or maintain
   - MEDIUM: Noticeable improvement to readability or structure
   - LOW: Minor cleanup

4. Apply the refactoring. Write the refactored code to the file (or present it if the user pasted code).

5. Show a summary of what changed:
   - List each refactoring applied with a one-line explanation
   - Show before/after for the most significant change
   - Note any further improvements that could be made but were out of scope

Important:
- Do NOT change behavior. Refactoring means improving structure without altering what the code does.
- Preserve all existing tests. If tests break, the refactoring is wrong.
- Apply the Boy Scout Rule: leave the code cleaner than you found it, but don't rewrite the entire file.
- Focus on the highest-impact improvements first.
