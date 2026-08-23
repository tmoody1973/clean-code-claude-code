#!/usr/bin/env bash
#
# Run one skill against its fixture and grade what came out.
#
#   evals/run_case.sh clean-code-review [--yes]
#
# This is the half of an eval that costs money. It starts a headless Claude Code
# session, so it is on-demand and never runs in CI on a pull request. The grader
# it hands off to is free, deterministic, and unit-tested, and that is where the
# rules live.
#
# The fixture is copied to a temporary git repository first. That is what makes
# "did this read-only skill change a file" answerable: git tells us, exactly.
set -euo pipefail

case_name="${1:-}"
[ -n "$case_name" ] || { echo "usage: evals/run_case.sh <case-name> [--yes]" >&2; exit 64; }

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
case_dir="$root/evals/$case_name"
[ -f "$case_dir/case.json" ] || { echo "no case at $case_dir/case.json" >&2; exit 66; }

prompt=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['prompt'])" "$case_dir/case.json")

if [ "${2:-}" != "--yes" ]; then
  echo "This starts a headless Claude Code session against $case_name."
  echo "It uses your account and it costs money. Re-run with --yes to proceed."
  exit 0
fi

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
cp -R "$case_dir/fixture" "$work/fixture"
cd "$work/fixture"
git init -q . && git add -A && git -c user.email=eval@local -c user.name=eval commit -qm fixture

echo "Running $case_name ..."
claude -p "$prompt" \
  --plugin-dir "$root" \
  --permission-mode acceptEdits \
  > "$work/review.md" 2> "$work/stderr.txt" || {
    echo "the run failed:" >&2; tail -5 "$work/stderr.txt" >&2; exit 70; }

dirty=$(git status --porcelain | awk '{print $2}' | paste -sd, -)

echo
echo "--- review (first 40 lines) ---"
head -40 "$work/review.md"
echo "--- end ---"
echo

python3 "$root/evals/grade_review.py" "$case_dir/case.json" "$work/review.md" \
  --fixture "$work/fixture" --dirty-files "$dirty"
