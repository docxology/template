#!/usr/bin/env python3
"""Parse coverage report text and manuscript Table 9-style module rows."""

from __future__ import annotations

import re
from pathlib import Path

_ROW_RE = re.compile(
    r"^\s*(?P<path>\S+\.py)\s+(?P<stmts>\d+)\s+\d+\s+(?P<cover>\d+)%",
    re.MULTILINE,
)
_TABLE_ROW_RE = re.compile(
    r"^\|\s*`(?P<module>[^`]+)`\s*\|\s*(?P<stmts>\d+)\s*\|\s*(?P<cover>\d+)%",
    re.MULTILINE,
)


def _file_to_module(path: str) -> str:
    if not path.endswith(".py"):
        return ""
    rel = path.replace("/", ".").removesuffix(".py")
    return rel


def _parse_coverage_report(text: str) -> dict[str, tuple[int, int]]:
    out: dict[str, tuple[int, int]] = {}
    for match in _ROW_RE.finditer(text):
        module = _file_to_module(match.group("path"))
        if not module:
            continue
        out[module] = (int(match.group("stmts")), int(match.group("cover")))
    return out


def _parse_table(md_path: Path) -> list[tuple[str, int, int]]:
    text = md_path.read_text(encoding="utf-8")
    rows: list[tuple[str, int, int]] = []
    for match in _TABLE_ROW_RE.finditer(text):
        rows.append(
            (
                match.group("module"),
                int(match.group("stmts")),
                int(match.group("cover")),
            )
        )
    return rows
