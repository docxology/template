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
    "templates/template_advanced_literature_review",
    "templates/template_autoresearch_project",
    "templates/template_autopoiesis",
    "templates/template_code_project",
    "templates/template_data_descriptor",
    "templates/template_eda_notebook",
    "templates/template_experiment_tree",
    "templates/template_formal",
    "templates/template_literature_meta_analysis",
    "templates/template_madlib",
    "templates/template_newspaper",
    "templates/template_pools_rules_tools",
    "templates/template_prose_project",
    "templates/template_autoscientists",
    "templates/template_gold_refinement",
    "templates/template_methods_paper",
    "templates/template_redacted_report",
    "templates/template_registered_report",
    "templates/template_search_project",
    "templates/template_sia",
    "templates/template_storybook",
    "templates/template_template",
    "templates/template_textbook",
    "templates/template_pitch_deck",
)

# Template exemplars that exist on disk under projects/templates/ but are NOT
# part of the public CI/publication scope. Empty: all on-disk exemplars are now
# public (tracked and CI-gated; publication requires its own receipts). Re-populate only if a new
# exemplar is staged locally before it is promoted to PUBLIC_PROJECT_NAMES.
LOCAL_ONLY_TEMPLATE_NAMES: tuple[str, ...] = ()

# Local-only template exemplars: see docs/maintenance/local-only-template-exemplars.md


def public_project_source_roots(repo_root: Path | str) -> tuple[Path, ...]:
    """Admit the complete canonical public source roster without discovery.

    This path admission does not inspect local lifecycle trees or establish
    executed-code custody. Acceptance workers independently audit consumed code.
    Missing, linked or wrong-origin canonical roots fail before path insertion.
    """
    root = Path(repo_root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("public source admission requires a repository directory")
    sources = []
    for name in PUBLIC_PROJECT_NAMES:
        source = root / "projects" / name / "src"
        try:
            resolved = source.resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise ValueError(f"canonical public source root is unavailable: {name}") from exc
        if source.is_symlink() or resolved != source or not source.is_dir():
            raise ValueError(f"canonical public source root must be an unlinked directory: {name}")
        if source in sources:
            raise ValueError("canonical public source roster contains a duplicate")
        sources.append(source)
    return tuple(sources)


def public_project_infos(repo_root: Path | str) -> list[ProjectInfo]:
    """Return discovered projects that are part of the public template repo."""
    root = Path(repo_root)
    allowed = set(PUBLIC_PROJECT_NAMES)
    return [project for project in discover_projects(root) if project.qualified_name in allowed]


def public_project_names(repo_root: Path | str) -> list[str]:
    """Return public template project names present in this checkout."""
    return sorted(project.qualified_name for project in public_project_infos(repo_root))


def public_ci_source_paths(repo_root: Path | str) -> list[Path]:
    """Return source paths for public CI type checks.

    Paths are repo-relative and cover reusable infrastructure, root pipeline
    scripts, and public exemplar ``src/`` trees. Local-only symlinked projects
    under ``projects/`` remain excluded.
    """
    root = Path(repo_root)
    paths = [Path("infrastructure"), Path("scripts")]
    for name in PUBLIC_PROJECT_NAMES:
        src = root / "projects" / name / "src"
        if src.is_dir():
            paths.append(Path("projects") / name / "src")
    return paths


def public_ci_lint_paths(repo_root: Path | str) -> list[Path]:
    """Return every public Python/notebook tree that Ruff must check.

    Type checking intentionally stays source-only because each standalone
    exemplar owns its own import root. Linting has no such package-collision
    constraint, so it also covers infrastructure tests plus every public
    exemplar's scripts, tests, and notebooks. Private lifecycle trees and
    generated ``output/`` content remain outside the public gate.
    """
    root = Path(repo_root)
    paths = [Path("conftest.py"), Path("docs"), Path("infrastructure"), Path("scripts"), Path("tests")]
    for name in PUBLIC_PROJECT_NAMES:
        project = root / "projects" / name
        for subdir_name in ("src", "scripts", "tests", "notebooks"):
            if (project / subdir_name).exists():
                paths.append(Path("projects") / name / subdir_name)
    return paths


def _format_paths(paths: Sequence[Path]) -> str:
    return " ".join(path.as_posix() for path in paths)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI for shelling the public scope into CI and hooks."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("lint-paths", "source-paths", "ci-paths", "project-names", "project-names-json"),
        help="Value to print; ci-paths emits lint_paths and source_paths key=value lines for CI outputs.",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        type=Path,
        help="Repository root. Defaults to the current directory.",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    if args.command == "ci-paths":
        # Compute both scopes before publishing either output. The helpers
        # remain the same source of truth used by health and project commands.
        lint_paths = _format_paths(public_ci_lint_paths(repo_root))
        source_paths = _format_paths(public_ci_source_paths(repo_root))
        print(f"lint_paths={lint_paths}\nsource_paths={source_paths}")
    elif args.command == "lint-paths":
        print(_format_paths(public_ci_lint_paths(repo_root)))
    elif args.command == "source-paths":
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
    "public_ci_lint_paths",
    "public_ci_source_paths",
    "public_project_infos",
    "public_project_names",
    "public_project_source_roots",
]
