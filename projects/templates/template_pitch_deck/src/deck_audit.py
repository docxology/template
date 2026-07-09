"""Shared token-resolution + cliche-lint audit, used by both the standalone
audit script (``scripts/10_audit_deck_content.py``) and the render script
(``scripts/20_render_decks.py``) so the two never drift out of sync."""

from __future__ import annotations

from dataclasses import dataclass

from cliche_lint import lint_deck_texts
from content_loader import raw_deck_texts
from token_resolution import UnresolvedTokenError, resolve_deck_tokens


@dataclass(frozen=True)
class AuditResult:
    length: str
    ok: bool
    unresolved_error: str = ""
    cliche_hits: dict[str, list[str]] | None = None
    resolved_texts: dict[str, str] | None = None


def audit_deck(length: str, raw: dict, tokens: dict[str, str]) -> AuditResult:
    """Run token resolution then cliche linting over one deck's raw content."""
    texts = raw_deck_texts(raw)
    try:
        resolved = resolve_deck_tokens(texts, tokens)
    except UnresolvedTokenError as exc:
        return AuditResult(length=length, ok=False, unresolved_error=str(exc))

    hits = lint_deck_texts(resolved)
    if hits:
        return AuditResult(length=length, ok=False, cliche_hits=hits, resolved_texts=resolved)

    return AuditResult(length=length, ok=True, resolved_texts=resolved)


__all__ = ["AuditResult", "audit_deck"]
