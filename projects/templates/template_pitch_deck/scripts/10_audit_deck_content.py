#!/usr/bin/env python3
"""Stage-02 analysis: audit deck content for unresolved tokens and cliche.

Runs before rendering (lexicographically before ``20_render_decks.py``) so a
broken content source fails the pipeline loudly instead of shipping a PDF/PPTX
with a literal ``{{TOKEN}}`` or a stock pitch-deck phrase. Exits non-zero on
either failure class; prints a per-length, per-check summary to stdout.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _bootstrap import get_logger, project_root, setup_paths  # noqa: E402

setup_paths()
logger = get_logger("pitch_deck.audit")

DECK_LENGTHS = ("short", "medium", "long")


def main(argv: list[str] | None = None) -> int:
    from content_loader import load_deck_yaml
    from deck_audit import audit_deck
    from deck_tokens import build_deck_tokens
    from paths import locate_repo_root

    root = project_root()
    repo_root = locate_repo_root(root)
    manuscript_dir = root / "manuscript"

    tokens = build_deck_tokens(repo_root)

    had_failure = False
    for length in DECK_LENGTHS:
        content_path = manuscript_dir / f"deck_content_{length}.yaml"
        if not content_path.is_file():
            logger.error("Missing deck content file: %s", content_path)
            had_failure = True
            continue

        raw = load_deck_yaml(content_path)
        result = audit_deck(length, raw, tokens)

        if result.unresolved_error:
            logger.error("[%s] token resolution FAILED: %s", length, result.unresolved_error)
            had_failure = True
            continue

        if result.cliche_hits:
            logger.error("[%s] cliche lint FAILED: %s", length, result.cliche_hits)
            had_failure = True
            continue

        logger.info("[%s] audit OK (%d text fields, 0 cliche hits)", length, len(result.resolved_texts or {}))

    if had_failure:
        logger.error("Deck content audit FAILED — see above.")
        return 1

    logger.info("Deck content audit passed for all lengths: %s", ", ".join(DECK_LENGTHS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
