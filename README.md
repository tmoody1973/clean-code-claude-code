# Clean Code Toolkit for Claude Code

You built an app by describing it to an AI. It works. Now you want to know: is it safe to put in front of real people, will it still make sense to me in a month, and could I hand it to a developer without embarrassment?

This toolkit answers those questions inside Claude Code, in plain English, and teaches you something each time. It is for people who vibe code and want to get better at it, not for people who already have an engineering team.

[![Validate toolkit](https://github.com/tmoody1973/clean-code-claude-code/actions/workflows/validate.yml/badge.svg)](https://github.com/tmoody1973/clean-code-claude-code/actions/workflows/validate.yml)

## The problem it solves

AI writes code faster than you can understand it. For a while that is fine. Then one day something breaks and you do not know where to look. Or a developer asks "how does this work?" and you cannot say. The app grew faster than your grasp of it.

The fix is not to stop using AI. The fix is to look before you touch, fix small, and write things down. This toolkit makes those habits easy to follow because Claude does the looking and explains what it found.

## Install

Open Claude Code and type these two lines:

```text
/plugin marketplace add tmoody1973/clean-code-claude-code
/plugin install clean-code-toolkit@clean-code-toolkit
```

Start a new session. You now have six skills and three commands. A skill is something Claude picks up on its own when you ask the right kind of question. A command is something you type with a slash.

## Ask in plain English

You do not need to remember tool names. Ask what you want and Claude picks the tool.

| You want to... | Say this | What happens |
|---|---|---|
| Know what is missing before going live | "Audit this repo for production readiness" | A script scans for the things that bite you in production: no automatic test runner, no error alerts, secrets in the code, no undo plan. You get a plain-English report that explains each gap, and a step-by-step fix list you can hand back to Claude. Writes two report files to a scratch folder, not your repo, unless you ask. |
| Know if the product actually works for users | "Is this product ready to launch?" | Claude reads the app as a whole, not file by file. Does it do what it claims? What would a real user hit first? Changes nothing. |
| Understand the quality of your code | "Review this code in plain English" | A report on what is unclear, untested, or fragile. Changes nothing. |
| Get a quick cleanup list | `/code-smells` | A short list of small things worth a look. Changes nothing. |
| Tidy one file safely | "Use boy-scout-cleanup on this file" | Three to five small fixes. Behavior stays the same. Tests prove it. |
| Make one bigger structural change | `/refactor` | One focused change with a check before and after. |
| Start a new project the right way | "Scaffold this project" | Folders and files the way your framework expects them. |
| Hand the project to a developer | "Prepare a developer handoff" | A guide that says what the app does, how to run it, what is fragile, and what is unknown. |
| Make Claude follow these rules every session | `/add-clean-code` | Adds a short set of standards to your project's `CLAUDE.md`. After that Claude applies them without being asked. |

Want to see what the audit looks like before you run it? Read the [example on vercel/commerce](docs/examples/vercel-commerce-plain-english-excerpt.md): a real public repo, a D grade, and why.

Start with the rows that say "changes nothing." Read what they find. Decide what matters to your users. Only then ask Claude to change code.

## A week with the toolkit

**Day 1.** You start a new app. "Scaffold a Next.js project for a recipe tracker." You build all day by describing features.

**Day 3.** You connect Vercel. The app is live. This is the moment that matters. "Audit this repo for production readiness." The report says: you have tests but nothing runs them automatically, and nothing tells you when the app breaks. Phase 1 of the fix list is one file. You hand it back to Claude. Twenty minutes later, every push runs your tests before it can go live. You understand why.

**Day 5.** Something feels messy. "Review this code in plain English." Three findings. You use boy-scout-cleanup on the worst file. Small, safe, tested.

**Week 3.** You want help. "Prepare a developer handoff." Claude writes the guide and lists what it could not figure out. You fill those in, because only you know them. The developer reads it and gets to work in an hour instead of a day.

You built it by vibe. You shipped it like someone who knows what they are doing. And you can explain each step.

## Four rules that prevent expensive mistakes

1. **Never put secrets in code.** API keys, passwords, and tokens live in environment variables, not in files you commit or paste into chat.
2. **A passing build is not proof the product works.** Test the things your users actually do.
3. **Do not let AI clean up code you have not read.** A rename or a "simpler" condition can quietly change behavior.
4. **"I don't know" is a fine answer.** A handoff that lists unknowns is safer than confident documentation the AI made up.

## The two readiness tools, and when to use which

Both ask "is it ready?" They answer different halves.

- **`prod-readiness-coach`** runs a script. Same repo, same findings every time. It checks the plumbing: automatic tests, error alerts, secrets, undo plans, and whether a rollback on one platform leaves another out of sync. Run it first, the day you go live, and again before any launch.
- **`product-readiness-review`** is Claude's judgment. Does the product do what it says? What would break first for a real person? Run it after the coach, when the plumbing is in.

## What CI is, if nobody ever told you

Imagine a group essay in a shared doc. One night someone deletes a paragraph by mistake. Nobody notices. The teacher reads it in the morning. That is how most vibe-coded apps work: you push a change, it goes live, and if it is broken your users are the teacher.

CI (short for "continuous integration," a name you can forget) is a robot that reads the essay after every edit, before the teacher sees it. Each time you push code, a fresh computer in the cloud wakes up, downloads your project, installs it from scratch, runs your tests, and tries to build the app. If any step fails you get a red X and the change cannot go live. If it passes, a green check. Then the computer is thrown away.

The fresh computer is the point. Your laptop has leftovers: old folders, forgotten settings. Code can work on your laptop because of a leftover and break everywhere else. The robot has no leftovers. If it works there, it works.

Why it matters: you will forget to run tests. It will be late, the change will be "tiny," and you will skip it. The robot never skips. And a robot that only ever says "fine" is useless, so the first thing to do after adding CI is break one test on purpose, watch it go red, then fix it. That red X is the proof.

One habit matters more than the file: when CI is red, stop and look. Never merge over a red X "just this once." The first time you do, the robot stops meaning anything.

## The going-live rule

Add CI the day your app first goes live. Not before: while you are sketching, tests change daily and the robot just slows you down. Not after: the moment a real person or a scheduled job depends on the app, a broken push has a real cost.

A simple trigger: the same day you connect Vercel, Fly, or Netlify, run the readiness coach. It will hand you the CI file. Then turn on branch protection in GitHub (Settings, Branches, add a rule for `main`, require the CI check) so the red X blocks a merge instead of just warning.

`/add-clean-code` puts this rule into a project's `CLAUDE.md` so Claude reminds you at the right moment in that project.

## Make it a habit everywhere

`/add-clean-code` works per project. If you want the rule in every project without remembering, paste this into your global `~/.claude/CLAUDE.md`. Claude reads that file at the start of every session on your machine.

```markdown
# GOING LIVE

The day a project first goes live, add CI the same day. "Live" means a real
person, a cron job, or another service now depends on it. Connecting a deploy
platform (Vercel, Fly, Netlify, Convex prod) counts as that day.

- Before that day: do not nag about CI.
- On that day, or whenever a live repo has no `.github/workflows/`: say so
  once and offer the two-step fix. (1) A workflow that runs typecheck, tests,
  and build on every PR and push to `main`; prove it by breaking one test,
  watching it go red, then reverting. (2) Branch protection on `main`
  requiring that check. This is a manual settings step; hand it to the human.
- Before any launch, schema change, or handoff, offer to run the
  `prod-readiness-coach` skill on the repo.
- Never merge over a red check "just this once."
```
## Requirements

- Claude Code 2.1.89 or newer.
- `/add-clean-code` needs Bash and standard Unix tools, so macOS or Linux.
- The readiness coach's script needs Python 3 (any recent version, no packages to install). Contributors need Python 3.9 or newer for the validator.

## For developers and contributors

To try a local clone before publishing:

```bash
claude --plugin-dir /absolute/path/to/clean-code-claude-code
```

To add the standards to a project without the plugin:

```bash
./scripts/add-clean-code.sh /path/to/project
```

It creates or appends to `CLAUDE.md` and refuses to overwrite a section it cannot migrate safely.

Repository layout:

```text
.
├── .claude-plugin/          # plugin and marketplace manifests
├── .github/workflows/       # validation and tests on every push
├── commands/                # slash commands
├── skills/                  # the six skills and their reference files
├── scripts/                 # installer and validator
├── templates/CLAUDE.md      # the always-on standards
└── docs/                    # guides, including the release checklist
```

The root `CLAUDE.md` holds contributor instructions for this repository. User-facing behavior lives in the skills, commands, and the installable template. Maintainers follow the [release checklist](docs/release-checklist.md) before tagging.

Design principles, in one line each: product intent first; read before editing; evidence over confidence; the framework's conventions beat generic advice; line counts are prompts to look, not failures; small focused diffs; unknowns stay unknown. [How It Works](docs/how-it-works.md) describes each tool's boundaries. [Start Here for Vibe Coders](docs/start-here-vibe-coders.md) is the longer plain-English guide.

## Scope

This toolkit improves engineering judgment and communication. It does not replace a specialist review for security, accessibility, legal, compliance, or production operations on high-risk products.

## Credits and license

Inspired by the [freeCodeCamp Clean Code Handbook](https://www.freecodecamp.org/news/the-clean-code-handbook/) and adapted for AI-assisted product development by Tarik Moody.

MIT License. See [LICENSE](LICENSE).
