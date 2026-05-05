#!/usr/bin/env python3
"""Regenerate ``docs/reference/api-reference.md`` from each package's ``__all__``.

Thin orchestrator over :mod:`infrastructure.documentation.api_reference_gen`.
The single source of truth is ``infrastructure/<pkg>/__init__.py`` —
this script renders a Markdown block from the union of those exports
and injects it between ``<!-- BEGIN:API_REFERENCE -->`` /
``<!-- END:API_REFERENCE -->`` markers in the target doc.

Usage::

    uv run python scripts/generate_api_reference_doc.py --check    # CI
    uv run python scripts/generate_api_reference_doc.py --write    # apply

Exit codes:
    0: Up-to-date (``--check``) or write succeeded (``--write``).
    1: Drift detected (``--check``) or target/path error.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from infrastructure.core.logging.utils import (  # noqa: E402
    get_logger,
    log_header,
    log_success,
)
from infrastructure.documentation.api_reference_gen import (  # noqa: E402
    build_api_reference_markdown,
    inject_api_reference,
)
from infrastructure.documentation.glossary_gen import inject_between_markers  # noqa: E402

logger = get_logger(__name__)


_DEFAULT_TARGET = Path("docs/reference/api-reference.md")


def _discover_packages(infra_dir: Path) -> list[Path]:
    """Return alphabetically-sorted package roots under ``infra_dir`` with __init__.py."""
    return sorted(
        (p.parent for p in infra_dir.glob("*/__init__.py") if not p.parent.name.startswith("_")),
        key=lambda p: p.name,
    )


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="Apply changes to the target file.")
    mode.add_argument(
        "--check",
        action="store_true",
        help="Compare with the on-disk target and exit non-zero on drift.",
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=_DEFAULT_TARGET,
        help=f"Markdown file to update (default: {_DEFAULT_TARGET}).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    log_header("Generate API-Reference Documentation", logger)

    repo_root = Path(__file__).resolve().parents[1]
    infra_dir = repo_root / "infrastructure"
    target = args.target if args.target.is_absolute() else repo_root / args.target
    if not target.exists():
        logger.error(f"Target not found: {target}")
        return 1

    packages = _discover_packages(infra_dir)
    content = build_api_reference_markdown(packages)

    if args.write:
        changed = inject_api_reference(target, content)
        log_success(
            f"Wrote {len(packages)} packages → {target.relative_to(repo_root)}"
            f" ({'changed' if changed else 'unchanged'})",
            logger,
        )
        return 0

    # --check (default behaviour): compare without writing.
    current = target.read_text(encoding="utf-8")
    new_text = inject_between_markers(
        current,
        "<!-- BEGIN:API_REFERENCE -->",
        "<!-- END:API_REFERENCE -->",
        content,
    )
    if new_text == current:
        log_success(f"API reference is up-to-date ({len(packages)} packages).", logger)
        return 0
    logger.error("API reference is stale. Run: uv run python scripts/generate_api_reference_doc.py --write")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
