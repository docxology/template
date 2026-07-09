"""``{{TOKEN}}`` resolution for deck content.

Mirrors the convention used by
``infrastructure/rendering/manuscript_injection.py`` (``\\{\\{[A-Z][A-Z0-9_]*\\}\\}``),
scoped here to deck-content strings instead of ``manuscript/*.md``. Unlike
that module — which logs unresolved tokens as warnings and leaves them
literal in output — ``resolve_tokens`` raises immediately on any unresolved
token, because deck content is a small, fully-authored surface where a
missing token is always an authoring bug, never an expected partial-render
state.
"""

from __future__ import annotations

import re

TOKEN_RE = re.compile(r"\{\{([A-Z][A-Z0-9_]*)\}\}")


class UnresolvedTokenError(ValueError):
    """Raised when ``resolve_tokens`` finds a token with no matching value."""

    def __init__(self, tokens: tuple[str, ...]):
        self.tokens = tokens
        super().__init__(f"Unresolved token(s): {', '.join(tokens)}")


def find_tokens(text: str) -> set[str]:
    """Return the set of ``{{TOKEN}}`` names referenced in ``text``."""
    return set(TOKEN_RE.findall(text))


def resolve_tokens(text: str, tokens: dict[str, str]) -> str:
    """Substitute every ``{{TOKEN}}`` in ``text`` with ``tokens[TOKEN]``.

    Raises:
        UnresolvedTokenError: if any referenced token has no entry in
            ``tokens``. Never returns text containing a literal ``{{``.
    """
    referenced = find_tokens(text)
    missing = tuple(sorted(referenced - tokens.keys()))
    if missing:
        raise UnresolvedTokenError(missing)

    def _substitute(match: re.Match[str]) -> str:
        return tokens[match.group(1)]

    resolved = TOKEN_RE.sub(_substitute, text)
    if "{{" in resolved:
        # Not reachable via the missing-token path above (every referenced
        # token was resolved) — this only fires if a token's own *value*
        # happens to contain "{{", which would otherwise ship a literal
        # brace pair silently. A real exception (not `assert`, which
        # `python -O` strips) so this can never be optimized away.
        raise UnresolvedTokenError(("<token value itself contains '{{'>",))
    return resolved


def resolve_deck_tokens(texts: dict[str, str], tokens: dict[str, str]) -> dict[str, str]:
    """Resolve tokens across a ``{slide_field_id: text}`` mapping in one pass."""
    return {key: resolve_tokens(value, tokens) for key, value in texts.items()}


__all__ = ["TOKEN_RE", "UnresolvedTokenError", "find_tokens", "resolve_tokens", "resolve_deck_tokens"]
