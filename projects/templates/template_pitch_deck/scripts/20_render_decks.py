#!/usr/bin/env python3
"""Stage-02 analysis: render the six pitch-deck artifacts.

Thin wrapper around ``src/render_orchestration.py::render_all_decks`` — see
that module's docstring for the audit → resolve → budget-filter → render
pipeline it runs per deck length. PPTX rendering is skipped with a warning
(not a failure) when ``python-pptx`` is not installed — install it with
``uv sync --group rendering-pptx`` to get all six artifacts.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _bootstrap import get_logger, project_root, setup_paths  # noqa: E402

setup_paths()
logger = get_logger("pitch_deck.render")


def main(argv: list[str] | None = None) -> int:
    from paths import locate_repo_root
    from render_orchestration import DeckAuditFailure, DiligenceAuditFailure, render_all_decks

    from infrastructure.core.exceptions import RenderingError

    root = project_root()
    repo_root = locate_repo_root(root)

    try:
        written = render_all_decks(root, repo_root, logger)
    except (DeckAuditFailure, DiligenceAuditFailure, RenderingError) as exc:
        logger.error(str(exc))
        return 1

    for path in written:
        print(path)
    logger.info("Rendered %d deck artifact(s).", len(written))
    return 0


if __name__ == "__main__":
    sys.exit(main())
