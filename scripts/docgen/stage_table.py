#!/usr/bin/env python3
"""Regenerate the canonical stage table in long-lived Markdown docs.

Stage NN. Thin orchestrator over
:mod:`infrastructure.documentation.stage_table`.

The single source of truth is ``infrastructure/core/pipeline/pipeline.yaml``.
This script renders a Markdown stage table from it and injects the result
between ``<!-- BEGIN:STAGE_TABLE -->`` / ``<!-- END:STAGE_TABLE -->``
markers in each target file.

Usage:
    uv run python scripts/docgen/stage_table.py            # preview only
    uv run python scripts/docgen/stage_table.py --write    # apply changes
    uv run python scripts/docgen/stage_table.py --write README.md

Exit codes:
    0: Success (always, in both preview and write modes)
    1: Failure (e.g. malformed pipeline.yaml or missing target file)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from infrastructure.core.logging.utils import (  # noqa: E402
    get_logger,
    log_header,
    log_success,
)
from infrastructure.documentation.stage_table import (  # noqa: E402
    DEFAULT_STAGE_TABLE_TARGETS,
    refresh_stage_tables,
)

logger = get_logger(__name__)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "targets",
        nargs="*",
        help="Markdown files to update (defaults to the canonical doc files).",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Apply changes. Without this flag, only a 'would-change' preview is printed.",
    )
    parser.add_argument(
        "--yaml",
        type=Path,
        default=None,
        help="Override path to pipeline.yaml (defaults to infrastructure/core/pipeline/pipeline.yaml).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    log_header("Generate Stage-Table Documentation", logger)

    repo_root = Path(__file__).resolve().parents[2]
    yaml_path = args.yaml or (repo_root / "infrastructure" / "core" / "pipeline" / "pipeline.yaml")
    targets: list[str | Path] = [Path(t) for t in (args.targets or DEFAULT_STAGE_TABLE_TARGETS)]

    try:
        result = refresh_stage_tables(
            repo_root,
            targets=targets,
            yaml_path=yaml_path,
            write=args.write,
        )
    except (FileNotFoundError, OSError, ValueError) as exc:
        logger.error("Stage-table generation failed: %s", exc)
        return 1

    verb = "Updated" if args.write else "Would update"
    log_success(f"{verb} {len(result.changed)}; up-to-date {len(result.unchanged)}", logger)
    for p in result.changed:
        logger.info(f"  CHANGE: {p.relative_to(repo_root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
