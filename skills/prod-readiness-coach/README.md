# prod-readiness-coach

Part of the [Clean Code Toolkit](../../README.md). Claude follows [SKILL.md](SKILL.md); the script is [`scripts/prod_audit.py`](scripts/prod_audit.py).

Run the script alone (Python 3.9+, no packages):

```bash
python3 scripts/prod_audit.py --repo /path/to/repo --output report.md --json report.json
python3 scripts/prod_audit.py --help   # --profile, --context, --fail-on
```

`scripts/check_report.py` lints a finished audit against the JSON it was written from: invented file paths, a text match sold as a win, a critical finding missing from the fix brief, a waived finding quietly dropped. The skill runs it before sharing.

Tests: `python3 -m unittest discover skills/prod-readiness-coach/tests` from the toolkit root.

Everything else (what it checks, profiles, confidence labels, limits, when to run it) lives in the [toolkit README](../../README.md) and [how it works](../../docs/how-it-works.md), so there is one place to keep current. Decisions that shaped this skill are in [`docs/decisions/`](docs/decisions/).

MIT. See [LICENSE](../../LICENSE).
