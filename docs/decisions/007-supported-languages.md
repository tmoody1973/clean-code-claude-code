# 007: Node and Next.js and Python are supported. Everything else gets the checks that do not care.

**Decision.** The tool no longer claims to work on any repository regardless of language. Checks split into two kinds. Checks that read the repository itself, is there CI, does it gate pull requests, is `.env` ignored, is there a runbook with real words in it, run on anything. Checks that need to understand the stack are supported on Node, Next.js and Python only, and on any other language they say what they could not check instead of guessing.

**Why this came up.** Five separate bugs turned out to be one bug wearing different hats: the engine only really knew Node. A helper returned a fake empty `package.json`, which is truthy in Python, so a Go repository was told "package.json exists but does not define a test script" about a file that was not there. The lint-step check knew `eslint` and `ruff` but not `mypy` or `golangci-lint`. The health-endpoint check could only find a route that was a file path, which is how Next.js declares one and how no other framework does. Sixty-eight tests caught none of it, because every fixture in the suite was a JavaScript repository. What was at stake: the tool's entire value is that it does not overstate what it looked at, and the sentence "it works on any git repo regardless of language/framework" was the tool overstating where it looked.

**Options.**
1. Keep the "any language" claim and keep patching. Cost: every new language is an edit in five files, the claim stays false in between, and the tool earns a reputation for lying about ecosystems it never supported.
2. Support Node, Next.js, Python and Go properly. Cost: Go is a fourth surface to keep correct, and Go is not who this tool is for. Its audience is self-taught developers shipping AI-assisted apps, which in practice means Next.js and Python.
3. Support Node, Next.js and Python. Split the checks so the language-agnostic ones still run everywhere, and make "no rules for Go" an explicit, named outcome that is left out of the score rather than counted as a failure.

**What we chose and why.** Option 3. Tarik's call, after research into how seven mature audit tools handle the same problem. OpenSSF Scorecard has a third outcome besides pass and fail, an inconclusive result scored `-1`, used when a check does not apply or the repository's language is unsupported, and it is excluded from the aggregate rather than penalized. Checkov has the same idea under the name `UNKNOWN`. That is the honest shape, and this codebase already had the machinery: an `n/a` status that is dropped from scoring.

**What we gave up.** The broad claim, which was the more impressive-sounding one. A Go or Ruby user now gets a smaller report. That is the correct trade: a smaller true report beats a larger one with invented findings in it.

**How we'll know if this was right.** A Go repository's report contains no statement about a file that does not exist, and names what it skipped. Adding a language later is one PR that adds an applicability tag and a fixture pair, not an edit across five files.

**What actually happened.**
(Tarik fills this in.)
