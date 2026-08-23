# 011: Fix the report, not the rubric

**Decision.** The two rubrics stay written for an engineer. The plain-English rules move to the two report formats whose output the project owner reads, they stop being conditional, and `validate-toolkit.sh` fails if either format loses them.

**Why this came up.** An independent tester said `skills/clean-code-review/references/review-rubric.md` "reads like undefined jargon trivia and contradicts its own skill's plain-English promise". Reading it, the vocabulary complaint is fair: about fifteen terms appear undefined, including temporal coupling, characterization tests, dependency injection, helper fragmentation and evidence of variation or coupling. The README row for that skill says "Review this code in plain English."

What was at stake is the toolkit's central promise to an audience that is learning. A finding somebody cannot understand is a finding they cannot fix.

**Options.**
1. Rewrite the rubrics in plain English, as the tester suggested. Cost: the rubric is what makes the review competent, and the precision is doing work. "Temporal coupling" names a specific failure that "order matters" does not. Softening the checklist to protect a reader who never sees it would buy nothing and cost the quality of every review.
2. Leave it. The rubric is internal, the model understands the terms, and the report is a separate document. Cost: this is what was already happening, and it produced the complaint. A model mirrors the register of its instructions, so a checklist in dense engineering prose pulls the report toward dense engineering prose, and nothing was pulling the other way.
3. Separate the two jobs explicitly. The rubric decides what to look at and stays technical. The report format decides how to say it and carries the plain-English rules. Say so in both files, so the next reviewer does not translate the wrong one.

**What we chose and why.** Option 3. Joint call, and it disagrees with the tester's recommendation while accepting the observation behind it. The complaint was real; the file it named was not the cause.

Looking closer found the actual defect. `prod-readiness-coach` has a glossary, six tone rules, and `check_report.py` linting the documents it produces. The two other skills the owner reads had, between them, one conditional half-sentence: "For beginner-facing reports, express evidence, impact, and recommendation as What / Why / Fix." Everyone this toolkit is built for is beginner-facing, so the condition never should have existed. **A promise enforced in one skill of six and hoped for in the others is not a standard.**

The `developer-handoff` template was deliberately left alone. Its reader is the developer receiving the project, and engineering vocabulary is the correct register there. Applying a plain-English rule to it would have been the same error in the other direction.

**What we gave up.** The tone rules now exist in three places: the coach's glossary and both report formats. That is real duplication and it will be tedious to reword. A rule that has to be followed while writing has to be in the same context as the writing, and the validator makes drift a build failure rather than a slow decay. We also did not verify that the rules change the output, because the five prompt-only skills still have no automated coverage.

**How we'll know if this was right.** A review of a repository reads like something the owner can act on, and the terms in the rubric appear in the report only with a definition attached. If a tester still says the report is jargon-heavy, the rules were not enough and the next step is a linter for these two documents, like the coach already has.

**What actually happened.**
(Tarik fills this in.)
