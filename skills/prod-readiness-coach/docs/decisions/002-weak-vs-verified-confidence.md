# 002: A text match is a clue, not proof

**Decision.** Every check now carries a confidence value. "Verified" means a real file, config entry, or dependency exists. "Weak" means the tool only found matching words in the code. A weak pass is reported as "verify by hand" and never counts as evidence that the control exists.

**Why this came up.** An outside review built small test repos to poke at the tool. A file containing only the comment `# TODO: add rate-limit later` made the rate-limiting check pass. The word was there. The feature was not. The same problem applied to request IDs and, in reverse, to secret scanning, which only looked at code files and skipped YAML, JSON, and untracked files. The tool was saying "pass" when it meant "I saw a word."

**Options.**
1. Remove the text-match checks. Cost: lose useful hints. "I see `express-rate-limit` in your code" is a real clue worth passing on.
2. Make the text matching smarter per framework. Cost: weeks of work, and still a guess.
3. Keep the matches but label them honestly, skip comment lines, and widen the secret scan to config files and untracked files. Cost: the report gets a new concept (confidence) the reader has to learn.

**What we chose and why.** Option 3. Joint call. A static tool (one that reads files and never runs the program) cannot prove a feature works. It can say "I found this, go look." Labeling that honestly is cheaper and more truthful than pretending to know.

**What we gave up.** Some passes now read as maybes. The report is a little less satisfying. We think a true maybe beats a false yes.

**How we'll know if this was right.** When someone checks a "weak" pass by hand, it should be wrong often enough that the label earned its place. If weak passes turn out right 99% of the time, the label is noise and we can drop it.

**What actually happened.**
(Tarik fills this in.)
