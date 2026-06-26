"""Public-repository project scope helpers.

Runtime project discovery intentionally includes local symlinked workspaces so
``run.sh`` can operate on private active projects. Public CI and generated docs
must stay narrower: only the tracked exemplar projects are part of the
public template repository.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from infrastructure.project.discovery import discover_projects
from infrastructure.project.project_info import ProjectInfo

PUBLIC_PROJECT_NAMES: tuple[str, ...] = (
    "templates/template_active_inference",
    "templates/template_autoresearch_project",
    "templates/template_code_project",
    "templates/template_literature_meta_analysis",
    "templates/template_madlib",
    "templates/template_newspaper",
    "templates/template_prose_project",
    "templates/template_autoscientists",
    "templates/template_gold_refinement",
    "templates/template_sia",
    "templates/template_template",
    "templates/template_textbook",
)

# Template exemplars that exist on disk under projects/templates/ but are NOT
# part of the public CI/publication scope. Empty: all on-disk exemplars are now
# fully public (tracked, CI-gated, double-published). Re-populate only if a new
# exemplar is staged locally before it is promoted to PUBLIC_PROJECT_NAMES.
LOCAL_ONLY_TEMPLATE_NAMES: tuple[str, ...] = ()

# Local-only template exemplars: see docs/maintenance/local-only-template-exemplars.md


def public_project_infos(repo_root: Path | str) -> list[ProjectInfo]:
    """Return discovered projects that are part of the public template repo."""
    root = Path(repo_root)
    allowed = set(PUBLIC_PROJECT_NAMES)
    return [project for project in discover_projects(root) if project.qualified_name in allowed]


def public_project_names(repo_root: Path | str) -> list[str]:
    """Return public template project names present in this checkout."""
    return sorted(project.qualified_name for project in public_project_infos(repo_root))


def public_ci_source_paths(repo_root: Path | str) -> list[Path]:
    """Return source paths for public CI lint/type checks.

    Paths are repo-relative and intentionally exclude local-only symlinked
    projects under ``projects/``.
    """
    root = Path(repo_root)
    paths = [Path("infrastructure")]
    for name in PUBLIC_PROJECT_NAMES:
        src = root / "projects" / name / "src"
        if src.is_dir():
            paths.append(Path("projects") / name / "src")
    return paths


def _format_paths(paths: Sequence[Path]) -> str:
    return " ".join(path.as_posix() for path in paths)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI for shelling the public scope into CI and hooks."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("source-paths", "project-names", "project-names-json"),
        help="Value to print for shell consumption.",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        type=Path,
        help="Repository root. Defaults to the current directory.",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    if args.command == "source-paths":
        print(_format_paths(public_ci_source_paths(repo_root)))
    elif args.command == "project-names-json":
        # Compact JSON array consumed by the CI test-project matrix via
        # ``fromJSON(needs.detect-projects.outputs.projects)``. ``separators``
        # keeps it on one line so it slots cleanly into ``$GITHUB_OUTPUT``.
        print(json.dumps(public_project_names(repo_root), separators=(",", ":")))
    else:
        print(" ".join(public_project_names(repo_root)))
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised via CLI tests
    raise SystemExit(main())


__all__ = [
    "LOCAL_ONLY_TEMPLATE_NAMES",
    "PUBLIC_PROJECT_NAMES",
    "main",
    "public_ci_source_paths",
    "public_project_infos",
    "public_project_names",
]
