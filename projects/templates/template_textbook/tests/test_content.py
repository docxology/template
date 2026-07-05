"""Tests for the chapter scaffolder and structural validator."""

from __future__ import annotations

from textbook.config import ChapterRef, UnitIntroRef
from textbook import content
from textbook.constants import REQUIRED_SECTION_HEADINGS, REQUIRED_TOKENS


def _chapter(stem: str = "first_principles") -> ChapterRef:
    return ChapterRef(
        part_id="part_I",
        part_label="I",
        part_title="Fundamentals",
        directory="part_I",
        file=f"{stem}.md",
        title="First Principles",
        enabled=True,
    )


def test_scaffolded_chapter_passes_validation():
    text = content.scaffold_chapter(_chapter())
    assert content.validate_chapter(text) == []
    for token in REQUIRED_TOKENS:
        assert token in text
    for heading in REQUIRED_SECTION_HEADINGS:
        assert f"## {heading}" in text


def test_scaffolded_chapter_has_stub_markers_and_words():
    text = content.scaffold_chapter(_chapter())
    assert content.count_stub_markers(text) > 0
    assert content.count_words(text) > 50


def test_scaffold_varies_by_stem_but_stays_valid():
    a = content.scaffold_chapter(_chapter("alpha"))
    b = content.scaffold_chapter(_chapter("omega"))
    # Deterministic rotation should make the glossary/citation selection differ.
    assert a != b
    assert content.validate_chapter(a) == []
    assert content.validate_chapter(b) == []


def test_scaffolded_lab_and_questions_link_back():
    ch = _chapter()
    lab = content.scaffold_lab(ch)
    questions = content.scaffold_question_bank(ch)
    assert "sec:lab_part_I_first_principles" in lab
    assert "sec:part_I_first_principles" in lab  # links to parent chapter
    assert "sec:q_part_I_first_principles" in questions
    assert content.count_stub_markers(lab) > 0
    assert content.count_stub_markers(questions) > 0


def test_validate_chapter_flags_missing_pieces():
    issues = content.validate_chapter("just some text without structure")
    joined = " ".join(issues)
    assert "missing H1 title" in joined
    assert "missing required token" in joined
    assert "missing required section" in joined
    assert "citation" in joined
    assert "glossary" in joined


def test_validate_chapter_detects_missing_single_section():
    text = content.scaffold_chapter(_chapter())
    broken = text.replace("## Summary", "## Recap")
    issues = content.validate_chapter(broken)
    assert any("Summary" in i for i in issues)


def test_count_words_and_stub_markers_basics():
    assert content.count_words("one two three") == 3
    assert content.count_stub_markers("TODO: a <!-- STUB --> b TKTK") == 3


def test_rotate_with_empty_items():
    """_rotate with an empty tuple must return [] without raising."""
    # Call via the internal helper through scaffold — the empty-items path
    # can be exercised directly since _rotate is module-level.
    from textbook.content import _rotate

    assert _rotate((), "any_seed", 3) == []
    assert _rotate((), "", 0) == []


def test_validate_chapter_flags_bad_figure_path():
    """validate_chapter must detect a figure path that won't resolve correctly."""
    good_text = content.scaffold_chapter(_chapter())
    # Inject a figure reference using the old (wrong) relative path form.
    bad_text = good_text + "\n![alt](../figures/bad_path.png){#fig:extra}\n"
    issues = content.validate_chapter(bad_text)
    assert any("figures" in i for i in issues)


def test_validate_chapter_accepts_correct_figure_path():
    """A figure path starting with '../../output/figures/' must not raise an issue."""
    good_text = content.scaffold_chapter(_chapter())
    # The scaffolded chapter always uses the correct path prefix.
    issues = content.validate_chapter(good_text)
    figure_path_issues = [i for i in issues if "figures" in i.lower()]
    assert figure_path_issues == []


def _intro() -> UnitIntroRef:
    return UnitIntroRef(
        part_id="part_I",
        part_label="I",
        part_title="Fundamentals",
        directory="part_I",
        file="unit_intro.md",
    )


def test_scaffolded_unit_intro_passes_validation():
    text = content.scaffold_unit_intro(_intro(), [_chapter()])
    assert content.validate_unit_intro(text) == []
    assert "sec:part_I_intro" in text
    assert content.count_stub_markers(text) > 0


def test_validate_unit_intro_requires_heading_and_cross_refs():
    issues = content.validate_unit_intro("plain text")
    joined = " ".join(issues)
    assert "missing H1 title" in joined
    assert "cross-reference" in joined
