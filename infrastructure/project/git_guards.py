"""Git index guards for tracked projects and generated artifacts."""

from __future__ import annotations

import fnmatch
import subprocess
from pathlib import Path

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

# Derived from PUBLIC_PROJECT_NAMES — the single roster source of truth — so it
# can never drift from the public exemplar roster. (Before 2026-06-10 this was a
# hand-maintained literal.)
ALLOWED_PROJECT_DIRS: tuple[str, ...] = tuple(f"projects/{name}/" for name in PUBLIC_PROJECT_NAMES)

# Navigation docs that may live directly under projects/ or the public
# projects/templates/ directory. This is an EXPLICIT allowlist, not a wildcard:
# a name-blind `projects/[^/]+\.md` pattern would let any future top-level
# markdown file (notes, a leaked private roster, an accidental
# `git add -f projects/secret.md`) sail past the confidentiality guard. Adding
# a new nav doc is a deliberate act that must be made here.
ALLOWED_PROJECTS_TOPLEVEL_FILES: frozenset[str] = frozenset(
    {
        "projects/AGENTS.md",
        "projects/PAI.md",
        "projects/PROJECTS_PARADIGM.md",
        "projects/README.md",
        "projects/templates/AGENTS.md",
    }
)


class _ExplicitToplevelAllowlist:
    """`.match()`-compatible shim over the explicit nav-doc allowlist.

    Preserves the historical ``ALLOWED_PROJECTS_TOPLEVEL.match(path)`` call site
    in :mod:`infrastructure.project.codegraph` while swapping the permissive
    wildcard regex for a closed set. Returns a truthy object on an exact match,
    ``None`` otherwise — matching ``re.Pattern.match`` truthiness semantics.
    """

    def match(self, path: str) -> str | None:
        return path if path in ALLOWED_PROJECTS_TOPLEVEL_FILES else None


ALLOWED_PROJECTS_TOPLEVEL = _ExplicitToplevelAllowlist()

GENERATED_ARTIFACT_PATTERNS: tuple[str, ...] = (
    ".codegraph/*",
    ".coverage",
    ".coverage.*",
    ".DS_Store",
    "*/.codegraph/*",
    "*/.DS_Store",
    "*.egg-info/*",
    "*/.egg-info/*",
    "coverage.json",
    "coverage*.xml",
    "coverage_project.json",
    "htmlcov/*",
    "output/*",
    "projects/*/output/*",
    "projects/*/*/output/*",
)


def offending_tracked_projects(repo_root: Path) -> list[str]:
    proc = subprocess.run(
        ["git", "ls-files", "-z", "projects/"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    paths = [p for p in proc.stdout.decode("utf-8").split("\0") if p]
    offenders: list[str] = []
    for path in paths:
        normalized = path.replace("\\", "/")
        if ALLOWED_PROJECTS_TOPLEVEL.match(normalized):
            continue
        if any(normalized.startswith(prefix) for prefix in ALLOWED_PROJECT_DIRS):
            continue
        offenders.append(normalized)
    return sorted(offenders)


def is_generated_artifact_path(path: str) -> bool:
    # No output/ path is exempt: all rendered output is disposable and must
    # never be committed (see .gitignore — the former living render-proof
    # exemption was dead and was removed). If render-proof outputs are ever
    # reintroduced, restore an output/<name>/ allowlist here AND the matching
    # .gitignore negation block together.
    normalized = path.replace("\\", "/")
    return any(fnmatch.fnmatch(normalized, pattern) for pattern in GENERATED_ARTIFACT_PATTERNS)


def tracked_generated_artifacts(repo_root: Path) -> list[str]:
    proc = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    paths = [p for p in proc.stdout.decode("utf-8").split("\0") if p]
    return sorted(path for path in paths if is_generated_artifact_path(path))
