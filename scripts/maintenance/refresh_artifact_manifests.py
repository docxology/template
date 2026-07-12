#!/usr/bin/env python3
"""Refresh integrity-only artifact manifests for existing project outputs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from infrastructure.core.pipeline.artifacts import (  # noqa: E402
    snapshot_current_artifact_manifest,
    validate_artifact_manifest,
)
from infrastructure.core.project_paths import resolve_project_root  # noqa: E402
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES  # noqa: E402


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument(
        "--project",
        action="append",
        dest="projects",
        metavar="QUALIFIED_NAME",
        help="Project to refresh; repeat for multiple projects.",
    )
    selection.add_argument(
        "--all-public",
        action="store_true",
        help="Refresh every project in infrastructure.project.public_scope.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=repo_root,
        help="Repository root (default: parent of scripts/).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Refresh selected manifests and fail when an output tree is invalid."""
    args = _parse_args(argv)
    root = args.repo_root.resolve()
    names = list(PUBLIC_PROJECT_NAMES if args.all_public else args.projects)
    failed = False

    for name in names:
        project_dir = resolve_project_root(root, name)
        output_dir = project_dir / "output"
        if not output_dir.is_dir():
            print(f"FAIL {name}: missing output directory: {output_dir}", file=sys.stderr)
            failed = True
            continue

        manifest = snapshot_current_artifact_manifest(output_dir)
        validation = validate_artifact_manifest(manifest, project_dir=project_dir)
        if validation.valid:
            print(f"PASS {name}: {len(manifest.entries)} stable artifacts")
            continue

        failed = True
        print(f"FAIL {name}: {len(validation.issues)} issue(s)", file=sys.stderr)
        for issue in validation.issues:
            print(f"  - {issue}", file=sys.stderr)

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
