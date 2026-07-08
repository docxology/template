"""Git index guards for tracked projects and generated artifacts."""

from __future__ import annotations

import fnmatch
import subprocess
from pathlib import Path

from infrastructure.fonds.public_scope import PUBLIC_FOND_NAMES
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.rules.public_scope import PUBLIC_RULE_NAMES
from infrastructure.tools.public_scope import PUBLIC_TOOL_NAMES

# Derived from PUBLIC_PROJECT_NAMES — the single roster source of truth — so it
# can never drift from the public exemplar roster. (Before 2026-06-10 this was a
# hand-maintained literal.)
ALLOWED_PROJECT_DIRS: tuple[str, ...] = tuple(f"projects/{name}/" for name in PUBLIC_PROJECT_NAMES)

ALLOWED_FONDS_TOPLEVEL_FILES: frozenset[str] = frozenset(
    {
        "fonds/AGENTS.md",
        "fonds/README.md",
    }
)
ALLOWED_FOND_DIRS: tuple[str, ...] = tuple(f"fonds/{name}/" for name in PUBLIC_FOND_NAMES)

ALLOWED_RULES_TOPLEVEL_FILES: frozenset[str] = frozenset(
    {
        "rules/AGENTS.md",
        "rules/README.md",
    }
)
ALLOWED_RULE_DIRS: tuple[str, ...] = tuple(f"rules/{name}/" for name in PUBLIC_RULE_NAMES)

ALLOWED_TOOLS_TOPLEVEL_FILES: frozenset[str] = frozenset(
    {
        "tools/AGENTS.md",
        "tools/README.md",
    }
)
ALLOWED_TOOL_DIRS: tuple[str, ...] = tuple(f"tools/{name}/" for name in PUBLIC_TOOL_NAMES)

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
        "projects/templates/DESIGN.md",
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
        """Process match."""
        return path if path in ALLOWED_PROJECTS_TOPLEVEL_FILES else None


ALLOWED_PROJECTS_TOPLEVEL = _ExplicitToplevelAllowlist()

ALWAYS_GENERATED_ARTIFACT_PATTERNS: tuple[str, ...] = (
    ".codegraph",
    ".codegraph/*",
    ".leann",
    ".leann/*",
    ".omo",
    ".omo/*",
    ".coverage",
    ".coverage.*",
    ".DS_Store",
    "*/.codegraph",
    "*/.codegraph/*",
    "*/.leann",
    "*/.leann/*",
    "*/.omo",
    "*/.omo/*",
    "*/.DS_Store",
    "*.egg-info/*",
    "*/.egg-info/*",
    "coverage.json",
    "coverage*.xml",
    "coverage_project.json",
    "htmlcov/*",
)

GENERATED_OUTPUT_PATTERNS: tuple[str, ...] = (
    "output/*",
    "projects/*/output/*",
    "projects/*/*/output/*",
)

PUBLIC_TEMPLATE_OUTPUT_PREFIXES: tuple[str, ...] = tuple(
    prefix
    for name in PUBLIC_PROJECT_NAMES
    for prefix in (f"projects/{name}/output/", f"output/{name}/")
    if name.startswith("templates/")
)

PUBLIC_TEMPLATE_OUTPUT_MAX_BYTES = 50 * 1024 * 1024


def is_public_template_output_path(path: str) -> bool:
    """Check whether public template output path."""
    normalized = path.replace("\\", "/")
    return any(normalized.startswith(prefix) for prefix in PUBLIC_TEMPLATE_OUTPUT_PREFIXES)


def offending_tracked_projects(repo_root: Path) -> list[str]:
    """Return the list of offending tracked projects."""
    return _offending_tracked_paths(
        repo_root,
        path_prefix="projects/",
        allowed_toplevel=ALLOWED_PROJECTS_TOPLEVEL_FILES,
        allowed_dirs=ALLOWED_PROJECT_DIRS,
    )


def offending_tracked_fonds(repo_root: Path) -> list[str]:
    """Return the list of offending tracked fonds."""
    return _offending_tracked_paths(
        repo_root,
        path_prefix="fonds/",
        allowed_toplevel=ALLOWED_FONDS_TOPLEVEL_FILES,
        allowed_dirs=ALLOWED_FOND_DIRS,
    )


def offending_tracked_rules(repo_root: Path) -> list[str]:
    """Return the list of offending tracked rules."""
    return _offending_tracked_paths(
        repo_root,
        path_prefix="rules/",
        allowed_toplevel=ALLOWED_RULES_TOPLEVEL_FILES,
        allowed_dirs=ALLOWED_RULE_DIRS,
    )


def offending_tracked_tools(repo_root: Path) -> list[str]:
    """Return the list of offending tracked tools."""
    return _offending_tracked_paths(
        repo_root,
        path_prefix="tools/",
        allowed_toplevel=ALLOWED_TOOLS_TOPLEVEL_FILES,
        allowed_dirs=ALLOWED_TOOL_DIRS,
    )


def _offending_tracked_paths(
    repo_root: Path,
    *,
    path_prefix: str,
    allowed_toplevel: frozenset[str],
    allowed_dirs: tuple[str, ...],
) -> list[str]:
    proc = subprocess.run(
        ["git", "ls-files", "-z", path_prefix],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    paths = [p for p in proc.stdout.decode("utf-8").split("\0") if p]
    offenders: list[str] = []
    for path in paths:
        normalized = path.replace("\\", "/")
        if normalized in allowed_toplevel:
            continue
        if any(normalized.startswith(prefix) for prefix in allowed_dirs):
            continue
        offenders.append(normalized)
    return sorted(offenders)


def is_generated_artifact_path(path: str) -> bool:
    """Check whether generated artifact path."""
    normalized = path.replace("\\", "/")
    if any(fnmatch.fnmatch(normalized, pattern) for pattern in ALWAYS_GENERATED_ARTIFACT_PATTERNS):
        return True
    if is_public_template_output_path(normalized):
        return False
    return any(fnmatch.fnmatch(normalized, pattern) for pattern in GENERATED_OUTPUT_PATTERNS)


def is_oversized_public_template_output(repo_root: Path, path: str) -> bool:
    """Check whether oversized public template output."""
    normalized = path.replace("\\", "/")
    if not is_public_template_output_path(normalized):
        return False
    try:
        return (repo_root / normalized).stat().st_size > PUBLIC_TEMPLATE_OUTPUT_MAX_BYTES
    except OSError:
        return False


def tracked_generated_artifacts(repo_root: Path) -> list[str]:
    """Return the set of tracked generated artifacts."""
    proc = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    paths = [p for p in proc.stdout.decode("utf-8").split("\0") if p]
    return sorted(
        path
        for path in paths
        if is_generated_artifact_path(path) or is_oversized_public_template_output(repo_root, path)
    )
