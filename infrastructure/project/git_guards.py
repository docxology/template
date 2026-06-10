"""Git index guards for tracked projects and generated artifacts."""

from __future__ import annotations

import fnmatch
import re
import subprocess
from pathlib import Path

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

# Both allowlists derive from PUBLIC_PROJECT_NAMES — the single roster source of
# truth — so they can never drift from the public exemplar roster. (Before
# 2026-06-10 these were hand-maintained literals and ALLOWED_TRACKED_OUTPUT_PREFIXES
# had silently fallen two exemplars behind the roster.)
ALLOWED_PROJECT_DIRS: tuple[str, ...] = tuple(f"projects/{name}/" for name in PUBLIC_PROJECT_NAMES)
# Repo-level navigation docs may live directly under projects/ (projects/*.md).
ALLOWED_PROJECTS_TOPLEVEL = re.compile(r"^projects/[^/]+\.md$")

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

# Public exemplar rendered output may be tracked as living render-proof (the
# published papers). Scoped to PUBLIC_PROJECT_NAMES only — every other
# project's output (confidential/rotating) stays ignored and is NEVER allowed
# here. Only repo-level output/<name>/ is allowed; project-local
# projects/<name>/output/ remains a disposable working tree.
ALLOWED_TRACKED_OUTPUT_PREFIXES: tuple[str, ...] = tuple(f"output/{name}/" for name in PUBLIC_PROJECT_NAMES)


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
    normalized = path.replace("\\", "/")
    if any(normalized.startswith(prefix) for prefix in ALLOWED_TRACKED_OUTPUT_PREFIXES):
        return False
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
