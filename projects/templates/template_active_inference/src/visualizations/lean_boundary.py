"""Parse Lean boundary modules into a status table for figures."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LeanBoundaryRow:
    module: str
    name: str
    kind: str
    status: str


_DECL_START_RE = re.compile(r"^\s*(?:def|theorem)\s+(\w+)", re.MULTILINE)
# A declaration is NOT cleanly proved if it leans on any of these: `sorry`/`admit`
# (placeholders), `sorryAx` (the compiled-term form), or `native_decide` (trusts the
# compiler via the `Lean.ofReduceBool` axiom). Plain `decide` is sound and stays
# "proved". A bare `\bsorry\b` regex missed admit/native_decide/sorryAx entirely.
_SORRY_RE = re.compile(r"\b(?:sorry|admit|sorryAx|native_decide)\b")


def _module_name(path: Path, lean_root: Path) -> str:
    rel = path.relative_to(lean_root).with_suffix("")
    parts = rel.parts
    if parts[-1] == parts[0]:
        return ".".join(parts)
    return ".".join(parts)


def _declaration_block(text: str, start: int) -> str:
    """Return the declaration body from ``start`` until the next top-level def/theorem."""
    tail = text[start:]
    next_match = _DECL_START_RE.search(tail, pos=1)
    if next_match is None:
        return tail
    return tail[: next_match.start()]


def _scan_lean_file(path: Path, lean_root: Path) -> list[LeanBoundaryRow]:
    text = path.read_text(encoding="utf-8")
    module = _module_name(path, lean_root)
    rows: list[LeanBoundaryRow] = []
    for match in _DECL_START_RE.finditer(text):
        name = match.group(1)
        block = _declaration_block(text, match.start())
        kind = "theorem" if match.group(0).lstrip().startswith("theorem") else "def"
        status = "sorry" if _SORRY_RE.search(block) else "proved"
        rows.append(LeanBoundaryRow(module=module, name=name, kind=kind, status=status))
    return rows


def load_lean_boundary_rows(project_root: Path) -> list[LeanBoundaryRow]:
    lean_root = project_root.resolve() / "lean"
    if not lean_root.is_dir():
        return []
    rows: list[LeanBoundaryRow] = []
    for path in sorted(lean_root.rglob("*.lean")):
        if path.name in {"lakefile.lean", "TemplateActiveInference.lean"}:
            continue
        if "TemplateActiveInference" not in path.parts:
            continue
        rows.extend(_scan_lean_file(path, lean_root))
    return rows
