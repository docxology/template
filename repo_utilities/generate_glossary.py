#!/usr/bin/env python3
"""Glossary generation script for building API index from source code.

This module provides functionality to automatically generate a glossary of
public APIs from the src/ directory and inject it into markdown files.
"""
from __future__ import annotations

import os
import sys
from typing import Tuple


def _repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _ensure_glossary_file(path: str) -> None:
    if os.path.exists(path):
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    skeleton = (
        "# API Symbols Glossary\n\n"
        "This glossary is auto-generated from the public API in `src/`.\n\n"
        "<!-- BEGIN: AUTO-API-GLOSSARY -->\n"
        "No public APIs detected in `src/`.\n"
        "<!-- END: AUTO-API-GLOSSARY -->\n"
    )
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(skeleton)


def main() -> int:
    """Main function to generate and update the API glossary.
    
    Returns:
        0 on success, 1 on failure
    """
    repo = _repo_root()
    project_dir = os.path.join(repo, "project")
    src_dir = os.path.join(project_dir, "src")
    # Write directly to project/manuscript/98_symbols_glossary.md
    glossary_md = os.path.join(project_dir, "manuscript", "98_symbols_glossary.md")

    # Ensure file exists with markers
    _ensure_glossary_file(glossary_md)

    sys.path.insert(0, src_dir)
    try:
        from infrastructure.glossary_gen import build_api_index, generate_markdown_table, inject_between_markers  # type: ignore
    except Exception as exc:
        print(f"Failed to import glossary_gen from src/: {exc}")
        return 1

    with open(glossary_md, "r", encoding="utf-8") as fh:
        text = fh.read()

    entries = build_api_index(src_dir)
    table = generate_markdown_table(entries)
    begin = "<!-- BEGIN: AUTO-API-GLOSSARY -->"
    end = "<!-- END: AUTO-API-GLOSSARY -->"
    new_text = inject_between_markers(text, begin, end, table)

    if new_text != text:
        with open(glossary_md, "w", encoding="utf-8") as fh:
            fh.write(new_text)
        print(f"Updated glossary: {glossary_md}")
    else:
        print("Glossary up-to-date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
