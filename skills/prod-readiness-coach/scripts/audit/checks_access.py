"""Checks about who is allowed to do what.

Broken access control is the most common way a small app hurts its users, and
it is the gap this tool shipped with for its first three versions. These checks
are deliberately shallow: they can tell you a guard is missing or that one
fails open, and they cannot tell you an authorization model is correct. Any
pass here is a starting point for a human, never a security review.
"""
import re

from .model import CheckResult
from .repo import Repo

AUTH_LIBS = [
    "@clerk/nextjs", "@clerk/clerk-react", "@clerk/backend", "next-auth", "@auth/core",
    "lucia", "better-auth", "@supabase/auth-helpers-nextjs", "@supabase/ssr",
    "@auth0/nextjs-auth0", "@workos-inc/node", "firebase-admin", "passport",
    "express-jwt", "jsonwebtoken", "@nestjs/passport", "django-allauth", "flask-login",
    "authlib", "devise", "pyjwt", "python-jose", "fastapi-users",
]
# Words that indicate a request handler actually consults an identity before acting.
GUARD_RX = re.compile(
    r"\b(?:auth|getSession|getServerSession|currentUser|requireUser|requireAuth|protect|"
    r"authorize|isOwner|isAdmin|verifyToken|jwt_required|login_required|current_user|"
    r"getToken|clerkClient|withAuth|ensureAuthenticated)\b", re.IGNORECASE)
ROUTE_GLOBS = [
    "**/app/api/**/route.ts", "**/app/api/**/route.js",
    "**/app/api/**/route.tsx", "**/app/api/**/route.jsx",
    "**/pages/api/**/*.ts", "**/pages/api/**/*.js",
    "**/routes/**/*.ts", "**/routes/**/*.js", "**/api/**/*.py",
]
# A route can be authenticated without a session. These are the two ways a
# machine caller proves itself, and the first version of auth-2 could see
# neither, so it called signed webhooks unguarded.
SIGNATURE_RX = re.compile(
    r"\bsvix\b|createHmac|timingSafeEqual|compare_digest|hmac"
    r"|x-[\w-]*-signature|signature[-_]?header|verifyHeader|verify_header"
    r"|constructEvent|verifyKey|nacl\.sign|ed25519",
    re.IGNORECASE)
SHARED_SECRET_RX = re.compile(
    r"(?:process\.env\.|import\.meta\.env\.|os\.environ(?:\.get)?[\[(]\s*[\'\"]|os\.getenv\(\s*[\'\"])"
    r"[A-Za-z0-9_]*(?:SECRET|TOKEN|API_?KEY|PASSWORD)",
    re.IGNORECASE)
# Auth that runs before the handler does. A file scan cannot prove a matcher
# covers a given route, so finding one lowers the claim rather than clearing it.
MIDDLEWARE_GLOBS = [
    "middleware.ts", "middleware.js", "src/middleware.ts", "src/middleware.js",
    "proxy.ts", "proxy.js", "src/proxy.ts", "src/proxy.js",
    "**/middleware.py", "**/middleware.ts", "**/middleware.js",
]
MIDDLEWARE_RX = re.compile(
    r"clerkMiddleware|createRouteMatcher|authMiddleware|auth\.protect\(|withAuth\("
    r"|app\.use\s*\(\s*[\w.]*(?:auth|passport|requireAuth|ensureAuth|jwt)"
    r"|add_middleware\s*\(|AuthenticationMiddleware"
    r"|dependencies\s*=\s*\[\s*Depends|before_request|before_action",
    re.IGNORECASE)
PUBLIC_PATTERN_RX = re.compile(r"[\'\"`](/[^\'\"`\s]*)[\'\"`]")


def _route_auth_mechanism(text: str) -> str:
    """Which in-file mechanism, if any, proves who is calling. '' when none."""
    if GUARD_RX.search(text):
        return "session or identity check"
    if SIGNATURE_RX.search(text):
        return "webhook signature verification"
    if SHARED_SECRET_RX.search(text):
        return "shared secret"
    return ""


def _matcher_middleware(repo: Repo) -> list[tuple[str, list[str]]]:
    """Files that guard requests before the handler, with any public paths listed."""
    found = []
    candidates = [f for f in repo.find_any(MIDDLEWARE_GLOBS) if "node_modules" not in f]
    candidates += [f for f in repo.code_files()
                   if f not in candidates and re.search(r"(?:^|/)(?:app|main|server|index)\.(?:py|ts|js)$", f)]
    for f in candidates:
        text = repo.read(f)
        if not MIDDLEWARE_RX.search(text):
            continue
        public = []
        block = re.search(r"createRouteMatcher\s*\(\s*\[(.*?)\]", text, re.S)
        if block:
            public = PUBLIC_PATTERN_RX.findall(block.group(1))
        found.append((f, public))
    return found
# A guard that returns "allowed" when its own configuration is missing.
# Real code rarely tests the env var inline. It reads it into a local first:
#   const owner = process.env.OWNER_EMAIL;
#   if (!owner) return true;
# so we learn the local names first, then look for the fail-open branch on them.
ENV_LOCAL_RX = re.compile(
    r"(?:const|let|var)\s+(\w+)\s*=\s*(?:process\.env\.|import\.meta\.env\.)\w+"
    r"|(\w+)\s*=\s*os\.(?:environ\.get|getenv)\(")
FAIL_OPEN_DIRECT_RX = re.compile(
    r"if\s*\(\s*!\s*(?:process\.env\.|import\.meta\.env\.)\w+\s*\)\s*\{?\s*return\s+true"
    r"|if\s+not\s+os\.(?:environ\.get|getenv)\([^)]*\)\s*:\s*return\s+True",
    re.IGNORECASE)


def _fail_open_lines(text: str) -> list[str]:
    """Lines where a permission check grants access because its setting is absent."""
    env_locals = {m.group(1) or m.group(2) for m in ENV_LOCAL_RX.finditer(text)} - {None}
    hits = []
    for line in text.splitlines():
        stripped = line.strip()
        if FAIL_OPEN_DIRECT_RX.search(stripped):
            hits.append(stripped)
            continue
        for name in env_locals:
            if re.search(rf"if\s*\(\s*!\s*{re.escape(name)}\s*\)\s*\{{?\s*return\s+true", stripped, re.I) \
                    or re.search(rf"if\s+not\s+{re.escape(name)}\s*:\s*return\s+True", stripped):
                hits.append(stripped)
                break
    return hits


REF = "https://owasp.org/Top10/A01_2021-Broken_Access_Control/"


def check_access_control(repo: Repo) -> list[CheckResult]:
    results = []
    pkg = repo.package_json()
    dep_names = {n.lower() for n in ((pkg.get("dependencies", {}) | pkg.get("devDependencies", {})).keys()
                                     if pkg else [])}
    dep_names |= repo.requirement_names()
    found = [lib for lib in AUTH_LIBS if lib.lower() in dep_names]

    results.append(CheckResult(
        "auth-1", "Access Control", "Authentication mechanism present",
        "pass" if found else "fail",
        "info" if found else "high",
        f"Authentication dependency detected: {', '.join(found)}." if found else
        "No authentication library found in the dependency list. If this app has "
        "users or non-public data, nothing here proves who a request belongs to.",
        "" if found else "Add an authentication library appropriate to the stack, or, if the "
        "app is genuinely public and read-only, say so in the README so the next reader knows "
        "it is a decision rather than an omission.",
        evidence=[f"dependency: {lib}" for lib in found],
        best_practice_ref=REF,
    ))

    route_files = [f for f in repo.find_any(ROUTE_GLOBS) if "node_modules" not in f]
    if route_files:
        mechanisms = {f: _route_auth_mechanism(repo.read(f)) for f in route_files}
        unguarded = [f for f, m in mechanisms.items() if not m]
        middleware = _matcher_middleware(repo)
        if not unguarded:
            kinds = sorted({m for m in mechanisms.values() if m})
            results.append(CheckResult(
                "auth-2", "Access Control", "Request handlers consult an identity",
                "pass", "info",
                f"All {len(route_files)} request handler(s) carry an auth mechanism "
                f"({', '.join(kinds)}). This says the check is mentioned, not that it is correct.",
                evidence=route_files[:10],
                best_practice_ref=REF,
            ))
        elif middleware:
            mw_files = ", ".join(f for f, _ in middleware)
            public = sorted({p for _, pats in middleware for p in pats})
            results.append(CheckResult(
                "auth-2", "Access Control", "Request handlers consult an identity",
                "warn", "low",
                f"{len(unguarded)} of {len(route_files)} request handler(s) hold no auth check "
                f"of their own. They appear to rely on {mw_files}, which guards requests before "
                "a handler runs. Reading files cannot prove that its route patterns cover these "
                "paths, so this is a thing to confirm, not a finding.",
                "Open the middleware and check its matcher against the handlers listed. Anything "
                "the matcher skips has no guard at all. Then call one protected route while "
                "signed out and confirm it is refused.",
                evidence=[f"middleware: {f}" for f, _ in middleware]
                + [f"public pattern: {p}" for p in public[:8]]
                + [f"relies on middleware: {f}" for f in unguarded[:8]],
                best_practice_ref=REF,
            ))
        else:
            results.append(CheckResult(
                "auth-2", "Access Control", "Request handlers consult an identity",
                "fail", "high",
                f"{len(unguarded)} of {len(route_files)} request handler(s) never mention an "
                "auth check, and no request middleware was found that could guard them first. "
                "A handler that does not ask who is calling will serve anyone who can reach the URL.",
                "Open each file listed. If it is meant to be public, note that in a comment so "
                "the next reader can tell 'public on purpose' from 'forgotten'. If it is not, "
                "add the guard your auth library provides, and test it by calling the route "
                "while signed out and while signed in as somebody else.",
                evidence=unguarded[:10],
                best_practice_ref=REF,
            ))

    fail_open = []
    for f in repo.code_files():
        for line in _fail_open_lines(repo.read(f)):
            fail_open.append(f"{f}: {line[:90]}")
    results.append(CheckResult(
        "auth-3", "Access Control", "No guard that fails open on missing configuration",
        "fail" if fail_open else "pass",
        "critical" if fail_open else "info",
        "A permission check appears to grant access when its own environment variable is "
        "unset. On a fresh deploy, or a fork, or after a rename, that means everyone passes."
        if fail_open else
        "No permission check was found that returns 'allowed' when its configuration is missing.",
        "Make the guard deny by default: when the variable is missing, refuse and log loudly. "
        "A missing setting is a broken deploy, not an open door." if fail_open else "",
        evidence=fail_open[:5] or ["scope: searched code files for guards that return true on missing config"],
        best_practice_ref=REF,
    ))
    return results
