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
    "**/pages/api/**/*.ts", "**/pages/api/**/*.js",
    "**/routes/**/*.ts", "**/routes/**/*.js", "**/api/**/*.py",
]
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
    dep_names |= {re.split(r"[=<>!~\[; ]", line.strip(), 1)[0].lower()
                  for line in repo.requirements_text().splitlines()
                  if line.strip() and not line.lstrip().startswith("#")}
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
        unguarded = [f for f in route_files if not GUARD_RX.search(repo.read(f))]
        if unguarded:
            results.append(CheckResult(
                "auth-2", "Access Control", "Request handlers consult an identity",
                "fail", "high",
                f"{len(unguarded)} of {len(route_files)} request handler(s) never mention an "
                "auth check. A handler that does not ask who is calling will serve anyone who "
                "can reach the URL.",
                "Open each file listed. If it is meant to be public, note that in a comment so "
                "the next reader can tell 'public on purpose' from 'forgotten'. If it is not, "
                "add the guard your auth library provides, and test it by calling the route "
                "while signed out and while signed in as somebody else.",
                evidence=unguarded[:10],
                best_practice_ref=REF,
            ))
        else:
            results.append(CheckResult(
                "auth-2", "Access Control", "Request handlers consult an identity",
                "pass", "info",
                f"All {len(route_files)} request handler(s) reference an auth check. This says "
                "the check is mentioned, not that it is correct.",
                evidence=route_files[:10],
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
