# 001: Any critical finding caps the letter grade at D

**Decision.** If a repo has even one critical finding, its letter grade cannot be better than D, no matter what the numeric score says.

**Why this came up.** The overall score is an average of eight category scores. A repo with no CI pipeline and no error tracking scored 83 and was graded "B, nearly ready." Three of its categories were perfect, and that hid the two that were not. A beginner would read "nearly ready" and ship. That is the opposite of what a coaching tool is for.

**Options.**
1. Leave it. The detail table shows the criticals if you scroll. Cost: most people do not scroll past the grade.
2. Change the math so criticals pull the average down harder. Cost: the number becomes hard to explain, and a big enough repo could still bury one critical under many passes.
3. Keep the number, cap the letter. Cost: the number and the letter can disagree, which looks odd at first.

**What we chose and why.** Option 3. Joint call (Tarik and Claude). The number stays useful for tracking progress between runs. The letter is the thing people act on, so the letter tells the truth about blockers. A one-line code change.

**What we gave up.** A clean "83 means B" relationship. A repo can show 83/100 and D on the same line. We accept that because the mismatch is itself the lesson: one blocker matters more than nine nice-to-haves.

**How we'll know if this was right.** Nobody who reads a D report ships without fixing the criticals first. If people start ignoring the letter because it "always says D," we were wrong.

**What actually happened.**
(Tarik fills this in.)
