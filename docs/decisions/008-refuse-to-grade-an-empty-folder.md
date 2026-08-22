# 008: An empty folder gets refused, not graded

**Decision.** When the target directory contains no files, the audit stops with an error and exit code 2 instead of producing a report. A directory that has files but is not a git repository still runs, and the report opens with a warning that `.gitignore` was not applied.

**Why this came up.** A developer experience audit ran the tool against an empty directory. It returned "Repository Controls Score: 65/100, D, release blockers present" and four CRITICAL findings, and never mentioned that the folder was empty. A person who mistypes a path gets a confident grade about nothing. This is the same failure the v3.5.1 release existed to fix, three times over: a tool claiming more than it checked. What was at stake is the only thing this tool sells, which is that its output can be trusted without re-checking it by hand.

**Options.**
1. Leave it. The report does say "none detected" on every stack line, so a careful reader could work it out. Cost: the score, the grade and the word CRITICAL are the parts people actually read, and all three are false.
2. Produce the report but add a banner saying the folder is empty. Cost: it still prints a grade. A grade for nothing is not made true by a banner above it, and CI gating on `--fail-on` would still act on it.
3. Refuse. Print what is wrong, print what to do instead, exit non-zero. Cost: exit code 2 on an empty directory is a behavior change. Anyone whose pipeline pointed at the wrong path was previously getting a silent pass and will now get a failure.

**What we chose and why.** Option 3. Joint call. The cost of option 3 is a pipeline that breaks and tells you why, which is the correct outcome for a pipeline that was auditing nothing. The cost of options 1 and 2 is a false grade that somebody acts on.

The "not a git repository" case is deliberately treated differently. There are real files, so the checks have something to read and the findings mean something. But `git ls-files` is unavailable, so `.gitignore` is not applied and `node_modules` or build output can be read as source. That is a caveat on a real result, not a refusal.

**What we gave up.** A pipeline pointed at a wrong path used to exit 0 and now exits 2. We judged that a fix, not a regression, but it is a breaking change in a patch release and the CHANGELOG says so.

**How we'll know if this was right.** Nobody reports a score for a directory they did not mean to audit. If someone's CI breaks after upgrading, the error message tells them their path is wrong in one line, and that is the finding.

**What actually happened.**
(Tarik fills this in.)
