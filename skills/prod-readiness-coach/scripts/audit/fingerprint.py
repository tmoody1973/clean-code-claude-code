"""What kind of project is this, and where does it deploy."""
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from .model import CHECK_SKIPS_BY_PROFILE, PROFILES
from .repo import Repo

# --------------------------------------------------------------------------
# Stack fingerprinting, deterministic detection of runtime/framework/deploy
# signals from manifests and deploy configs. This is what lets the skill
# layer load only the reference adapter file(s) relevant to THIS repo
# (progressive disclosure) instead of hardcoding stack-specific advice into
# one generic prompt. Two runs on the same commit must produce the same
# fingerprint, no LLM involvement here.
# --------------------------------------------------------------------------

@dataclass
class StackFingerprint:
    languages: list[str] = field(default_factory=list)
    package_managers: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    deploy_surfaces: list[str] = field(default_factory=list)
    deploy_evidence: dict[str, list[str]] = field(default_factory=dict)
    runtimes: list[str] = field(default_factory=list)
    migration_tooling: list[str] = field(default_factory=list)
    waivers_applied: list = field(default_factory=list)
    waiver_problems: list = field(default_factory=list)
    profile: str = "web-app"
    profile_source: str = "default"  # "given" | "guessed" | "default"
    multi_surface: bool = False
    multi_surface_evidence: list[str] = field(default_factory=list)
    adapters_matched: list[str] = field(default_factory=list)

    def add_surface(self, name: str, evidence: str) -> None:
        if name not in self.deploy_surfaces:
            self.deploy_surfaces.append(name)
        self.deploy_evidence.setdefault(name, [])
        if evidence not in self.deploy_evidence[name]:
            self.deploy_evidence[name].append(evidence)


def parse_compose_services(content: str) -> dict[str, str]:
    """Lightweight, stdlib-only extraction of top-level service blocks from a
    docker-compose file. Not a full YAML parser, deliberately heuristic and
    indentation-based, which is sufficient for the standard 2-space-indented
    `services:` block every compose file uses, and keeps this tool dependency-free.
    """
    services: dict[str, str] = {}
    lines = content.splitlines()
    in_services = False
    current: Optional[str] = None
    buf: list[str] = []
    for line in lines:
        if re.match(r"^services:\s*$", line):
            in_services = True
            continue
        if not in_services:
            continue
        if re.match(r"^\S", line):  # dedented back to top-level key, services block ended
            if current:
                services[current] = "\n".join(buf)
            break
        m = re.match(r"^  ([\w.-]+):\s*$", line)
        if m:
            if current:
                services[current] = "\n".join(buf)
            current = m.group(1)
            buf = []
        elif current is not None:
            buf.append(line)
    if current:
        services[current] = "\n".join(buf)
    return services


def detect_stack_fingerprint(repo: Repo) -> StackFingerprint:
    fp = StackFingerprint()
    pkg = repo.package_json()
    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

    # --- Languages & package managers -------------------------------------
    if pkg:
        fp.languages.append("typescript" if repo.exists("tsconfig.json") else "javascript")
        if repo.exists("bun.lock", "bun.lockb") or pkg.get("packageManager", "").startswith("bun"):
            fp.package_managers.append("bun")
        elif repo.exists("pnpm-lock.yaml"):
            fp.package_managers.append("pnpm")
        elif repo.exists("yarn.lock"):
            fp.package_managers.append("yarn")
        elif repo.exists("package-lock.json"):
            fp.package_managers.append("npm")
    if repo.requirements_text() or repo.exists("requirements.txt", "pyproject.toml", "Pipfile"):
        fp.languages.append("python")
        fp.package_managers.append("pip" if repo.exists("requirements.txt") else "poetry/pipenv")
    if repo.exists("go.mod"):
        fp.languages.append("go")
        fp.package_managers.append("go modules")

    # --- Frameworks ---------------------------------------------------------
    framework_deps = {
        "next": "nextjs", "convex": "convex", "@remix-run/dev": "remix",
        "express": "express", "fastify": "fastify", "@sveltejs/kit": "sveltekit",
        "nuxt": "nuxt", "@nestjs/core": "nestjs", "astro": "astro",
    }
    for dep_name, fw in framework_deps.items():
        if dep_name in deps:
            fp.frameworks.append(fw)
    req_text = repo.requirements_text().lower()
    for needle, fw in (("django", "django"), ("flask", "flask"), ("fastapi", "fastapi")):
        if needle in req_text:
            fp.frameworks.append(fw)

    # --- Deploy surfaces ------------------------------------------------
    member_vercel = repo.find_any(["apps/*/vercel.json", "packages/*/vercel.json"])
    if repo.exists("vercel.json") or repo.exists(".vercel") or member_vercel or "vercel-build" in pkg.get("scripts", {}):
        fp.add_surface("vercel", repo.exists("vercel.json", ".vercel") or (member_vercel[0] if member_vercel else "package.json scripts.vercel-build"))
    def anywhere(*names: str) -> list[str]:
        """Root or a workspace member (apps/*, packages/*, services/*)."""
        pats = list(names) + [f"{d}/*/{n}" for d in ("apps", "packages", "services") for n in names]
        return repo.find_any(pats)
    for surface, names in (("netlify", ("netlify.toml",)), ("fly", ("fly.toml",)),
                           ("cloudflare-workers", ("wrangler.toml", "wrangler.jsonc", "wrangler.json")),
                           ("render", ("render.yaml",)), ("heroku", ("Procfile",))):
        hits = anywhere(*names)
        if hits:
            fp.add_surface(surface, hits[0])
    dockerfiles = repo.find_any(["**/Dockerfile", "Dockerfile"])
    compose_files = repo.find_any(["docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"])
    if dockerfiles or compose_files:
        fp.add_surface("docker", ", ".join(dockerfiles[:3] + compose_files[:2]))
    convex_schema = repo.exists("convex/schema.ts", "convex/schema.js") or repo.find_any(["**/convex/schema.ts", "**/convex/schema.js"])
    if "convex" in fp.frameworks or convex_schema:
        fp.add_surface("convex", "convex/ directory or convex dependency")

    # --- Runtimes -------------------------------------------------------
    if "convex" in fp.frameworks:
        fp.runtimes.append("convex-v8-isolate")
        if repo.grep(r'^[\'"]use node[\'"]', paths=repo.find_any(["**/convex/**/*.ts", "**/convex/**/*.js"])):
            fp.runtimes.append("convex-node")
    if "cloudflare-workers" in fp.deploy_surfaces:
        fp.runtimes.append("cloudflare-v8-isolate")
    if "nextjs" in fp.frameworks:
        fp.runtimes.append("node")
        if repo.grep(r"runtime\s*[:=]\s*['\"]edge['\"]") or repo.exists("middleware.ts", "middleware.js"):
            fp.runtimes.append("edge")
    if "python" in fp.languages:
        fp.runtimes.append("python")

    # --- Migration tooling ------------------------------------------------
    if repo.find_any(["prisma/migrations/*"]):
        fp.migration_tooling.append("prisma")
    if repo.exists("drizzle.config.ts", "drizzle.config.js") or repo.find_any(["drizzle/*", "**/drizzle/*"]):
        fp.migration_tooling.append("drizzle")
    if repo.find_any(["alembic/versions/*"]):
        fp.migration_tooling.append("alembic")
    if repo.find_any(["db/migrate/*"]):
        fp.migration_tooling.append("rails-migrations")
    if convex_schema:
        fp.migration_tooling.append("convex-schema")

    # --- Multi-surface detection ------------------------------------------
    # Most Next.js apps on Vercel have no vercel.json. If Next.js is present and
    # no other frontend host was detected, assume Vercel (flagged as inferred).
    root_docker = bool(repo.exists("Dockerfile", "docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"))
    frontend_hosts = ("vercel", "netlify", "cloudflare-workers", "render", "heroku")
    if "nextjs" in fp.frameworks and not any(sfc in fp.deploy_surfaces for sfc in frontend_hosts) \
            and not root_docker and not (repo.exists("fly.toml")):
        fp.add_surface("vercel", "inferred: Next.js with no other frontend host config (confirm)")

    independently_deployable = {"vercel", "netlify", "fly", "cloudflare-workers", "render", "heroku", "convex"}
    matched_platforms = [s for s in fp.deploy_surfaces if s in independently_deployable]
    if len(matched_platforms) >= 2:
        fp.multi_surface = True
        fp.multi_surface_evidence.append(
            f"Multiple independently-deployable platforms detected: {', '.join(sorted(matched_platforms))}. "
            "These deploy and roll back on separate timelines."
        )
    for cf in compose_files:
        content = repo.read(cf)
        services = parse_compose_services(content)
        migrate_services = [s for s, block in services.items()
                             if re.search(r"migrat", s, re.IGNORECASE) or re.search(r"migrat", block, re.IGNORECASE)]
        app_services = [s for s in services if s not in migrate_services]
        if migrate_services and app_services:
            fp.multi_surface = True
            fp.multi_surface_evidence.append(
                f"{cf}: dedicated migration service(s) {migrate_services} run alongside "
                f"{len(app_services)} app/data service(s) ({', '.join(app_services[:6])}). "
                "A bad deploy needs the app rolled back AND the migration's effects accounted for."
            )

    # --- Adapter matching (progressive disclosure) -------------------------
    if "vercel" in fp.deploy_surfaces and "nextjs" in fp.frameworks:
        fp.adapters_matched.append("nextjs-vercel")
    if "convex" in fp.deploy_surfaces:
        fp.adapters_matched.append("convex")
    if "fly" in fp.deploy_surfaces:
        fp.adapters_matched.append("fly")
    if "cloudflare-workers" in fp.deploy_surfaces:
        fp.adapters_matched.append("cloudflare-workers")
    if "netlify" in fp.deploy_surfaces:
        fp.adapters_matched.append("netlify")

    fp.languages = sorted(set(fp.languages))
    fp.package_managers = sorted(set(fp.package_managers))
    fp.frameworks = sorted(set(fp.frameworks))
    fp.runtimes = sorted(set(fp.runtimes))
    fp.migration_tooling = sorted(set(fp.migration_tooling))
    return fp


