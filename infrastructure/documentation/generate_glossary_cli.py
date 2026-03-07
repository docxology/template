#!/usr/bin/env python3
"""Glossary generation script for building API index from source code.

This module provides functionality to automatically generate a glossary of
public APIs from the src/ directory and inject it into markdown files.
"""

from __future__ import annotations

import sys
from pathlib import Path

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


def _repo_root() -> Path:
    return Path(__file__).parent.parent


def _ensure_glossary_file(path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# API Symbols Glossary\n\n"
        "This glossary is auto-generated from the public API in `src/`.\n\n"
        "<!-- BEGIN: AUTO-API-GLOSSARY -->\n"
        "No public APIs detected in `src/`.\n"
        "<!-- END: AUTO-API-GLOSSARY -->\n",
        encoding="utf-8",
    )


def main() -> int:
    """Main function to generate and update the API glossary.

    Returns:
        0 on success, 1 on failure
    """
    args = sys.argv[1:]
    if len(args) >= 2:
        src_dir = Path(args[0])
        glossary_md = Path(args[1])
        repo = src_dir.parent.parent
    else:
        repo = _repo_root()
        project_dir = repo / "project"
        src_dir = project_dir / "src"
        glossary_md = project_dir / "manuscript" / "98_symbols_glossary.md"

    _ensure_glossary_file(glossary_md)

    sys.path.insert(0, str(repo))
    try:
        from infrastructure.documentation.glossary_gen import (
            build_api_index,
            generate_markdown_table,
            inject_between_markers,
        )
    except Exception as exc:
        logger.error("Failed to import glossary_gen from infrastructure/documentation/: %s", exc)
        return 1

    text = glossary_md.read_text(encoding="utf-8")

    entries = build_api_index(str(src_dir))
    table = generate_markdown_table(entries)
    begin = "<!-- BEGIN: AUTO-API-GLOSSARY -->"
    end = "<!-- END: AUTO-API-GLOSSARY -->"
    new_text = inject_between_markers(text, begin, end, table)

    if new_text != text:
        glossary_md.write_text(new_text, encoding="utf-8")
        logger.info("Updated glossary: %s", glossary_md)
    else:
        logger.info("Glossary up-to-date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
