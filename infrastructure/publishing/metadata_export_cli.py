"""CLI entry point for metadata export files derived from project config."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

from infrastructure.core.config.loader import load_config
from infrastructure.core.project_paths import find_repo_root
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
        help="Project name under projects/ (optionally typed-subfolder-qualified, e.g. working/<name>).",
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
        dict(config),
        out_dir,
        released_date=_stable_released_date(out_dir),
    )
    for path in written:
        print(path)
    return 0


_RELEASED_DATE_RE = re.compile(r"^date-released:\s*'?(\d{4}-\d{2}-\d{2})'?\s*$", re.MULTILINE)


def _stable_released_date(out_dir: Path) -> str:
    """Return the already-published release date, or today for a first export.

    No exemplar pins a release date in ``config.yaml``, so stamping
    ``date.today()`` on every run made ``date-released`` mean "whenever someone
    last regenerated" rather than when the work was released — it rewrote the
    field on each export and churned three tracked sidecars with it. Preserving
    the committed date makes regeneration idempotent, which a CI-gated generated
    file has to be, and keeps the value agreeing with the Zenodo deposit.

    A genuine re-release should move the date by updating the deposit and
    editing ``CITATION.cff`` deliberately, not as a side effect of regenerating.
    """
    existing = out_dir / "CITATION.cff"
    if existing.is_file():
        match = _RELEASED_DATE_RE.search(existing.read_text(encoding="utf-8"))
        if match:
            return match.group(1)
    return date.today().isoformat()


def _resolve_repo_root(repo_root: Path | None) -> Path:
    if repo_root is not None:
        return repo_root.resolve()
    derived = find_repo_root()
    if not (derived / "projects").is_dir():
        raise ValueError(f"Could not determine repo root from {__file__}")
    return derived


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
