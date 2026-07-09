"""No-mocks tests for src/deck_audit.py."""

from __future__ import annotations

from deck_audit import audit_deck


def test_audit_deck_ok_when_tokens_resolve_and_no_cliche():
    raw = {"title": "{{NAME}}", "slides": [{"title": "S", "bullets": ["Clean prose."]}]}
    result = audit_deck("short", raw, {"NAME": "My Deck"})
    assert result.ok is True
    assert result.unresolved_error == ""
    assert result.cliche_hits is None
    assert result.resolved_texts["title"] == "My Deck"


def test_audit_deck_fails_on_unresolved_token():
    raw = {"title": "{{MISSING}}", "slides": []}
    result = audit_deck("short", raw, {})
    assert result.ok is False
    assert "MISSING" in result.unresolved_error
    assert result.cliche_hits is None


def test_audit_deck_fails_on_cliche():
    raw = {"title": "T", "slides": [{"title": "S", "bullets": ["We will disrupt everything."]}]}
    result = audit_deck("short", raw, {})
    assert result.ok is False
    assert result.unresolved_error == ""
    assert result.cliche_hits is not None
    assert any("disrupt" in hits for hits in result.cliche_hits.values())


def test_audit_deck_carries_the_length_through():
    result = audit_deck("medium", {"title": "T", "slides": []}, {})
    assert result.length == "medium"
