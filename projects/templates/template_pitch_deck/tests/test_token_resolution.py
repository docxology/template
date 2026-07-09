"""No-mocks tests for src/token_resolution.py."""

from __future__ import annotations

import pytest

from token_resolution import UnresolvedTokenError, find_tokens, resolve_deck_tokens, resolve_tokens


def test_find_tokens_extracts_uppercase_names():
    assert find_tokens("Hello {{NAME}}, you have {{COUNT}} items.") == {"NAME", "COUNT"}


def test_find_tokens_ignores_lowercase_braces():
    assert find_tokens("This {{not_a_token}} is skipped, but {{VALID}} matches.") == {"VALID"}


def test_resolve_tokens_substitutes_all_values():
    resolved = resolve_tokens("Hello {{NAME}}, you have {{COUNT}} items.", {"NAME": "Ada", "COUNT": "3"})
    assert resolved == "Hello Ada, you have 3 items."


def test_resolve_tokens_leaves_no_literal_braces():
    resolved = resolve_tokens("{{A}}{{B}}", {"A": "x", "B": "y"})
    assert "{{" not in resolved


def test_resolve_tokens_raises_if_a_tokens_own_value_contains_braces():
    """A token whose value itself contains '{{' must not ship a literal brace
    pair — this is unreachable via the missing-token path (the token IS
    resolved), so it needs its own real (non-`assert`) guard."""
    with pytest.raises(UnresolvedTokenError):
        resolve_tokens("{{A}}", {"A": "oops {{B}} leaked"})


def test_resolve_tokens_raises_on_missing_token():
    """Proof-of-detection: deliberately omit a required token and confirm it raises."""
    with pytest.raises(UnresolvedTokenError) as exc_info:
        resolve_tokens("Hello {{MISSING}}.", {"OTHER": "value"})
    assert "MISSING" in str(exc_info.value)


def test_resolve_tokens_no_tokens_present_is_a_noop():
    assert resolve_tokens("Plain text, no tokens.", {}) == "Plain text, no tokens."


def test_resolve_deck_tokens_resolves_a_mapping():
    texts = {"title": "{{TITLE}}", "body": "{{BODY}}"}
    resolved = resolve_deck_tokens(texts, {"TITLE": "My Deck", "BODY": "Some content"})
    assert resolved == {"title": "My Deck", "body": "Some content"}


def test_resolve_deck_tokens_raises_if_any_field_has_missing_token():
    texts = {"ok": "{{PRESENT}}", "broken": "{{ABSENT}}"}
    with pytest.raises(UnresolvedTokenError):
        resolve_deck_tokens(texts, {"PRESENT": "value"})
