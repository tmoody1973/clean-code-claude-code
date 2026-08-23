# Product Readiness Report

## Verdict

State the reviewed scope, confidence, and readiness for the user's stated milestone.

## Blockers

List evidence-backed issues that should prevent launch or handoff. Include location, affected user journey, realistic impact, and minimum remediation.

## Important improvements

List non-blocking work ordered by risk reduction and user value.

## Readiness matrix

Rate each relevant dimension as:

- **Ready:** credible evidence supports the milestone.
- **Needs work:** usable, with identified risk or missing evidence.
- **Blocked:** a material failure or unknown prevents a responsible readiness claim.
- **Not assessed:** outside the available evidence or scope.

Never turn the matrix into an unsupported numeric score.

## Evidence and checks

List documents inspected, commands run, results, and material areas not exercised.

## Recommended sequence

Give the smallest ordered path from current state to the stated milestone. Separate work for now, next, and later.

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
7. **No em dashes and no en dashes.** House style is plain punctuation: a comma,
   a colon, or a full stop. This is checked on the documents `prod-readiness-coach`
   produces and it applies to yours too.

The rubric this review is built on is written for an engineer, on purpose,
because it decides what to look at. This section decides how to say it. Do not
let the rubric's vocabulary leak into the report.
