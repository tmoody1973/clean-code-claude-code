"""Named repository fixtures. Together these are the coverage grid.

Every check has to prove two things: that it fires when a control is missing,
and that it stays quiet when the control is there. Only the first half was ever
tested, which is how auth-2 shipped wrong about half the time it spoke.

The grid is computed by running the audit over these fixtures, not by anyone
maintaining a list. Add a fixture and cells fill in on their own. Add a check
with no fixture that exercises it and test_coverage_grid fails.
"""
import json

# --------------------------------------------------------------------------
# Node / Next.js
# --------------------------------------------------------------------------

NEXTJS_BARE = {
    "package.json": json.dumps({"dependencies": {"next": "15.0.0"}}),
    "tsconfig.json": "{}",
    "package-lock.json": "{}",
}

_COMPLETE_CI = """
name: CI
on:
  pull_request:
  push:
    branches: [main]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: npm ci
      - run: npm run lint
      - run: tsc --noEmit
      - run: npx vitest run --coverage
      - run: npm audit --audit-level=high
      - run: npx playwright test
      - run: vercel deploy --prod
"""

_COMPLETE_RUNBOOK = """
# Runbook

## Rollback across every surface

This app deploys to two places that can drift apart, so a rollback has to cover
both. Vercel hosts the web app; Convex holds the database and the functions.

1. Vercel: open the deployment list, pick the last good build, use Instant
   Rollback. This swaps the routing layer and takes about a minute.
2. Convex: run `npx convex deploy` from the matching git tag so the functions and
   the schema go back together with the frontend.
3. If a migration ran, apply the reverse migration in `migrations/` before the
   Convex step, because rolling back code does not undo a schema change.

## When the database is unreachable

The health route at /api/health returns 503 and the load balancer drains the
instance. Page the on-call engineer when the error rate passes two percent for
five minutes running.

## Backups

Convex keeps daily snapshots. To restore, use the dashboard export from the day
before the incident and re-import it. Confirm row counts before pointing traffic
back.
"""

NEXTJS_COMPLETE = {
    "package.json": json.dumps({
        "dependencies": {"next": "15.0.0", "convex": "1.0.0", "@clerk/nextjs": "6.0.0",
                         "pino": "9.0.0", "@sentry/nextjs": "8.0.0", "@upstash/ratelimit": "2.0.0"},
        "devDependencies": {"vitest": "2.0.0", "@playwright/test": "1.0.0", "typescript": "5.0.0"},
        "scripts": {"test": "vitest run", "lint": "eslint .", "build": "next build"},
    }),
    "package-lock.json": "{}",
    "tsconfig.json": json.dumps({"compilerOptions": {"strict": True}}),
    "vitest.config.ts": "export default { test: { coverage: { lines: 80 } } }",
    "playwright.config.ts": "export default { testDir: './e2e' }",
    "vercel.json": json.dumps({"env": {"NEXT_PUBLIC_CONVEX_URL": "@convex-url"}}),
    "convex/schema.ts": "export default {}",
    "next.config.ts": 'export default { env: { STAGE: process.env.VERCEL_ENV } }',
    ".github/workflows/ci.yml": _COMPLETE_CI,
    ".github/dependabot.yml": 'version: 2\nupdates:\n  - package-ecosystem: npm\n    directory: "/"\n',
    ".env.example": "CONVEX_URL=\nCLERK_SECRET_KEY=\nSENTRY_DSN=\n",
    ".env.production.example": "CONVEX_URL=\n",
    ".env.development.example": "CONVEX_URL=\n",
    ".gitignore": ".env\n.env.local\n!.env.example\nnode_modules\n",
    "CLAUDE.md": ("Next.js app on Vercel with Convex behind it. Build with npm run build. "
                  "Test with npm test. Lint with npm run lint. Rollback needs both surfaces, "
                  "see docs/runbook.md. Auth is Clerk, enforced in src/middleware.ts, and every "
                  "route not on the public list is protected before the handler runs."),
    "docs/runbook.md": _COMPLETE_RUNBOOK,
    "README.md": ("# App\n\nDeployed to Vercel with a Convex backend. To roll back, follow the "
                  "coordinated procedure in docs/runbook.md, which covers Vercel and Convex "
                  "together and tells you when to reverse a migration first. Backups are the "
                  "Convex daily snapshots.\n"),
    "src/middleware.ts": (
        'import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";\n'
        'const isPublicRoute = createRouteMatcher(["/", "/sign-in(.*)"]);\n'
        'export default clerkMiddleware(async (auth, req) => {\n'
        '  if (!isPublicRoute(req)) await auth.protect();\n});\n'),
    "src/app/api/health/route.ts": (
        'export async function GET() {\n  return Response.json({ status: "ok" });\n}\n'),
    "src/app/api/items/route.ts": (
        'import { auth } from "@clerk/nextjs/server";\n'
        'import { ratelimit } from "@/lib/ratelimit";\n'
        'import { logger } from "@/lib/logger";\n\n'
        'export async function GET(req) {\n'
        '  const { userId } = await auth();\n'
        '  if (!userId) return new Response("no", { status: 401 });\n'
        '  const requestId = req.headers.get("x-request-id") ?? crypto.randomUUID();\n'
        '  const { success } = await ratelimit.limit(userId);\n'
        '  if (!success) return new Response("slow down", { status: 429 });\n'
        '  try {\n    logger.info({ requestId }, "items");\n    return Response.json([]);\n'
        '  } catch (e) {\n    logger.error({ requestId, e }, "items failed");\n'
        '    return new Response("error", { status: 500 });\n  }\n}\n'),
    "src/lib/ratelimit.ts": (
        'import { Ratelimit } from "@upstash/ratelimit";\n'
        'export const ratelimit = new Ratelimit({ limiter: Ratelimit.slidingWindow(10, "10 s") });\n'),
    "src/lib/logger.ts": 'import pino from "pino";\nexport const logger = pino();\n',
    "src/lib/owner.ts": ('const owner = process.env.OWNER_EMAIL;\n'
                         'export function isOwner(email) {\n'
                         '  if (!owner) return false;\n  return email === owner;\n}\n'),
    "migrations/0001_add_items.sql": "ALTER TABLE items ADD COLUMN label text;\n",
    "tests/items.test.ts": 'import { test } from "vitest";\ntest("items", () => {});\n',
    "e2e/checkout.spec.ts": 'import { test } from "@playwright/test";\ntest("checkout", async () => {});\n',
}

# A repo where every control is a costume: the file exists, the substance does not.
HOLLOW = {
    "package.json": json.dumps({"dependencies": {"next": "15.0.0"},
                                "scripts": {"test": "echo 'test skipped'"}}),
    "package-lock.json": "{}",
    "tsconfig.json": "{}",
    ".github/workflows/ci.yml": ("on: push\njobs:\n  t:\n    runs-on: ubuntu-latest\n"
                                 "    steps:\n      - run: echo \"running tests\"\n"),
    "docs/runbook.md": "# Runbook\n\nTODO: write this.\n",
    "README.md": "# App\n\n- [ ] document the rollback\n",
    ".gitignore": "node_modules\n",
    "src/app/api/thing/route.ts": "export async function GET() { return Response.json({}) }\n",
    "migrations/0002_drop.sql": "DROP TABLE customers;\n",
}
