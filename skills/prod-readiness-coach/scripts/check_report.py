#!/usr/bin/env python3
"""Lint a generated audit against the JSON it was written from.

The script's findings are tested. The documents Claude writes from them were
not, and they are what the user actually reads. This turns the review rules in
SKILL.md step 8 from things to remember into things that are checked.

    python3 check_report.py AUDIT_PLAIN_ENGLISH.md FIX_BRIEF_FOR_CLAUDE_CODE.md --json report.json

Exits 1 if any rule is broken, so it can gate a hand-off.
"""
import argparse
import json
import re
import sys
from pathlib import Path

PATH_RX = re.compile(r"`([\w./-]+\.(?:ts|tsx|js|jsx|mjs|cjs|py|go|rb|java|kt|rs|php|cs|json|ya?ml|toml|md|sh|tf|lock))`")
PLACEHOLDER_RX = re.compile(r"\{\{[^}]+\}\}")
DASHES = ("—", "–")
WINS_HEADINGS = ("what's already solid", "whats already solid", "what is already solid")


def _section(md: str, *heading_starts: str) -> str:
    """Text under the first heading that starts with any of these, up to the next heading."""
    lines, out, capturing = md.splitlines(), [], False
    for line in lines:
        if line.startswith("#"):
            low = line.lstrip("# ").strip().lower()
            if capturing:
                break
            capturing = any(low.startswith(h) for h in heading_starts)
            continue
        if capturing:
            out.append(line)
    return "\n".join(out)


def lint(audit_md: str, brief_md: str, report: dict) -> list[str]:
    problems = []
    checks = {k["id"]: k for c in report["categories"] for k in c["checks"]}
    blob = json.dumps(report).lower()
    both = f"{audit_md}\n{brief_md}"

    # 1. A quoted file path must come from the scan, not from the model's memory.
    for doc_name, doc in (("audit", audit_md), ("brief", brief_md)):
        for path in set(PATH_RX.findall(doc)):
            if path.lower() not in blob and not _is_new_file(path, doc):
                problems.append(f"{doc_name}: `{path}` is quoted but never appears in the JSON. "
                                "Verify it exists, or label it as a file to create.")

    # 2. A text match must never be presented as a win.
    wins = _section(audit_md, *WINS_HEADINGS).lower()
    for cid, k in checks.items():
        if k["status"] == "pass" and k.get("confidence") == "weak":
            title_words = [w for w in re.split(r"\W+", k["title"].lower()) if len(w) > 4]
            if title_words and all(w in wins for w in title_words[:2]):
                problems.append(f"audit: {cid} is a text match, not proof, but reads as a win. "
                                "Move it to the text-match section.")

    # 3. Every critical finding has to show up in the fix brief.
    for cid, k in checks.items():
        if k["status"] == "fail" and k["severity"] == "critical":
            words = [w for w in re.split(r"\W+", k["title"].lower()) if len(w) > 4][:2]
            if words and not all(w in brief_md.lower() for w in words):
                problems.append(f"brief: critical finding {cid} ({k['title']}) is not addressed.")

    # 4. Waived findings must stay visible.
    for w in report.get("waivers", {}).get("applied", []):
        if w["id"] not in both:
            problems.append(f"audit/brief: waived finding {w['id']} is not mentioned. "
                            "A waiver is an accepted risk, not a deleted one.")

    # 5 and 6. House rules.
    for doc_name, doc in (("audit", audit_md), ("brief", brief_md)):
        if PLACEHOLDER_RX.search(doc):
            problems.append(f"{doc_name}: an unfilled {{{{placeholder}}}} was left in.")
        if any(d in doc for d in DASHES):
            problems.append(f"{doc_name}: contains an em or en dash; house style uses plain punctuation.")
    return problems


def _is_new_file(path: str, doc: str) -> bool:
    """A path the brief asks the reader to create is allowed to be absent."""
    for line in doc.splitlines():
        if f"`{path}`" in line and re.search(r"\b(create|add|new file|scaffold|write)\b", line, re.I):
            return True
    return False


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("audit", help="AUDIT_PLAIN_ENGLISH.md")
    ap.add_argument("brief", help="FIX_BRIEF_FOR_CLAUDE_CODE.md")
    ap.add_argument("--json", required=True, help="the audit JSON both were written from")
    a = ap.parse_args()
    problems = lint(Path(a.audit).read_text(), Path(a.brief).read_text(), json.loads(Path(a.json).read_text()))
    if not problems:
        print("Report checks passed: every quoted path is in the scan, no text match is sold as a win, "
              "every critical is addressed, nothing waived is hidden.")
        return 0
    print(f"{len(problems)} problem(s):", file=sys.stderr)
    for p in problems:
        print(f"  - {p}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
