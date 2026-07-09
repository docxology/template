"""No-mocks tests for src/standalone_slides.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.rendering.slide_deck import DeckContent, Slide

from standalone_slides import (
    attach_qr_urls,
    standalone_slide_markdown,
    standalone_slide_relpath,
    write_standalone_slides,
)


def test_standalone_slide_relpath_is_deterministic_and_zero_padded():
    path = standalone_slide_relpath("template_template", "short", 3)
    assert path == "projects/templates/template_pitch_deck/output/slides_standalone/template_template_short/slide_03.md"


def test_standalone_slide_relpath_differs_by_length_and_index():
    a = standalone_slide_relpath("template_template", "short", 1)
    b = standalone_slide_relpath("template_template", "medium", 1)
    c = standalone_slide_relpath("template_template", "short", 2)
    assert len({a, b, c}) == 3


def test_standalone_slide_markdown_content_slide_includes_bullets_and_source():
    slide = Slide(title="A Title", bullets=("point one", "point two"), source="path/to/file.py")
    md = standalone_slide_markdown(
        slide,
        index=2,
        total=5,
        length="short",
        pitch_subject="template_template",
        source_base_url="https://github.com/org/repo/blob/main/",
    )
    assert "# A Title" in md
    assert "Slide 2 of 5" in md
    assert "point one" in md
    assert "point two" in md
    assert "[path/to/file.py](https://github.com/org/repo/blob/main/path/to/file.py)" in md
    assert "PDF" in md and "PPTX" in md


def test_standalone_slide_markdown_stat_slide_shows_value_and_label():
    slide = Slide(title="Proof", kind="stat", stat_value="89 tests", stat_label="91% coverage")
    md = standalone_slide_markdown(
        slide, index=1, total=1, length="short", pitch_subject="x", source_base_url=""
    )
    assert "89 tests" in md
    assert "91% coverage" in md


def test_standalone_slide_markdown_quote_slide_shows_quote_and_attribution():
    slide = Slide(title="", kind="quote", quote_text="A real quote.", quote_attribution="Someone")
    md = standalone_slide_markdown(
        slide, index=1, total=1, length="short", pitch_subject="x", source_base_url=""
    )
    assert "A real quote." in md
    assert "Someone" in md


def test_standalone_slide_markdown_without_source_omits_source_line():
    slide = Slide(title="No source", bullets=("x",))
    md = standalone_slide_markdown(
        slide, index=1, total=1, length="short", pitch_subject="x", source_base_url=""
    )
    assert "**Source:**" not in md


def test_write_standalone_slides_writes_one_real_file_per_slide(tmp_path: Path):
    deck = DeckContent(
        title="Deck",
        slides=(
            Slide(title="One", bullets=("a",)),
            Slide(title="Two", bullets=("b",)),
        ),
    )
    written = write_standalone_slides(
        deck,
        length="short",
        pitch_subject="template_template",
        project_root=tmp_path,
        source_base_url="",
    )
    assert len(written) == 2
    for path in written:
        assert path.is_file()
    assert (
        tmp_path / "output" / "slides_standalone" / "template_template_short" / "slide_01.md"
    ).is_file()
    assert (
        tmp_path / "output" / "slides_standalone" / "template_template_short" / "slide_02.md"
    ).is_file()


def test_attach_qr_urls_sets_deterministic_url_per_slide():
    deck = DeckContent(title="Deck", slides=(Slide(title="One"), Slide(title="Two")))
    updated = attach_qr_urls(
        deck, length="short", pitch_subject="template_template", source_base_url="https://github.com/org/repo/blob/main/"
    )
    assert updated.slides[0].qr_url == (
        "https://github.com/org/repo/blob/main/"
        "projects/templates/template_pitch_deck/output/slides_standalone/template_template_short/slide_01.md"
    )
    assert updated.slides[1].qr_url.endswith("slide_02.md")
    assert updated.slides[0].qr_url != updated.slides[1].qr_url


def test_attach_qr_urls_is_pure_original_deck_unmodified():
    deck = DeckContent(title="Deck", slides=(Slide(title="One"),))
    attach_qr_urls(deck, length="short", pitch_subject="x", source_base_url="https://example.org/")
    assert deck.slides[0].qr_url == ""


def test_attach_qr_urls_noop_without_source_base_url():
    deck = DeckContent(title="Deck", slides=(Slide(title="One"),))
    updated = attach_qr_urls(deck, length="short", pitch_subject="x", source_base_url="")
    assert updated is deck
    assert updated.slides[0].qr_url == ""


def test_attach_qr_urls_preserves_other_slide_fields():
    deck = DeckContent(title="Deck", slides=(Slide(title="One", bullets=("a", "b"), source="f.py"),))
    updated = attach_qr_urls(deck, length="short", pitch_subject="x", source_base_url="https://example.org/")
    assert updated.slides[0].title == "One"
    assert updated.slides[0].bullets == ("a", "b")
    assert updated.slides[0].source == "f.py"


def test_standalone_slide_relpath_rejects_path_traversal_pitch_subject():
    """Real reproduction of the red-team-flagged path-traversal risk."""
    with pytest.raises(ValueError):
        standalone_slide_relpath("../../../../../../tmp/pwned", "short", 1)


def test_standalone_slide_relpath_rejects_path_traversal_length():
    with pytest.raises(ValueError):
        standalone_slide_relpath("template_template", "../../tmp/pwned", 1)


def test_write_standalone_slides_rejects_path_traversal(tmp_path: Path):
    deck = DeckContent(title="Deck", slides=(Slide(title="One"),))
    with pytest.raises(ValueError):
        write_standalone_slides(
            deck,
            length="short",
            pitch_subject="../../../../../../tmp/pwned",
            project_root=tmp_path,
            source_base_url="",
        )
    # Nothing must be written outside tmp_path as a side effect of the attempt.
    assert not (tmp_path.parent / "pwned_short").exists()


def test_write_standalone_slides_clears_stale_files_on_shrinking_rerender(tmp_path: Path):
    """Real reproduction of the red-team-flagged stale-output bug: a deck
    that shrinks between regenerations must not leave orphaned slide_NN.md
    files from the previous, larger run."""
    big_deck = DeckContent(
        title="Deck",
        slides=(Slide(title="One", bullets=("a",)), Slide(title="Two", bullets=("b",)), Slide(title="Three", bullets=("c",))),
    )
    write_standalone_slides(
        big_deck, length="short", pitch_subject="template_template", project_root=tmp_path, source_base_url=""
    )
    standalone_dir = tmp_path / "output" / "slides_standalone" / "template_template_short"
    assert len(list(standalone_dir.glob("slide_*.md"))) == 3

    small_deck = DeckContent(title="Deck", slides=(Slide(title="One", bullets=("a",)),))
    write_standalone_slides(
        small_deck, length="short", pitch_subject="template_template", project_root=tmp_path, source_base_url=""
    )
    remaining = sorted(p.name for p in standalone_dir.glob("slide_*.md"))
    assert remaining == ["slide_01.md"]
