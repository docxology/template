#!/usr/bin/env python3
"""Emit JSON manuscript statistics — thin orchestrator."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

PROJECT_DIR = Path(os.environ.get("PROJECT_DIR", Path(__file__).resolve().parent.parent))
REPO_ROOT = PROJECT_DIR.parent.parent
SRC_DIR = PROJECT_DIR / "src"
for path_str in (str(REPO_ROOT), str(SRC_DIR)):
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from infrastructure.core.logging_utils import get_logger
from newspaper.sections import all_tracked_manuscript_basenames

logger = get_logger(__name__)

_WORD_RE = re.compile(r"\S+")


def _stats_for_file(path: Path) -> dict[str, int | str]:
    text = path.read_text(encoding="utf-8")
    lines = text.count("\n") + (0 if text.endswith("\n") else 1)
    if not text:
        lines = 0
    words = len(_WORD_RE.findall(text))
    return {
        "path": str(path.relative_to(PROJECT_DIR)),
        "lines": lines,
        "words": words,
        "bytes": path.stat().st_size,
    }


def main() -> None:
    """Write ``output/data/manuscript_stats.json`` and print its path."""
    manuscript_dir = PROJECT_DIR / "manuscript"
    out_dir = PROJECT_DIR / "output" / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "manuscript_stats.json"

    entries: list[dict[str, int | str]] = []
    for name in all_tracked_manuscript_basenames():
        fp = manuscript_dir / name
        if not fp.is_file():
            logger.warning("Skipping missing manuscript file: %s", name)
            continue
        st = _stats_for_file(fp)
        entries.append(st)
        logger.info("%s: %s words, %s lines", name, st["words"], st["lines"])

    payload = {"project": PROJECT_DIR.name, "files": entries}
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.info("Wrote %s", out_path)
    print(out_path.resolve())


if __name__ == "__main__":
    main()
