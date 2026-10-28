#!/usr/bin/env python3
"""Refresh rendered provenance receipts for already-green project outputs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from infrastructure.core.pipeline.artifacts import (  # noqa: E402
    output_inventory_mode_for_project,
    snapshot_current_artifact_manifest,
)
from infrastructure.core.project_paths import resolve_project_root  # noqa: E402
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES  # noqa: E402
from infrastructure.rendering.pipeline import execute_render_pipeline  # noqa: E402
from infrastructure.validation.output.pipeline import execute_validation_pipeline  # noqa: E402
from infrastructure.validation.publication.rendered_provenance import (  # noqa: E402
    RenderedProvenanceError,
    write_rendered_provenance_receipt,
)


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
        help="Refresh every canonical public exemplar.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=repo_root,
        help="Repository root (default: parent of scripts/).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Rerender, snapshot, validate, and then write selected receipts."""
    args = _parse_args(argv)
    root = args.repo_root.resolve()
    names = list(PUBLIC_PROJECT_NAMES if args.all_public else args.projects)
    failed = False
    for name in names:
        project_root = resolve_project_root(root, name)
        old_manifest = project_root / "output" / "reports" / "artifact_manifest.json"
        old_paths: set[str] = set()
        try:
            old_payload = json.loads(old_manifest.read_text(encoding="utf-8"))
            old_paths = {
                str(row["path"])
                for row in old_payload.get("entries", [])
                if isinstance(row, dict) and isinstance(row.get("path"), str)
            }
        except (FileNotFoundError, OSError, json.JSONDecodeError, TypeError):
            pass
        if execute_render_pipeline(name, repo_root=root) != 0:
            print(f"FAIL {name} [RENDER_FAILED]: canonical Stage 3 render failed", file=sys.stderr)
            failed = True
            continue
        try:
            manifest = snapshot_current_artifact_manifest(
                project_root / "output",
                inventory_mode=output_inventory_mode_for_project(root, project_root),
            )
            if execute_validation_pipeline(name, repo_root=root) != 0:
                print(f"FAIL {name} [VALIDATION_FAILED]: canonical Stage 4 validation failed", file=sys.stderr)
                failed = True
                continue
            receipt = write_rendered_provenance_receipt(root, name)
        except (OSError, ValueError, RenderedProvenanceError) as exc:
            code = exc.code if isinstance(exc, RenderedProvenanceError) else "IO_ERROR"
            print(f"FAIL {name} [{code}]: {exc}", file=sys.stderr)
            failed = True
            continue
        new_paths = {entry.path for entry in manifest.entries}
        print(
            f"PASS {name}: "
            f"{receipt.source.file_count} source, "
            f"{receipt.config.file_count} config, "
            f"{receipt.output.file_count} output files; "
            f"manifest +{len(new_paths - old_paths)}/-{len(old_paths - new_paths)}"
        )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
