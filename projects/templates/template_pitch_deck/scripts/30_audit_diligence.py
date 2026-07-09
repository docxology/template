#!/usr/bin/env python3
"""Stage-02 analysis: diligence audit — every fact-bearing slide must cite its source.

Runs after content/token audit and rendering (lexicographically last) so a
missing citation is caught even if token resolution and cliche linting both
passed. Exits non-zero if any slide referencing a live-sourced fact token
(PITCH_SUBJECT_*/EXEMPLAR_*) has no `source` field.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _bootstrap import get_logger, project_root, setup_paths  # noqa: E402

setup_paths()
logger = get_logger("pitch_deck.diligence")

DECK_LENGTHS = ("short", "medium", "long")


def main(argv: list[str] | None = None) -> int:
    from content_loader import load_deck_yaml
    from diligence_audit import diligence_rows, uncited_fact_slides
    from paths import locate_repo_root

    root = project_root()
    repo_root = locate_repo_root(root)
    manuscript_dir = root / "manuscript"

    had_gap = False
    for length in DECK_LENGTHS:
        content_path = manuscript_dir / f"deck_content_{length}.yaml"
        raw = load_deck_yaml(content_path)
        rows = diligence_rows(raw, repo_root)
        n_needs = sum(1 for r in rows if r["needs_citation"])
        n_cited = sum(1 for r in rows if r["needs_citation"] and r["has_citation"])

        gaps = uncited_fact_slides(raw, repo_root)
        if gaps:
            had_gap = True
            for gap in gaps:
                logger.error("[%s] slide %d (%r) cites a fact but has no `source`", length, gap["index"], gap["title"])
        logger.info("[%s] diligence coverage: %d/%d fact-bearing slides cited", length, n_cited, n_needs)

    if had_gap:
        logger.error("Diligence audit FAILED — see above.")
        return 1

    logger.info("Diligence audit passed for all lengths: %s", ", ".join(DECK_LENGTHS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
