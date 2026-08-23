# 012: Testing prompts without `claude plugin eval`

**Decision.** Split an eval in two. A runner that starts a headless Claude session against a fixture, which costs money and runs on demand. A grader that reads the output and checks it, which is free, deterministic, unit-tested, and runs in CI on every pull request. Seven rules block. Two are reported and never block, because judging them needs a judge we cannot run.

**Why this came up.** One of the six tools is a script with 130 tests. The other five are prompts, and a prompt cannot be tested the way a script can: run it twice on the same repository and the words come out different. If somebody edits `clean-code-review/SKILL.md` and makes it worse, nothing catches it.

`claude plugin eval` is built for exactly this. Its `--help` prints, so it looked available, and that was reported here as good news. Every real path returns "`plugin eval` is currently in early access". The original handoff had said so and was right.

What was at stake: five of six tools, which is most of the plugin, changing behaviour with nothing watching.

**Options.**
1. Wait for early access. Cost: unknown date, and until then the majority of the plugin has no behavioural coverage at all.
2. Run the skill in CI and have a model grade the output. Cost: every pull request starts a Claude session, which is slow, costs money, and returns a different answer each time, so a red build would not reliably mean a real regression.
3. Split it. Almost everything worth knowing about a review is mechanical: did it modify a file it promised not to, did it quote a path that does not exist, did it name the file holding the planted bug, did it do what a comment in the repository told it to. Those are free and give the same answer twice. Put them in a grader with its own unit tests, run those tests on every pull request, and keep the paid runner on demand.

**What we chose and why.** Option 3. Joint call. The reasoning is that the expensive half and the valuable half are not the same half. Running the skill is what costs; knowing whether the output was right is what matters, and most of that is a file existence check and a string search.

The first run proved the design by breaking it. Six failures: two were bugs in the grader, three were the operator's own `CLAUDE.md` reformatting the output, and one was a real gap in the product. The most instructive was the injection rule, which searched for "no issues found" and fired on a review that was quoting the attack in order to report it. **Quoting an attack is the opposite of obeying it.** The rule is positive now: the review must name the file the instruction was planted in.

Two rules were demoted to notes for the same reason. "Return false instead", "say no when the setting is missing" and "it should refuse by default" are one fix in three vocabularies, and a keyword list is always one phrasing behind. A rule that fails a correct answer teaches people to scroll past the eval, which is what a wrong HIGH finding did to `auth-2` for three releases. Judging a sentence needs a judge, so those two are reported for a human and never block.

**What we gave up.** The semantic half. Nothing here can tell whether the prose is good, whether the explanation would land with a beginner, or whether a differently-worded fix is correct. Those are exactly what an LLM grader is for, and they stay unmeasured until early access opens. We also gave up asserting layout: the first version checked for a "Verdict" heading and failed because the operator's `CLAUDE.md` had reformatted the output. User instructions outrank a skill by design, so asserting heading names asserts something the product does not promise.

Config isolation was tried and abandoned. `CLAUDE_CONFIG_DIR` does separate the config, and it separates the credentials with it, so the run cannot authenticate. The eval therefore runs under the operator's own configuration, and the assertions are written to survive that.

**How we'll know if this was right.** A change that makes a skill worse turns the grader red before it ships. If a correct review ever fails a blocking rule, that rule was written too tightly and belongs in the notes with the other two. When early access opens, the runner already produces the transcript an LLM grader would score, so adding the semantic half is additive rather than a rewrite.

**What actually happened.**
(Tarik fills this in.)
