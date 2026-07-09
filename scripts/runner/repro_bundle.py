#!/usr/bin/env python3
"""Repro-bundle stage orchestrator (REPRO-BUNDLE-1 — thin wrapper).

All logic lives in :mod:`infrastructure.publishing.repro_bundle`; this script
only wires the repository root onto ``sys.path`` and forwards CLI arguments.

Usage::

    uv run python scripts/runner/repro_bundle.py build <project> [--out dir]
    uv run python scripts/runner/repro_bundle.py verify <manifest>
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts import ensure_repo_root_on_path  # noqa: E402

ensure_repo_root_on_path()

from infrastructure.publishing.repro_bundle import main as _main  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    """Forward to the module CLI."""
    return _main(argv)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
