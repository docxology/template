"""Pure project-owned manuscript configuration markers and token inspection.

Shared by rendering and validation without importing rendering providers.
"""

from __future__ import annotations

import re
from pathlib import Path


GENERATED_ORDERING_MARKER = "# Generated manuscript ordering"
"""Marker a generator writes when it owns the injected manuscript ordering."""

PROJECT_RESOLVED_MARKER = "# Project-resolved config"
"""Explicit opt-in marker: this injected config is the project's own artifact."""

# ``{{UPPER_SNAKE}}`` is the canonical project hydration token, the same shape
# as :data:`infrastructure.rendering.manuscript_injection._TOKEN_RE`.
_CONFIG_TOKEN_RE = re.compile(r"\{\{([A-Z][A-Z0-9_]*)\}\}")

# A token inside a backtick code span is prose *about* the token syntax, not a
# hydration target — ``template_gold_refinement``'s config documents "Resolve
# `{{TOKEN}}` placeholders into output/manuscript/". Those spans are stripped
# before scanning so documenting the contract can never fail a render. Same
# rationale as ``manuscript_injection.EXCLUDED_DOC_FILENAMES`` for markdown.
_CODE_SPAN_RE = re.compile(r"`[^`\n]*`")


def has_generated_manuscript_ordering(config_path: Path) -> bool:
    """Return True when an injected config owns generated manuscript ordering."""
    if not config_path.is_file():
        return False
    return GENERATED_ORDERING_MARKER in config_path.read_text(encoding="utf-8")


def unresolved_config_tokens(config_path: Path) -> list[str]:
    """Return the sorted unique ``{{UPPER_SNAKE}}`` tokens still present in *config_path*.

    Backtick code spans are stripped first (see :data:`_CODE_SPAN_RE`), so a
    config that *documents* the token syntax reports no unresolved tokens.
    """
    if not config_path.is_file():
        return []
    text = _CODE_SPAN_RE.sub("", config_path.read_text(encoding="utf-8"))
    return sorted({match.group(1) for match in _CONFIG_TOKEN_RE.finditer(text)})


def is_project_resolved(config_path: Path, source_config_path: Path | None = None) -> bool:
    """Return whether the injected ``config.yaml`` is a project-owned artifact.

    A project generator may substitute ``{{TOKEN}}`` values into
    ``output/manuscript/config.yaml``; that resolved file is authoritative and
    must not be clobbered by the tracked source template. Three branches claim
    ownership:

    1. :data:`GENERATED_ORDERING_MARKER` — the original marker behaviour,
       unchanged;
    2. :data:`PROJECT_RESOLVED_MARKER` — an explicit opt-in for generators that
       do not reorder the manuscript;
    3. inference — the tracked source still carries hydration tokens that the
       injected copy has resolved.

    Branch 3 is deliberately narrow: it fires only when the source itself is a
    token template, so a project that merely hand-edits its injected config
    still receives the source refresh it has always received.
    """
    if not config_path.is_file():
        return False
    text = config_path.read_text(encoding="utf-8")
    if GENERATED_ORDERING_MARKER in text or PROJECT_RESOLVED_MARKER in text:
        return True
    if source_config_path is None:
        return False
    source_tokens = set(unresolved_config_tokens(source_config_path))
    if not source_tokens:
        return False
    return bool(source_tokens - set(unresolved_config_tokens(config_path)))
