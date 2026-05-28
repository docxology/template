"""Public-repository project scope helpers.

Runtime project discovery intentionally includes local symlinked workspaces so
``run.sh`` can operate on private active projects. Public CI and generated docs
must stay narrower: only the tracked exemplar projects are part of the
public template repository.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from infrastructure.project.discovery import discover_projects
from infrastructure.project.project_info import ProjectInfo

PUBLIC_PROJECT_NAMES: tuple[str, ...] = (
    "templates/template_active_inference",
    "templates/template_autoresearch_project",
    "templates/template_code_project",
    "templates/template_prose_project",
    "templates/template_template",
)


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
        choices=("source-paths", "project-names"),
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
    else:
        print(" ".join(public_project_names(repo_root)))
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised via CLI tests
    raise SystemExit(main())


__all__ = [
    "PUBLIC_PROJECT_NAMES",
    "main",
    "public_ci_source_paths",
    "public_project_infos",
    "public_project_names",
]
