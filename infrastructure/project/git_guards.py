"""Git index guards for tracked projects and generated artifacts."""

from __future__ import annotations

import fnmatch
import re
import subprocess
from pathlib import Path

ALLOWED_PROJECT_DIRS: tuple[str, ...] = (
    "projects/template_code_project/",
    "projects/template_prose_project/",
)
ALLOWED_PROJECTS_TOPLEVEL = re.compile(r"^projects/[^/]+\.md$")

GENERATED_ARTIFACT_PATTERNS: tuple[str, ...] = (
    ".coverage",
    ".coverage.*",
    ".DS_Store",
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

ALLOWED_TRACKED_OUTPUT_PREFIXES: tuple[str, ...] = (
    "output/template_code_project/",
    "output/template_prose_project/",
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
