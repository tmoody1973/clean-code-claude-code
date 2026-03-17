Scan the code the user provides or the file they specify for code smells.

Follow these steps exactly:

1. Read the code to scan. If the user specified a file or directory, read those files. If they pasted code, use that.

2. Check the code against each of these 8 code smells (from the Clean Code Handbook):

   | # | Smell | What to Look For |
   |---|-------|-----------------|
   | 1 | Duplicated logic | Same or very similar code blocks appearing in multiple places |
   | 2 | God objects | Classes or modules doing too many unrelated things |
   | 3 | Long parameter lists | Functions with 4 or more parameters |
   | 4 | Nested conditionals | if/else chains 3 or more levels deep |
   | 5 | Long methods | Functions that need scrolling (over 20 lines) |
   | 6 | Vague names | Variables or functions that don't communicate intent |
   | 7 | Commented-out code | Dead code left in comments instead of deleted |
   | 8 | Magic numbers | Hardcoded values without named constants |

3. For each smell found, report:
   - Which smell it is (by name and number)
   - Where it is (file and line number)
   - A one-line description of the specific instance
   - The recommended fix

4. Produce a summary table:

   | Smell | Count | Severity |
   |-------|-------|----------|
   | (name) | (how many instances) | HIGH / MEDIUM / LOW |

5. If the code is clean with no smells detected, say so. Don't invent problems.

Important:
- This is a READ-ONLY scan. Do NOT modify any files.
- Be specific about locations. "There are some vague names" is not useful. "Line 42: variable `d` should be `daysSinceLastLogin`" is useful.
- Prioritize by impact. A god object is worse than a single magic number.
