# 009: A coverage grid, and a rule for when to stop reviewing

**Decision.** Every check must have a fixture that makes it fire and a fixture that makes it stay quiet. Checks a profile can skip must also have a fixture that skips them. The count is computed by running the audit over the fixtures, printed by `scripts/coverage_grid.py`, and CI fails if it drops below 100 percent. Once the grid is full and the invariants have tests, only a real user's bug report changes the engine.

**Why this came up.** Three review rounds in a row each found new defects, and the question was asked plainly: is there any end to this. There was no way to answer, because nobody could say how much had been checked. Sixty-eight tests existed and every one asked only whether a check fires. None asked whether it stays quiet when it should. That is the exact hole `auth-2` fell through: it was wrong about half the time it spoke, for three releases, with a full green suite. Without a denominator, every finding looks like proof of infinite findings, and the honest answer to "are we done" is "nobody can tell".

**Options.**
1. Keep reviewing. Each round finds real things, and the severity has been dropping. Cost: no finish line, and no way to distinguish a review that found nothing because the code is good from one that found nothing because the reviewer looked in the wrong place.
2. Rules as data. Move every check into a YAML or Rego file carrying its own applicability and its own fixtures, the way Semgrep, KICS and Trivy do. Cost: those projects did that at thousands of rules. This engine has thirty-four. The machinery would cost more than the checks.
3. Keep the checks as Python. Add fixtures and count the grid mechanically. Borrow the contract from KICS, which refuses a query that ships without both a vulnerable and a safe fixture, and from Checkov, which requires both a PASSED and a FAILED test case. Cost: fixtures are work, and a fixture that is wrong teaches the wrong lesson confidently.

**What we chose and why.** Option 3. Tarik's call, after research into how OpenSSF Scorecard, Semgrep, Checkov, Trivy, KICS, SonarQube and Datree each handle it. The deciding detail is that the grid is derived, not maintained. Nobody writes down which checks have which coverage. The number comes from running the audit over the fixtures, so it cannot drift from the code, and adding a check with no fixture fails the build with that check's id in the message.

It paid immediately. Demanding a passing fixture for every check surfaced two false negatives that three rounds of human review had missed: a Sentry package installed as `@sentry/nextjs` was invisible to the error-tracking check, so a correctly instrumented Next.js app was told at CRITICAL that it had no error tracking, and a plain `migrations/` folder was never read for destructive SQL, so a `DROP TABLE` went unreported outside four specific ORMs.

**What we gave up.** Fixtures are a maintenance surface of their own. A fixture that misrepresents a real repository will make a check look covered when it is not, and nothing in the grid can detect that. The count says a behaviour is exercised; it does not say the behaviour is right.

**The stop rule.** The engine is done when the grid is at 100 percent, the five invariants have tests, and CI is green. After that, a review looks for a new class of defect, not a new instance of an old one, and a review that finds nothing counts as a pass. Only a bug report from a real user reopens the engine.

**How we'll know if this was right.** The next review round finds either nothing or something in a class nobody had named before. If it finds another instance of a class already on the invariant list, the invariant was written too narrowly and that is the thing to fix.

**What actually happened.**
(Tarik fills this in.)
