# Review Report Format

Lead with the verdict and the highest-risk findings.

## Verdict

State what was reviewed, overall confidence, and whether the code appears safe to hand to another developer.

## Findings

Order findings by severity. For each finding include:

1. **Title and severity**
2. **Location**: file and tight line range
3. **Evidence**: what the code demonstrably does
4. **Impact**: realistic user, operational, or maintenance consequence
5. **Recommendation**: smallest credible fix

Express evidence, impact, and recommendation as What / Why / Fix. This is not conditional: everyone this toolkit is built for is learning, so there is no second, terser audience to switch to.

## Checks run

List commands and outcomes. Say explicitly when checks could not be run or when no relevant tool is configured.

## Handoff gaps

If relevant, list missing setup instructions, architecture context, tests, or operational documentation that would slow another developer.

## Positive signals

Mention only strengths that materially reduce risk or make the code easier to change. Keep this shorter than the findings.

If no actionable findings exist, say so plainly and identify the scope limitations of the review.

## Write it so the owner can act on it

The person reading this built the app by describing it to an AI. They are
learning. A finding they cannot understand is a finding they cannot fix, so the
plain-English rules are part of the output, not a nicety.

1. **Never lead with jargon.** Say what it does and why it matters, then name it.
   "Anyone who knows the URL can read this page (missing an authorization check)"
   beats "missing authz on the handler".
2. **Define a technical term inline, in one clause, the first time you use it.**
   If you cannot define it in a clause, you are using it to sound precise rather
   than to be understood.
3. **Use a real consequence, not an abstract one.** "You will not know it broke
   until a user emails you" lands harder than "lacks observability".
4. **Frame a gap as the next thing to learn, not as a mistake.** The reader is
   learning; a gap is a lesson, not a failure.
5. **Say a win plainly.** If something is genuinely fine, say so. Do not
   manufacture urgency to make the report feel worthwhile.
6. **Short sentences. One idea each.** Avoid stacked clauses.

The rubric this review is built on is written for an engineer, on purpose,
because it decides what to look at. This section decides how to say it. Do not
let the rubric's vocabulary leak into the report.
