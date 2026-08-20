# Review Report Format

Lead with the verdict and the highest-risk findings.

## Verdict

State what was reviewed, overall confidence, and whether the code appears safe to hand to another developer.

## Findings

Order findings by severity. For each finding include:

1. **Title and severity**
2. **Location** — file and tight line range
3. **Evidence** — what the code demonstrably does
4. **Impact** — realistic user, operational, or maintenance consequence
5. **Recommendation** — smallest credible fix

For beginner-facing reports, express evidence, impact, and recommendation as What / Why / Fix.

## Checks run

List commands and outcomes. Say explicitly when checks could not be run or when no relevant tool is configured.

## Handoff gaps

If relevant, list missing setup instructions, architecture context, tests, or operational documentation that would slow another developer.

## Positive signals

Mention only strengths that materially reduce risk or make the code easier to change. Keep this shorter than the findings.

If no actionable findings exist, say so plainly and identify the scope limitations of the review.
