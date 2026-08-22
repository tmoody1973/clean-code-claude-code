"""Turn findings into a Markdown report and a JSON document."""
import fnmatch
import json
import re
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from .model import (WAIVER_FILE, WAIVER_MAX_AGE_DAYS, Category, SEVERITY_LABEL, SEVERITY_ORDER,
                    find_contradictions)
from .fingerprint import StackFingerprint

# --------------------------------------------------------------------------
# Report rendering
# --------------------------------------------------------------------------

def overall_score(categories: list[Category]) -> int:
    scored = [c for c in categories if c.applicable]
    if not scored:
        return 0
    return round(sum(c.score for c in scored) / len(scored))


def grade_for(score: int, critical_count: int = 0) -> str:
    # A category average can hide a release blocker. Any critical fail caps
    # the grade at D regardless of the numeric score.
    if critical_count > 0:
        return "D — Release blockers present" if score >= 40 else "F — Release blockers, little else in place"
    if score >= 90:
        return "A — Strong evidence of controls"
    if score >= 75:
        return "B — Minor gaps"
    if score >= 60:
        return "C — Notable gaps"
    if score >= 40:
        return "D — Major gaps"
    return "F — Few controls found"


def render_markdown(categories: list[Category], repo_name: str, fp: Optional[StackFingerprint] = None,
                     product_context: str = "") -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    score = overall_score(categories)
    all_checks = [c for cat in categories for c in cat.checks]
    blocking = [c for c in all_checks if c.status == "fail" and c.severity == "critical"]
    grade = grade_for(score, len(blocking))
    high = [c for c in all_checks if c.status == "fail" and c.severity == "high"]

    lines = []
    lines.append(f"# Production Readiness Audit — {repo_name}")
    lines.append("")
    lines.append(f"_Generated {now} by prod_audit.py_")
    lines.append("")

    if fp is not None:
        lines.append("## Detected Stack")
        lines.append("")
        lines.append(
            "This section is produced by deterministic static analysis (manifests, lockfiles, deploy "
            "configs) — re-running against the same commit always yields the same result. It drives "
            "which stack-specific reference material gets applied on top of this report."
        )
        lines.append("")
        lines.append(f"- **Languages:** {', '.join(fp.languages) or '_none detected_'}")
        lines.append(f"- **Package manager(s):** {', '.join(fp.package_managers) or '_none detected_'}")
        lines.append(f"- **Frameworks:** {', '.join(fp.frameworks) or '_none detected_'}")
        lines.append(f"- **Deploy surface(s):** {', '.join(fp.deploy_surfaces) or '_none detected_'}")
        lines.append(f"- **Runtime(s):** {', '.join(fp.runtimes) or '_none detected_'}")
        lines.append(f"- **Migration tooling:** {', '.join(fp.migration_tooling) or '_none detected_'}")
        lines.append(f"- **Multi-surface deployment:** {'YES — see Multi-Surface category below' if fp.multi_surface else 'No'}")
        if fp.adapters_matched:
            lines.append(
                f"- **Stack adapter reference(s) to apply:** {', '.join(fp.adapters_matched)} "
                f"(`references/stacks/<name>.md` in this skill)"
            )
        lines.append("")

    if product_context:
        lines.append("## Product Context (as provided)")
        lines.append("")
        lines.append(
            f"> {product_context}"
        )
        lines.append("")
        lines.append(
            "_This does not change the deterministic severity scores below — it's used to reprioritize "
            "which findings matter most when this report is translated into a fix plan (e.g. a 'medium' "
            "backups finding is functionally critical for an app holding irreplaceable user data)._"
        )
        lines.append("")

    if fp is not None:
        lines.append(f"**Profile:** `{fp.profile}` ({fp.profile_source}). Checks that do not apply to this "
                     "profile are marked n/a and left out of the score. Wrong profile? Re-run with `--profile`.")
        lines.append("")
    lines.append(f"## Repository Controls Score: {score}/100 — {grade}")
    lines.append("")
    lines.append("_This is a static scan of files and config. It measures which production controls "
                 "have evidence in the repo. It does not run the app and cannot prove the product works._")
    lines.append("")
    if blocking:
        lines.append(f"**{len(blocking)} CRITICAL blocking issue(s)** must be resolved before a stable, "
                      f"scalable production release.")
    else:
        lines.append("No CRITICAL blocking issues detected — review HIGH/MEDIUM findings below before release.")
    lines.append("")

    lines.append("| Category | Score | Critical | High | Failing Checks |")
    lines.append("|---|---|---|---|---|")
    for cat in categories:
        fails = [c for c in cat.checks if c.status == "fail"]
        crit = sum(1 for c in fails if c.severity == "critical")
        hi = sum(1 for c in fails if c.severity == "high")
        score_cell = f"{cat.score}/100" if cat.applicable else "N/A"
        if cat.has_weak_evidence:
            score_cell += " (text match only)"
        lines.append(f"| {cat.title} | {score_cell} | {crit} | {hi} | {len(fails)} |")
    lines.append("")

    conflicts = find_contradictions(categories)
    if conflicts:
        lines.append("## Conflicting signals")
        lines.append("")
        lines.append("One check passed while another failed in a way that undercuts it. "
                     "Resolve these before trusting either result.")
        lines.append("")
        for c in conflicts:
            lines.append(f"- **{' + '.join(c['ids'])}** — {c['note']}")
        lines.append("")

    applied = getattr(fp, "waivers_applied", []) if fp is not None else []
    problems = getattr(fp, "waiver_problems", []) if fp is not None else []
    if applied:
        lines.append("## Waived, with evidence")
        lines.append("")
        lines.append(f"These findings are real but were accepted by a human in `{WAIVER_FILE}`. "
                     f"They do not count toward the score or the exit code. Waivers expire after "
                     f"{WAIVER_MAX_AGE_DAYS} days.")
        lines.append("")
        lines.append("| Check | Reason | Evidence | Approved by | Date |")
        lines.append("|---|---|---|---|---|")
        for w in applied:
            lines.append(f"| `{w['id']}` | {w['reason']} | {w['evidence']} | {w['approved_by']} | {w['date']} |")
        lines.append("")
    if problems:
        lines.append("## Waivers that were rejected")
        lines.append("")
        lines.append("These entries did not apply, so their findings still count:")
        lines.append("")
        for _p in problems:
            lines.append(f"- {_p}")
        lines.append("")

    if blocking:
        lines.append("## 🔴 Release Blockers (Critical)")
        lines.append("")
        for c in blocking:
            lines.append(f"### {c.title} ({c.category})")
            lines.append(f"- **Issue:** {c.detail}")
            if c.recommendation:
                lines.append(f"- **Fix:** {c.recommendation}")
            if c.evidence:
                lines.append(f"- **Evidence:** {', '.join(c.evidence[:5])}")
            if c.best_practice_ref:
                lines.append(f"- **Best practice reference:** [{c.best_practice_ref}]({c.best_practice_ref})")
            lines.append("")

    if high:
        lines.append("## 🟠 High-Priority Gaps")
        lines.append("")
        for c in high:
            lines.append(f"### {c.title} ({c.category})")
            lines.append(f"- **Issue:** {c.detail}")
            if c.recommendation:
                lines.append(f"- **Fix:** {c.recommendation}")
            if c.evidence:
                lines.append(f"- **Evidence:** {', '.join(c.evidence[:5])}")
            if c.best_practice_ref:
                lines.append(f"- **Best practice reference:** [{c.best_practice_ref}]({c.best_practice_ref})")
            lines.append("")

    lines.append("## Full Findings by Category")
    lines.append("")
    for cat in categories:
        lines.append(f"### {cat.title}")
        lines.append(f"_{cat.description}_")
        lines.append("")
        lines.append(f"Best practice reference: [{cat.best_practice_ref}]({cat.best_practice_ref})")
        lines.append("")
        lines.append("| Check | Status | Severity | Detail |")
        lines.append("|---|---|---|---|")
        for c in sorted(cat.checks, key=lambda x: SEVERITY_ORDER.get(x.severity, 9)):
            status_icon = {"pass": "✅", "fail": "❌", "warn": "⚠️", "info": "ℹ️", "n/a": "➖", "waived": "🟦"}.get(c.status, "")
            detail = c.detail.replace("|", "\\|")
            status_text = f"{status_icon} {c.status}" + (" (text match — verify by hand)" if c.confidence == "weak" else "")
            lines.append(f"| {c.title} | {status_text} | {SEVERITY_LABEL.get(c.severity, c.severity)} | {detail} |")
        # Recommendations for any non-pass checks
        recs = [c for c in cat.checks if c.status != "pass" and c.recommendation]
        if recs:
            lines.append("")
            lines.append("**Recommendations:**")
            for c in recs:
                lines.append(f"- **{c.title}:** {c.recommendation}")
        lines.append("")

    lines.append("## Methodology")
    lines.append("")
    lines.append(
        "This tool performs static analysis of the repository working tree "
        "(via `git ls-files` where available) — no code execution, no network "
        "calls, no dependency installation. Secret detection uses pattern "
        "matching and is not a substitute for a dedicated secret-scanning tool "
        "(e.g. gitleaks/truffleHog) run against full git history. Re-run after "
        "remediation to confirm fixes and track score over time."
    )
    lines.append("")
    lines.append("Best-practice sources used to define these checks:")
    lines.append("- [The Twelve-Factor App](https://12factor.net/)")
    lines.append("- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)")
    lines.append("- [Google SRE Book](https://sre.google/sre-book/table-of-contents/)")
    lines.append("- [GitHub Actions documentation](https://docs.github.com/en/actions/learn-github-actions)")
    lines.append("- [GitHub Dependabot documentation](https://docs.github.com/en/code-security/dependabot)")
    lines.append("- [Martin Fowler on Testing](https://martinfowler.com/testing/)")
    lines.append("")

    return "\n".join(lines)


def render_json(categories: list[Category], repo_name: str, fp: Optional[StackFingerprint] = None,
                 product_context: str = "") -> dict:
    return {
        "repo": repo_name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_score": overall_score(categories),
        "grade": grade_for(overall_score(categories), sum(c.blocking_count for c in categories)),
        "stack_fingerprint": asdict(fp) if fp is not None else None,
        "product_context": product_context or None,
        "waivers": {"applied": getattr(fp, "waivers_applied", []) if fp else [],
                    "problems": getattr(fp, "waiver_problems", []) if fp else []},
        "contradictions": find_contradictions(categories),
        "categories": [
            {
                "key": cat.key,
                "title": cat.title,
                "score": cat.score if cat.applicable else None,
                "applicable": cat.applicable,
                "has_weak_evidence": cat.has_weak_evidence,
                "checks": [asdict(c) for c in cat.checks],
            }
            for cat in categories
        ],
    }


