# 003: Project profiles, and stay strict when unsure

**Decision.** The tool now knows five kinds of project: web app, API, worker, CLI, and library. Checks that do not fit the kind are marked "n/a" and dropped from the score. The tool guesses the kind from the stack. When it cannot tell, it picks web app, the strictest one.

**Why this came up.** The tool audited itself, a command-line script, and failed it for having no health-check web page and no rate limiting. Those are web-app things. A script has no web page. Every failure of that kind made the score less believable, and a tool that fails its own audit for the wrong reasons is hard to trust.

**Options.**
1. Ignore it. Tell people to read past the irrelevant failures. Cost: the score is meaningless for anything that is not a web app.
2. Let the tool guess freely, leaning lenient. Cost: a wrong lenient guess hides real checks. A Convex backend guessed as "library" would skip error tracking, which it needs.
3. Guess only on a clear signal. Default to the strictest kind. Print the guess at the top so a human can override it with `--profile`. Cost: an unknown repo still gets some false failures until someone sets the flag.

**What we chose and why.** Option 3. Joint call, with the "strict when unsure" rule coming out of a Socratic check: what breaks if you pick the wrong profile for a Convex repo? Picking too strict gives you a false failure you can ignore. Picking too lenient skips a real check you will never see. The costs are not symmetric, so the default should not be either.

**What we gave up.** Out-of-the-box accuracy for unusual repos. And a wrong "n/a" now hides a check completely, which is why the profile is printed in the first lines of every report.

**How we'll know if this was right.** People running it on non-web projects stop complaining about health-check failures, and nobody reports a real gap that was hidden behind an n/a.

**What actually happened.**
(Tarik fills this in.)
