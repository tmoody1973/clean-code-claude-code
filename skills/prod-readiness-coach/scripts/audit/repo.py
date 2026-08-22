"""Reading a repository safely: tracked files, greps, symlink containment."""
import fnmatch
import json
import re
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

# --------------------------------------------------------------------------
# Repo scanning helpers
# --------------------------------------------------------------------------

DEFAULT_EXCLUDE_DIRS = {
    ".git", "node_modules", ".next", "dist", "build", "out", "coverage",
    ".venv", "venv", "__pycache__", ".pnpm", ".turbo", ".vercel", "vendor",
    ".cache", "target", ".idea", ".vscode",
}

CODE_EXTS = {
    ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py", ".go", ".rb",
    ".java", ".kt", ".rs", ".php", ".cs",
}
# Secrets live in config as often as in code, so the secret scan covers more.
SECRET_SCAN_EXTS = CODE_EXTS | {
    ".yaml", ".yml", ".json", ".toml", ".env", ".sh", ".tf", ".ini", ".cfg", ".properties",
}
COMMENT_LINE_RX = re.compile(r"^\s*(#|//|/\*|\*|<!--|--)")


class Repo:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self._git_files: Optional[list[str]] = None
        self._pkg_cache: Optional[dict] = None

    def is_git_repo(self) -> bool:
        return (self.root / ".git").exists()

    def git_files(self) -> list[str]:
        """Files tracked by git (preferred — respects .gitignore automatically)."""
        if self._git_files is not None:
            return self._git_files
        if self.is_git_repo():
            try:
                out = subprocess.run(
                    ["git", "-C", str(self.root), "ls-files"],
                    capture_output=True, text=True, timeout=30, check=True,
                )
                self._git_files = [l for l in out.stdout.splitlines() if l.strip()]
                return self._git_files
            except Exception:
                pass
        # Fallback: walk filesystem excluding common junk dirs.
        files = []
        for p in self.root.rglob("*"):
            if p.is_dir():
                continue
            if any(part in DEFAULT_EXCLUDE_DIRS for part in p.parts):
                continue
            files.append(str(p.relative_to(self.root)))
        self._git_files = files
        return self._git_files

    def untracked_files(self) -> list[str]:
        """Untracked, non-ignored files. Empty when not a git repo (walk already covers them)."""
        if not self.is_git_repo():
            return []
        try:
            out = subprocess.run(
                ["git", "-C", str(self.root), "ls-files", "--others", "--exclude-standard"],
                capture_output=True, text=True, timeout=30, check=True,
            )
            return [l for l in out.stdout.splitlines() if l.strip()]
        except Exception:
            return []

    def exists(self, *candidates: str) -> Optional[str]:
        """Return the first candidate path (relative) that exists on disk, else None."""
        for c in candidates:
            if (self.root / c).exists():
                return c
        return None

    def glob(self, pattern: str) -> list[str]:
        """Glob within tracked files (case-sensitive fnmatch), pattern uses '**' for recursion."""
        matches = []
        for f in self.git_files():
            if fnmatch.fnmatch(f, pattern) or fnmatch.fnmatch("/" + f, pattern):
                matches.append(f)
        return matches

    def find_any(self, patterns: list[str]) -> list[str]:
        found = []
        for pat in patterns:
            found.extend(self.glob(pat))
        return sorted(set(found))

    def read(self, relpath: str, max_bytes: int = 200_000) -> str:
        try:
            p = self.root / relpath
            # Never follow a symlink out of the repository. A cloned repo is
            # untrusted input; a link named config.env could point at ~/.aws.
            if not p.resolve().is_relative_to(self.root.resolve()):
                return ""
            data = p.read_bytes()[:max_bytes]
            return data.decode("utf-8", errors="ignore")
        except Exception:
            return ""

    def grep(self, pattern: str, paths: Optional[list[str]] = None, flags=re.IGNORECASE,
             skip_comments: bool = True, with_lineno: bool = False) -> list:
        """Return (file, matching line) for regex pattern across given files (or all code files).
        Comment lines are skipped by default so a TODO never counts as an implementation."""
        rx = re.compile(pattern, flags)
        hits = []
        target_files = paths if paths is not None else [
            f for f in self.git_files() if Path(f).suffix in CODE_EXTS
        ]
        for f in target_files:
            content = self.read(f)
            if not content:
                continue
            for lineno, line in enumerate(content.splitlines(), 1):
                if skip_comments and COMMENT_LINE_RX.match(line):
                    continue
                if rx.search(line):
                    hits.append((f, line.strip()[:160]) if not with_lineno else (f, lineno, line))
        return hits

    def _read_json(self, relpath: str) -> dict:
        try:
            return json.loads(self.read(relpath)) if (self.root / relpath).exists() else {}
        except Exception:
            return {}

    def workspace_package_files(self) -> list[str]:
        """package.json files of workspace members in a monorepo (pnpm/turbo/npm/yarn workspaces)."""
        root = self._read_json("package.json")
        is_monorepo = bool(root.get("workspaces")) or self.exists("pnpm-workspace.yaml", "turbo.json", "lerna.json", "nx.json")
        if not is_monorepo:
            return []
        return [f for f in self.find_any(["apps/*/package.json", "packages/*/package.json", "services/*/package.json"])
                if "node_modules" not in f]

    def package_json(self) -> dict:
        """Root package.json, with workspace members' dependencies and scripts merged in.
        A monorepo's frameworks live in apps/* and packages/*, not at the root."""
        if self._pkg_cache is not None:
            return self._pkg_cache
        root = self._read_json("package.json")
        merged = dict(root)
        for key in ("dependencies", "devDependencies", "scripts"):
            merged[key] = dict(root.get(key, {}))
        for f in self.workspace_package_files():
            member = self._read_json(f)
            for key in ("dependencies", "devDependencies"):
                merged[key] = {**member.get(key, {}), **merged[key]}
            for name, cmd in member.get("scripts", {}).items():
                merged["scripts"].setdefault(name, cmd)
        self._pkg_cache = merged
        return merged

    def requirements_text(self) -> str:
        parts = []
        for f in ("requirements.txt", "pyproject.toml", "Pipfile"):
            if (self.root / f).exists():
                parts.append(self.read(f))
        return "\n".join(parts)


