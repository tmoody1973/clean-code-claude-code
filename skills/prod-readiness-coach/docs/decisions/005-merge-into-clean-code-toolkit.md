# 005: Move this skill into the Clean Code Toolkit plugin

**Decision.** Fold `prod-readiness-coach` into `tmoody1973/clean-code-claude-code` as one of its skills, and turn this repo into a pointer. Do the move on a fresh day, not the same day this was decided.

**Why this came up.** Two repos now answer the same question, "is this ready?" The toolkit has a skill called `product-readiness-review`. This repo has `prod-readiness-coach`. A person who installs both gets two tools with near-identical names and no sign saying which to use. Claude Code picks skills by reading their descriptions, so it would be confused too.

**Options.**
1. Keep them separate. Cost: two installs, two READMEs, two places to fix the same thing, and the naming clash stays.
2. Delete one. Cost: they are not the same tool. The coach runs a script, so it gives the same answer every time and can run in CI. The review is Claude's judgment about whether the product works for users. Each does something the other cannot.
3. Merge the coach into the toolkit and give each readiness skill a clear job. The coach is the repeatable scan plus the plain-English teaching. The review is the judgment layer on top. Cost: about half a day of moving files, and this repo loses its own URL.

**What we chose and why.** Option 3. Joint call. The toolkit already has the plumbing the coach lacks: a plugin manifest, a one-line install, a validator, a changelog, CI. Moving in gets all of that for free. It also gives the going-live rule a natural home: the toolkit's `/add-clean-code` command already appends rules to a project's CLAUDE.md, so the rule goes in that template instead of needing its own skill. One install, one story: write it well, check it is ready, hand it off.

**What we gave up.** A separate GitHub page for the coach, and a little clarity for anyone who only wants the script. We keep history and tags by moving with `git subtree`, and the old repo's README will point to the new home.

**How we'll know if this was right.** After the move, a new user installs one plugin, asks "is my app ready?", and Claude picks the right skill without being told which. If people keep asking "which readiness tool do I use?", the relationship lines between the two skills are not clear enough.

**Move checklist (for the day we do it).**
- `git subtree add` this repo into `skills/prod-readiness-coach/` in the toolkit.
- Add it to the plugin manifest and the validator.
- Add a "Relationship to other tools" line to both readiness skills.
- Put the going-live rule into `templates/CLAUDE.md` so `/add-clean-code` carries it.
- Bump the plugin version and changelog.
- Replace this repo's README with a pointer.

**What actually happened.**
(Tarik fills this in.)
