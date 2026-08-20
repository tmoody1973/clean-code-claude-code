# Release Checklist

Use this checklist from a clean checkout before publishing a stable version. A passing metadata validator does not prove that Claude follows the workflows correctly.

## 1. Review the release

- Confirm `git status` contains only intended changes.
- Review examples for behavior changes, invented facts, or exposed secrets.
- Confirm versions match in `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, and `CHANGELOG.md`.
- Confirm README tool names, installation commands, and supported environment are current.

## 2. Run deterministic validation

```bash
./scripts/validate-toolkit.sh
claude plugin validate .
claude plugin validate skills
claude plugin validate commands
```

The root `CLAUDE.md` warning from direct plugin-manifest validation is expected: that file guides repository contributors and is not shipped as plugin context.

## 3. Smoke-test from a clean checkout

Load the checkout with:

```bash
claude --plugin-dir /absolute/path/to/clean-code-claude-code
```

Exercise these user journeys:

1. Ask for a read-only code review and confirm no files change.
2. Ask for a product-readiness review and confirm it evaluates product evidence rather than only style.
3. Run `/code-smells` and confirm deterministic output is separated from judgment.
4. Run `/add-clean-code` against fresh, existing, repeated, and legacy-section fixtures.
5. Request Boy Scout cleanup on untested code and confirm risky edits are not presented as safe.
6. Run `/refactor` and confirm it identifies behavior-preservation evidence before editing.
7. Ask for a developer handoff and confirm commands are verified, secret values are omitted, and unknowns remain explicit.

Record unexpected behavior as an issue or fix it before release.

## 4. Publish and verify

- Commit and push the release candidate.
- Confirm the GitHub validation workflow passes.
- Install from the GitHub marketplace using the README instructions.
- Repeat one read-only and one editing smoke test from the installed plugin.
- Create the release tag only after the published version works.

For an initial release with limited behavioral evaluation, label the version as a beta instead of claiming stable production readiness.
