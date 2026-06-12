#!/usr/bin/env python3
"""Guard against stale ``canonical_facts`` paths after the COUNTS.md rename."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

STALE_MARKERS = (
    "canonical_facts.md",
    "docs/_generated/canonical_facts",
)
SKIP_PARTS = (
    "docs/audit/archived/",
    ".git/",
    "node_modules/",
    ".venv/",
    "__pycache__/",
)


def find_stale_paths(repo_root: Path) -> list[tuple[Path, str]]:
    hits: list[tuple[Path, str]] = []
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(repo_root).as_posix()
        if any(skip in rel for skip in SKIP_PARTS):
            continue
        if path.name == "rename_counts_doc.py":
            continue
        if path.suffix not in {".md", ".py", ".json", ".yaml", ".yml", ".html", ".toml"}:
            if path.name not in {".cursorrules"}:
                continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue
        for marker in STALE_MARKERS:
            if marker in text:
                hits.append((path, marker))
                break
    return hits


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero when stale canonical_facts paths remain outside archived audits.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root (default: auto-detected).",
    )
    args = parser.parse_args(argv)
    hits = find_stale_paths(args.repo_root.resolve())
    if not hits:
        print("rename_counts_doc: no stale canonical_facts paths found.")
        return 0
    for path, marker in hits:
        print(f"{path}: contains stale marker {marker!r}")
    return 1 if args.check else 0


if __name__ == "__main__":
    raise SystemExit(main())
