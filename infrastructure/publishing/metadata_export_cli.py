"""CLI entry point for metadata export files derived from project config."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from infrastructure.core.config.loader import load_config
from infrastructure.project.discovery import resolve_project_root
from infrastructure.publishing.metadata_export import write_metadata_files


def main(argv: list[str] | None = None) -> int:
    """Run the metadata export CLI.

    Args:
        argv: Optional CLI arguments. Defaults to ``sys.argv[1:]``.

    Returns:
        Process exit code.
    """
    parser = argparse.ArgumentParser(
        prog="python -m infrastructure.publishing.metadata_export_cli",
        description="Write CITATION.cff, codemeta.json, and .zenodo.json for a project.",
    )
    subparsers = parser.add_subparsers(dest="command")

    export_parser = subparsers.add_parser(
        "metadata-export",
        help="Export citation and archival metadata files from manuscript/config.yaml.",
    )
    export_parser.add_argument(
        "--project",
        required=True,
        help="Project name under projects/ or projects_in_progress/.",
    )
    export_parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output directory for the metadata files. Defaults to the project root.",
    )
    export_parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Optional repository root override.",
    )

    args = parser.parse_args(argv)
    if args.command != "metadata-export":
        parser.print_help()
        return 1

    repo_root = _resolve_repo_root(args.repo_root)
    project_root = resolve_project_root(repo_root, args.project)
    config_path = project_root / "manuscript" / "config.yaml"
    config = load_config(config_path)
    if config is None:
        print(f"Could not load config: {config_path}")
        return 1

    out_dir = args.out or project_root
    written = write_metadata_files(
        config,
        out_dir,
        released_date=date.today().isoformat(),
    )
    for path in written:
        print(path)
    return 0


def _resolve_repo_root(repo_root: Path | None) -> Path:
    if repo_root is not None:
        return repo_root.resolve()
    derived = Path(__file__).resolve().parents[2]
    if not (derived / "projects").is_dir():
        raise ValueError(f"Could not determine repo root from {__file__}")
    return derived


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
