#!/usr/bin/env python3
"""Write ``docs/_generated/architecture_overview.{mmd,svg}`` from live state.

Thin orchestrator — all logic lives in
:mod:`infrastructure.documentation.architecture_overview`.

Run from repository root::

    uv run python scripts/docgen/architecture_overview.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from infrastructure.core.logging.utils import get_logger, log_header, log_success
from infrastructure.documentation.architecture_overview import render_architecture_svg

logger = get_logger(__name__)


def main() -> None:
    log_header("Generate Architecture Overview Diagram", logger)
    repo_root = Path(__file__).resolve().parents[1]
    out_dir = repo_root / "docs" / "_generated"
    out_dir.mkdir(parents=True, exist_ok=True)
    svg_path = out_dir / "architecture_overview.svg"

    rendered = render_architecture_svg(repo_root, svg_path)
    mmd_path = rendered.with_suffix(".mmd")

    print(str(mmd_path))
    print(str(rendered))
    log_success(f"Wrote {mmd_path} and {rendered}", logger)


if __name__ == "__main__":
    main()
