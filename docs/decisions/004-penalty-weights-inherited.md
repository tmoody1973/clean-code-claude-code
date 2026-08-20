# 004: The score weights are inherited, not chosen

**Decision.** Leave the penalty table as it is (critical 30, high 18, medium 10, low 5) and write down that nobody has justified those numbers.

**Why this came up.** After a day of making the tool more honest, the one thing left unexamined was the score itself. Each failing check subtracts a fixed number of points from its category, and the overall score is the average. Those numbers came with the first version. When asked "why 30?", the honest answer is "it felt about right to whoever wrote it."

**Options.**
1. Re-pick the numbers now. Cost: a new guess replaces an old guess. We have run the tool on two repos. That is not enough to know what a better number is.
2. Drop the number and show only the letter. Cost: lose the ability to see progress between runs, which is the main thing the number is good for.
3. Keep the number, keep the letter cap that stops it from hiding blockers, and record that the weights are uncalibrated. Revisit when there are ten or more audited repos to compare against.

**What we chose and why.** Option 3. Joint call. The letter grade, capped by critical findings (see decision 001), already carries the safety. The number is a progress meter, and a progress meter only needs to move in the right direction. Comparing two different repos by number was never a promise this tool made, and the README should not imply it.

**What we gave up.** The comfort of a number that looks precise. An 82 here is not an 82 anywhere else.

**How we'll know if this was right.** When ten repos have been audited and someone lines up the numbers against their own judgement of which repos are riskier, the order should mostly agree. If it does not, that is the day to re-pick the weights, with data.

**What actually happened.**
(Tarik fills this in.)
