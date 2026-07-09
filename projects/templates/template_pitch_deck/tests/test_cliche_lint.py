"""No-mocks tests for src/cliche_lint.py."""

from __future__ import annotations

from cliche_lint import DENYLIST, lint_deck_texts, lint_text


def test_denylist_has_at_least_fifteen_terms():
    assert len(DENYLIST) >= 15


def test_lint_text_detects_known_cliche():
    """Proof-of-detection: the lint DOES fire on a deliberately cliche sentence."""
    hits = lint_text("Our platform will disrupt the entire industry with 10x synergy.")
    assert "disrupt" in hits
    assert "10x" in hits
    assert "synergy" in hits


def test_lint_text_clean_sentence_has_no_hits():
    assert lint_text("The renderer produces six real, token-validated artifacts.") == []


def test_lint_text_word_boundary_avoids_false_positive_on_substring():
    """'classic' must not falsely match the denylisted phrase 'best-in-class'."""
    assert "best-in-class" not in lint_text("This is a classic design choice.")


def test_lint_text_word_boundary_still_matches_hyphenated_form():
    """'disruptive-looking' still matches 'disruptive' — hyphen is a word boundary."""
    assert "disruptive" in lint_text("We chose a disruptive-looking font for the cover.")


def test_lint_text_is_case_insensitive():
    assert "unicorn" in lint_text("We are the next UNICORN.")


def test_lint_deck_texts_returns_only_entries_with_hits():
    texts = {
        "clean": "This sentence is fine.",
        "dirty": "We will revolutionize the field with a paradigm shift.",
    }
    result = lint_deck_texts(texts)
    assert "clean" not in result
    assert "dirty" in result
    assert "revolutionize" in result["dirty"]
    assert "paradigm shift" in result["dirty"]


def test_lint_does_not_flag_necessary_domain_vocabulary():
    """The lint must not also flag this project's own required vocabulary."""
    domain_text = "This reproducible template infrastructure has strong test coverage."
    assert lint_text(domain_text) == []
