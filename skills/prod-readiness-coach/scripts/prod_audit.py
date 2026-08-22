#!/usr/bin/env python3
"""Production-readiness audit for a code repository.

Static analysis only: it reads files and configuration, never runs the app and
never makes a network call. Run it directly:

    python3 prod_audit.py --repo /path/to/repo [--output report.md] [--json report.json]
    python3 prod_audit.py --repo . --profile cli --fail-on critical

The engine lives in the `audit/` package next to this file; this module is the
command line entry point and re-exports the public names so
`import prod_audit` keeps working for tests and callers.
"""
import sys as _sys
from pathlib import Path as _Path

_sys.path.insert(0, str(_Path(__file__).resolve().parent))

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# The audit modules use syntax that 3.8 cannot parse, so this has to sit ABOVE
# the imports below. Moved under them, it never runs and the reader gets
# "TypeError: 'type' object is not subscriptable" instead of a sentence. The
# audience here is often on the macOS system python3, which is old.
MIN_PYTHON = (3, 9)
if sys.version_info < MIN_PYTHON:
    sys.stderr.write(
        f"error: this script needs Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or newer, "
        f"and you are running {sys.version.split()[0]}.\n"
        "On macOS the built-in python3 is usually older than the one you installed. "
        "Try `python3.12` or `python3.11` in place of `python3`, or install a current "
        "Python from python.org or with `brew install python`.\n")
    raise SystemExit(2)

from audit.model import (  # noqa: F401  (re-exported for callers and tests)
    CHECK_SKIPS_BY_PROFILE, CONTRADICTIONS, MIN_DOC_WORDS, PROFILES,
    SEVERITY_LABEL, SEVERITY_PENALTY, SEVERITY_PENALTY_WARN, WAIVER_FIELDS, WAIVER_FILE, WAIVER_MAX_AGE_DAYS,
    WEAK_PASS_IDS, Category, CheckResult, find_contradictions, has_substance,
    load_waivers, runs_a_test_suite,
)
from audit.repo import Repo  # noqa: F401
from audit.checks_runtime import SECRET_PATTERNS, redact  # noqa: F401
from audit.fingerprint import StackFingerprint, detect_stack_fingerprint  # noqa: F401
from audit.runner import CATEGORY_META, guess_profile, run_audit  # noqa: F401
from audit.report import grade_for, overall_score, render_json, render_markdown  # noqa: F401

def main():
    parser = argparse.ArgumentParser(
        description="Production-readiness audit tool for a project repository.",
        epilog=(
            "Exit codes (these are a contract, wire CI against them):\n"
            "   0  the audit ran and nothing at or above --fail-on failed\n"
            "   1  the audit ran and at least one check at or above --fail-on failed\n"
            "   2  the audit could not run: the path is missing, is a file, or holds no files\n"
            "\nExit 2 always means nothing was scanned. It is never a verdict about the code."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", required=True, help="Path to the repository to audit.")
    parser.add_argument("--output", default=None, help="Path to write the Markdown report (default: prints to stdout).")
    parser.add_argument("--json", default=None, help="Optional path to also write a JSON report.")
    parser.add_argument("--fail-on", choices=["critical", "high", "none"], default="none",
                         help="Exit non-zero if any failing check at/above this severity is found (for CI gating).")
    parser.add_argument("--context", default="",
                         help="Optional one-line product context (e.g. 'what's the worst case if this loses "
                              "data or goes down for a day') used downstream to reprioritize findings. Does "
                              "not change the deterministic scores.")
    parser.add_argument("--profile", choices=PROFILES, default=None,
                         help="What kind of project this is. Checks that do not apply are marked n/a and "
                              "skipped in scoring. Guessed from the stack when omitted (strict when unsure).")
    args = parser.parse_args()

    HINT = ("Check the path, or pass `--repo .` to audit the directory you are in.")
    repo_path = Path(args.repo)
    if not repo_path.exists():
        print(f"error: repo path does not exist: {repo_path}\n{HINT}", file=sys.stderr)
        sys.exit(2)
    if not repo_path.is_dir():
        print(f"error: --repo must be a directory, and {repo_path} is a file.\n{HINT}",
              file=sys.stderr)
        sys.exit(2)
    # Grading an empty folder produces a confident score about nothing, which is
    # the exact failure this tool exists to catch. Refuse instead.
    if not Repo(repo_path).git_files():
        print(f"error: {repo_path} has no files to audit. Nothing was scanned, so no "
              f"score would mean anything.\n{HINT}", file=sys.stderr)
        sys.exit(2)

    categories, fingerprint = run_audit(repo_path, args.profile)
    md = render_markdown(categories, repo_path.resolve().name, fingerprint, args.context)

    if args.output:
        Path(args.output).write_text(md, encoding="utf-8")
        print(f"Markdown report written to {args.output}")
    else:
        print(md)

    if args.json:
        Path(args.json).write_text(
            json.dumps(render_json(categories, repo_path.resolve().name, fingerprint, args.context), indent=2),
            encoding="utf-8")
        print(f"JSON report written to {args.json}")

    if args.fail_on != "none":
        all_checks = [c for cat in categories for c in cat.checks]
        threshold = ["critical", "high"] if args.fail_on == "high" else ["critical"]
        blocking = [c for c in all_checks if c.status == "fail" and c.severity in threshold]
        if blocking:
            print(f"\n{len(blocking)} check(s) at or above '{args.fail_on}' severity failed.", file=sys.stderr)
            sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
