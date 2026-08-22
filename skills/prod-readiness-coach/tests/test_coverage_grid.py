"""The coverage grid.

Every check must prove it fires when the control is missing AND stays quiet when
the control is there. Counting that is the point: without a denominator, every
review feels like proof of infinite findings.

The grid is computed by running the audit over the fixtures, so it cannot drift
from the code. Add a check with no fixture that exercises both sides and this
file fails with the check's id.
"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import prod_audit  # noqa: E402
import fixtures  # noqa: E402
from test_prod_audit import (  # noqa: E402
    GoRepoIsNotLiedTo, PythonServiceRepo, make_repo,
)

ALL_CHECK_IDS = [
    "agent-1",
    "auth-1", "auth-2", "auth-3",
    "ci-1", "ci-2", "ci-3", "ci-4", "ci-5", "ci-6",
    "log-1", "log-2", "log-3", "log-4",
    "sec-1", "sec-2", "sec-3", "sec-4", "sec-5",
    "res-1", "res-2", "res-3", "res-4", "res-5",
    "ms-1", "ms-2", "ms-3",
    "test-1", "test-2", "test-3", "test-4",
    "dep-1", "dep-2", "dep-3",
]

FAKE_AWS_KEY = "AKIA" + "ABCDEFGHIJKLMNOP"

# Small fixtures that exist only to push one check to one side.
GUARDED_ROUTES = {
    **fixtures.NEXTJS_BARE,
    "package.json": json.dumps({"dependencies": {"next": "15.0.0", "@clerk/nextjs": "6.0.0"}}),
    "src/app/api/items/route.ts": (
        'import { auth } from "@clerk/nextjs/server";\n'
        'export async function GET() { const { userId } = await auth(); return Response.json([]); }\n'),
}
FAIL_OPEN_GUARD = {
    **fixtures.NEXTJS_BARE,
    "src/lib/owner.ts": ('const owner = process.env.OWNER_EMAIL;\n'
                         'export function isOwner(e) { if (!owner) return true; return e === owner; }\n'),
}
LEAKY_SECRETS = {
    **fixtures.NEXTJS_BARE,
    "src/config.ts": f'export const key = "{FAKE_AWS_KEY}";\n'
                     'const url = process.env.DATABASE_URL;\n',
    ".env": "DATABASE_URL=postgres://real:secret@host/db\n",
}
UNSAFE_ROUTE = {
    **fixtures.NEXTJS_BARE,
    "src/app/api/pay/route.ts": (
        'export async function POST(req) {\n'
        '  const body = await req.json();\n  return Response.json(charge(body));\n}\n'),
}
PLAIN_MIGRATIONS = {
    **fixtures.NEXTJS_BARE,
    "migrations/0001_drop_customers.sql": "DROP TABLE customers;\n",
}

CRON_NO_HANDLING = {
    **fixtures.NEXTJS_BARE,
    "src/cron/cleanup.ts": ("export async function cleanup() {\n"
                            "  const rows = await db.stale();\n"
                            "  await db.remove(rows);\n}\n"),
}
CRON_WITH_HANDLING = {
    **fixtures.NEXTJS_BARE,
    "src/cron/cleanup.ts": ("export async function cleanup() {\n  try {\n"
                           "    const rows = await db.stale();\n    await db.remove(rows);\n"
                           "  } catch (e) {\n    logger.error(e);\n  }\n}\n"),
}
MULTI_SURFACE_UNCOORDINATED = {
    **fixtures.NEXTJS_BARE,
    "package.json": json.dumps({"dependencies": {"next": "15.0.0", "convex": "1.0.0"}}),
    "convex/schema.ts": "export default {}",
    "vercel.json": "{}",
    "README.md": "# App\n\nRun npm run dev to start it locally.\n",
}

FIXTURES = {
    "nextjs-bare": (fixtures.NEXTJS_BARE, None),
    "cron-no-error-handling": (CRON_NO_HANDLING, None),
    "cron-with-error-handling": (CRON_WITH_HANDLING, None),
    "cron-in-a-library": (CRON_NO_HANDLING, "library"),
    "multi-surface-uncoordinated": (MULTI_SURFACE_UNCOORDINATED, None),
    "nextjs-complete": (fixtures.NEXTJS_COMPLETE, None),
    "hollow": (fixtures.HOLLOW, None),
    "python-service": (PythonServiceRepo.FILES, None),
    "go-service": (GoRepoIsNotLiedTo.FILES, None),
    "library-profile": (GUARDED_ROUTES, "library"),
    "guarded-routes": (GUARDED_ROUTES, None),
    "fail-open-guard": (FAIL_OPEN_GUARD, None),
    "leaky-secrets": (LEAKY_SECRETS, None),
    "unsafe-route": (UNSAFE_ROUTE, None),
    "plain-migrations": (PLAIN_MIGRATIONS, None),
}

FIRING = {"fail", "warn"}


def build_grid() -> dict[str, set[str]]:
    grid: dict[str, set[str]] = {cid: set() for cid in ALL_CHECK_IDS}
    for _, (files, profile) in FIXTURES.items():
        categories, _ = prod_audit.run_audit(make_repo(files), profile)
        for cat in categories:
            for check in cat.checks:
                grid.setdefault(check.id, set()).add(check.status)
    return grid


GRID = build_grid()


class CoverageGrid(unittest.TestCase):
    def test_the_registered_id_list_matches_what_the_engine_emits(self):
        emitted = {cid for cid, seen in GRID.items() if seen}
        self.assertEqual(sorted(emitted), sorted(ALL_CHECK_IDS),
                         "a check was added or removed without updating ALL_CHECK_IDS")

    def test_every_check_has_a_fixture_where_it_fires(self):
        missing = sorted(c for c in ALL_CHECK_IDS if not GRID[c] & FIRING)
        self.assertEqual(missing, [], f"no fixture makes these fire: {missing}")

    def test_every_check_has_a_fixture_where_it_stays_quiet(self):
        missing = sorted(c for c in ALL_CHECK_IDS if "pass" not in GRID[c])
        self.assertEqual(missing, [], f"no fixture makes these pass: {missing}")

    def test_checks_that_can_be_skipped_have_a_fixture_that_skips_them(self):
        skippable = sorted(prod_audit.CHECK_SKIPS_BY_PROFILE["library"])
        missing = [c for c in skippable if "n/a" not in GRID.get(c, set())]
        self.assertEqual(missing, [], f"no fixture marks these n/a: {missing}")


class FalseNegativesTheGridFound(unittest.TestCase):
    """Both of these were invisible until the grid demanded a passing fixture."""

    def check(self, files, cid, profile=None):
        categories, _ = prod_audit.run_audit(make_repo(files), profile)
        return next(c for cat in categories for c in cat.checks if c.id == cid)

    def test_scoped_sentry_package_counts_as_error_tracking(self):
        files = {**fixtures.NEXTJS_BARE,
                 "package.json": json.dumps({"dependencies": {"next": "15.0.0",
                                                              "@sentry/nextjs": "8.0.0"}})}
        c = self.check(files, "log-2", profile="web-app")
        self.assertEqual(c.status, "pass", c.detail)

    def test_vercel_otel_counts_as_error_tracking(self):
        files = {**fixtures.NEXTJS_BARE,
                 "package.json": json.dumps({"dependencies": {"next": "15.0.0",
                                                              "@vercel/otel": "1.0.0"}})}
        self.assertEqual(self.check(files, "log-2", profile="web-app").status, "pass")

    def test_a_plain_migrations_folder_is_read_for_destructive_sql(self):
        c = self.check(PLAIN_MIGRATIONS, "ms-3", profile="web-app")
        self.assertEqual(c.status, "fail", c.detail)
        self.assertTrue(any("drop_customers" in e for e in c.evidence), c.evidence)


class Invariants(unittest.TestCase):
    """Five rules the engine must never break. Each one closes a whole class of
    bug, so it cannot come back one instance at a time.

    1. Never report about a file that is not there.        (test_prod_audit: Go fixture)
    2. Never claim a control exists from a text match      (here)
       without saying the evidence is weak.
    3. Never grade what it did not scan.                   (test_prod_audit: RefusesToGradeNothing)
    4. Never ship text its own linter rejects.             (test_prod_audit: HouseStyle)
    5. Every check has a firing case and a quiet case.     (CoverageGrid, above)
    """

    def all_checks(self):
        for name, (files, profile) in FIXTURES.items():
            categories, _ = prod_audit.run_audit(make_repo(files), profile)
            for cat in categories:
                for check in cat.checks:
                    yield name, check

    def test_a_pass_with_no_evidence_is_never_called_verified(self):
        bad = [f"{n}:{c.id}" for n, c in self.all_checks()
               if c.status == "pass" and not c.evidence and c.confidence != "weak"]
        self.assertEqual(bad, [], f"passing with nothing to show, but marked verified: {bad}")

    def test_every_failing_check_tells_the_reader_what_to_do(self):
        bad = [f"{n}:{c.id}" for n, c in self.all_checks()
               if c.status == "fail" and not c.recommendation.strip()]
        self.assertEqual(bad, [], f"a failure with no recommendation: {bad}")

    def test_no_check_ever_crashes_on_any_fixture(self):
        ids = {c.id for _, c in self.all_checks()}
        self.assertTrue(ids.issubset(set(ALL_CHECK_IDS)), ids - set(ALL_CHECK_IDS))

    def test_no_shipped_finding_text_uses_an_em_or_en_dash(self):
        bad = [f"{n}:{c.id}" for n, c in self.all_checks()
               if "\u2014" in (c.detail + c.recommendation)
               or "\u2013" in (c.detail + c.recommendation)]
        self.assertEqual(bad, [], f"em or en dash in a finding: {bad}")


if __name__ == "__main__":
    unittest.main()
