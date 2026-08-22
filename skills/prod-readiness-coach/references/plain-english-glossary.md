# Plain-English Glossary

Use these translations whenever a check or finding uses the term on the
left. Lead with the plain-English phrase; mention the technical term once
in parentheses so the reader can Google it or recognize it later, don't
hide the vocabulary, just don't lead with it.

| Technical term | Plain-English translation |
|---|---|
| CI/CD pipeline | An automatic checker that tests your code every time you (or an AI) push a change, *before* it can break the live site. Think of it as a robot proofreader that runs your test suite for you, every single time, so you don't have to remember to. |
| CI runs on pull requests | The robot proofreader checks your work *before* it's allowed to merge into the main version of the app, not after. |
| Structured logging | Writing down what your app is doing in a consistent, computer-readable format (like a form with labeled fields) instead of scattered `console.log("it broke")` notes. It's the difference between a filled-out incident report and a sticky note. |
| console.log / print statements | The "sticky note" way of debugging, quick and easy while coding, but these notes get lost, aren't searchable, and vanish once your terminal closes. Fine for local development, risky as your *only* way of knowing what happened in production. |
| Error tracking / APM (Application Performance Monitoring) | A tool (like Sentry) that automatically emails or messages you the moment something breaks for a real user, instead of you finding out because that user complained (or, worse, silently left). |
| Secrets management | Keeping passwords, API keys, and tokens out of your code and out of GitHub, storing them instead in a separate, locked-away place (environment variables, a secrets vault, or your hosting platform's dashboard). |
| .env file | A private file on your computer (or your hosting platform) that holds your actual secret values. It should never be uploaded to GitHub. |
| .env.example | A *public*, safe-to-share list of which secret names your app needs (with fake/blank values), like a packing list without the actual passport number filled in. |
| Hardcoded secret | A password or API key typed directly into your code instead of pulled from a `.env` file. Dangerous because anyone who can see your code (including the public, if the repo is public) can see the secret too. |
| Environment-specific config | Making sure your "practice" version (staging/development) and your "real" version (production) use different logins and different databases, so a mistake in testing can't accidentally mess up real users' data. |
| Runbook / incident response doc | A written "break glass in case of emergency" instruction sheet, what to do, in order, when something goes wrong at 2am. Without one, every outage is improvised. |
| Rollback | Un-doing a bad deploy and going back to the last version that worked, like `Ctrl+Z` for your whole live application. |
| Rate limiting | A speed bump that stops one user (or a bot, or a bug) from hammering your app or your AI API bill thousands of times a minute. |
| Database migration | A tracked, repeatable, undo-able way of changing your database's structure (adding a column, etc.), instead of manually editing the live database and hoping you remember what you did. |
| Health check endpoint | A tiny webpage (like `/health`) that just says "yes, I'm alive and my database connection works", so automated systems can notice and restart your app if it ever stops responding, without a human having to notice first. |
| Correlation ID / request ID / trace ID | A tracking number attached to one user's action as it moves through your system, so when something goes wrong you can find *all* the log lines related to that one specific request instead of guessing which of thousands of log lines matter. |
| Test coverage | The percentage of your code that your automated tests actually run through and check. Not a perfect measure of quality, but a decent smoke alarm for "nobody is testing this part at all." |
| Static type checking / strict mode | Having the computer double-check, before you even run the code, that you're not accidentally treating a number like a word or forgetting to handle a value that could be missing. Catches a whole category of bugs before they ever run. |
| Lockfile (package-lock.json, etc.) | A frozen, exact list of every dependency version your app is using, so "works on my machine" reliably means "works everywhere," including in production. |
| Dependabot / Renovate | A robot that automatically opens a pull request when one of your dependencies has a security fix available, so you don't have to manually check for updates. |
| Vulnerability scan | An automated check of your dependencies against a public database of known security holes. |
| CLAUDE.md / AGENTS.md | A "welcome guide" file for AI coding assistants (and human teammates) explaining how your project is set up, what commands to run, and any house rules, so every session starts with the right context instead of re-guessing it. |
| Multi-surface deployment | Your app doesn't live in just one place, maybe your website is on one platform and your database/backend is on another. Each piece rolls back independently, which means "undo the bad deploy" isn't always one button. |
| Coordinated rollback | A rollback plan that accounts for *every* piece your app is split across, not just the one that's easiest to undo. Without it, you can "fix" the frontend while leaving the backend on the version that caused the problem, now they don't match, and things break in new ways. |
| Irreversible migration | A database change (like deleting a column or a table) that can't be undone just by putting the old app code back. The old code doesn't bring the deleted data back with it, only a backup can. |
| Stack fingerprint | The specific combination of language, framework, and hosting platform this tool detected for your repo, used to tailor advice to your actual setup instead of giving generic one-size-fits-all tips. |

## Tone rules for any text you write using this glossary

1. **Never lead with jargon.** Say what it *does* and why it matters before naming it.
2. **Celebrate wins genuinely.** If a category passed, say so plainly, don't manufacture urgency where none exists.
3. **Frame gaps as "next skill to learn," not "you did this wrong."** The audience is learning; treat every gap as a lesson, not a failure.
4. **Use a real consequence, not an abstract one.** "If this breaks, you won't know until a user emails you" lands harder than "lacks observability."
5. **Keep sentences short.** One idea per sentence. Avoid stacked subordinate clauses.
6. **It's OK to be a little encouraging/informal**: this is a coach, not an auditor filing a compliance report.
