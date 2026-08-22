#!/usr/bin/env python3
"""Print the coverage grid, so 'is there an end to this' has a number.

Every check must prove two things: that it fires when the control is missing,
and that it stays quiet when the control is there. Checks that a profile can
skip must also have a fixture that skips them. This counts those cells.

Run: python3 skills/prod-readiness-coach/scripts/coverage_grid.py
     python3 skills/prod-readiness-coach/scripts/coverage_grid.py --fail-under 100
"""
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "tests"))

import prod_audit  # noqa: E402
from test_coverage_grid import ALL_CHECK_IDS, FIXTURES, FIRING, build_grid  # noqa: E402

MARK = {True: "  yes", False: "   NO"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fail-under", type=float, default=None,
                        help="Exit 1 if the filled percentage is below this number.")
    parser.add_argument("--quiet", action="store_true", help="Print the summary only.")
    args = parser.parse_args()

    grid = build_grid()
    skippable = set(prod_audit.CHECK_SKIPS_BY_PROFILE["library"])

    filled = required = 0
    rows = []
    for cid in ALL_CHECK_IDS:
        seen = grid.get(cid, set())
        fires, quiet = bool(seen & FIRING), "pass" in seen
        needs_na = cid in skippable
        has_na = "n/a" in seen
        required += 2 + (1 if needs_na else 0)
        filled += int(fires) + int(quiet) + (int(has_na) if needs_na else 0)
        rows.append((cid, fires, quiet, needs_na, has_na))

    pct = 100.0 * filled / required if required else 100.0
    if not args.quiet:
        print(f"Coverage grid, {len(FIXTURES)} fixtures over {len(ALL_CHECK_IDS)} checks\n")
        print(f"{'check':10}{'fires':>7}{'quiet':>7}{'skips':>7}")
        print("-" * 31)
        for cid, fires, quiet, needs_na, has_na in rows:
            skip = MARK[has_na] if needs_na else "    ."
            print(f"{cid:10}{MARK[fires]:>7}{MARK[quiet]:>7}{skip:>7}")
        print("-" * 31)

    gaps = [cid for cid, fires, quiet, needs_na, has_na in rows
            if not fires or not quiet or (needs_na and not has_na)]
    print(f"\n{filled} of {required} cells filled ({pct:.0f}%). {len(gaps)} check(s) with a gap.")
    if gaps:
        print("Gaps: " + ", ".join(gaps))
        print("A gap means no fixture proves that behaviour. Add one to tests/fixtures.py.")

    if args.fail_under is not None and pct < args.fail_under:
        print(f"\nBelow the floor of {args.fail_under}%.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
