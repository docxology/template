#!/usr/bin/env python3
"""Stage-02 preflight: confirm the newspaper can be built before doing work.

Checks that the rendering dependencies import, that the content directory and
edition manifest exist, and that the manifest parses into an :class:`Edition`.
Exits non-zero with a precise message on the first failure so the pipeline stops
early rather than producing a broken PDF.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _bootstrap import get_logger, project_root, setup_paths  # noqa: E402

setup_paths()
logger = get_logger("newspaper.preflight")


def main() -> int:
    root = project_root()
    try:
        import PIL  # noqa: F401
        import reportlab  # noqa: F401
        import yaml  # noqa: F401
    except Exception as exc:  # pragma: no cover - environment failure
        logger.error("Missing rendering dependency: %s", exc)
        return 1

    content_dir = root / "content"
    manifest = content_dir / "edition.yaml"
    if not manifest.exists():
        logger.error("Edition manifest not found: %s", manifest)
        return 1

    try:
        from newspaper.config import load_newspaper_config
        from newspaper.content import load_edition

        edition = load_edition(content_dir)
        load_newspaper_config(content_dir)
    except Exception as exc:
        logger.error("Edition failed to load/validate: %s", exc)
        return 1

    logger.info(
        "Preflight OK — '%s', %d pages, dated %s.",
        edition.nameplate,
        edition.page_count,
        edition.date,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
