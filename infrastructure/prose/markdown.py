"""Markdown front-matter / fence-stripping helpers.

Prose analysers operate on plain text. The functions here strip
front-matter (YAML/TOML) and fenced code blocks so the metrics reflect
prose, not embedded code or metadata.
"""

from __future__ import annotations

import re
from pathlib import Path

_FRONT_MATTER_RE = re.compile(r"^\s*---\s*\n.*?\n\s*---\s*\n", re.DOTALL)
_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
_LINK_RE = re.compile(r"\[([^\]]+)\]\([^\)]+\)")
_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\([^\)]+\)")


def strip_front_matter(text: str) -> str:
    """Remove a leading YAML front-matter block, if any."""
    return _FRONT_MATTER_RE.sub("", text, count=1)


def strip_fences(text: str) -> str:
    """Remove fenced code blocks (``` ... ```)."""
    return _FENCE_RE.sub("", text)


def strip_inline_code(text: str) -> str:
    """Remove inline code spans (`...`)."""
    return _INLINE_CODE_RE.sub("", text)


def strip_links_to_text(text: str) -> str:
    """Replace ``[label](url)`` with ``label`` and drop ``![alt](url)``."""
    text = _IMAGE_RE.sub("", text)
    text = _LINK_RE.sub(r"\1", text)
    return text


def normalise_for_prose(text: str) -> str:
    """Apply all stripping passes in canonical order."""
    out = strip_front_matter(text)
    out = strip_fences(out)
    out = strip_inline_code(out)
    out = strip_links_to_text(out)
    return out


def read_manuscript_dir(
    manuscript_dir: Path | str,
    *,
    include: str = "*.md",
    exclude_filenames: tuple[str, ...] = (
        "preamble.md",
        "config.yaml.example",
        "AGENTS.md",
        "README.md",
        "SYNTAX.md",
    ),
) -> dict[str, str]:
    """Read every Markdown file in *manuscript_dir* into a ``{name: text}`` map.

    Files whose name appears in *exclude_filenames* are skipped (their
    content is documentation/scaffolding, not prose worth analysing).
    """
    base = Path(manuscript_dir)
    out: dict[str, str] = {}
    for path in sorted(base.glob(include)):
        if path.name in exclude_filenames:
            continue
        out[path.name] = path.read_text(encoding="utf-8")
    return out
