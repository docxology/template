"""Real-render tests for infrastructure.rendering.pptx_deck (no mocks).

Skips cleanly if the opt-in `rendering-pptx` dependency group
(`uv sync --group rendering-pptx`) is not installed, matching the pattern the
rest of the repo uses for optional-dependency modules (e.g. discopy tests).
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("pptx", reason="python-pptx opt-in group not installed (uv sync --group rendering-pptx)")

from pptx import Presentation  # noqa: E402

from infrastructure.core.exceptions import RenderingError  # noqa: E402
from infrastructure.rendering.pptx_deck import _fit_single_line_font_size_pt, render_pptx  # noqa: E402
from infrastructure.rendering.slide_deck import CONTENT_HEADER_FONT_SIZE, DeckContent, DeckTheme, Slide, render_pdf  # noqa: E402


def _make_deck(n_slides: int) -> DeckContent:
    slides = tuple(
        Slide(title=f"Slide {i}", bullets=(f"Point {i}.a", f"Point {i}.b"), kind="content") for i in range(n_slides)
    )
    return DeckContent(title="Test Deck", subtitle="A subtitle", slides=slides)


def test_render_pptx_rejects_empty_deck(tmp_path: Path):
    empty_deck = DeckContent(title="Empty")
    with pytest.raises(RenderingError):
        render_pptx(empty_deck, tmp_path / "empty.pptx")


def test_render_pptx_produces_real_file_with_expected_slide_count(tmp_path: Path):
    deck = _make_deck(4)
    output = render_pptx(deck, tmp_path / "deck.pptx")

    assert output.is_file()
    assert output.stat().st_size > 1000

    prs = Presentation(str(output))
    assert len(prs.slides._sldIdLst) == 4 + 1  # synthesized title + 4 content slides


def test_render_pptx_slide_count_matches_render_pdf_page_count(tmp_path: Path):
    from pypdf import PdfReader

    deck = _make_deck(6)
    pdf_path = render_pdf(deck, tmp_path / "deck.pdf")
    pptx_path = render_pptx(deck, tmp_path / "deck.pptx")

    pdf_page_count = len(PdfReader(str(pdf_path)).pages)
    prs = Presentation(str(pptx_path))
    pptx_slide_count = len(prs.slides._sldIdLst)

    assert pdf_page_count == pptx_slide_count


def test_render_pptx_text_contains_slide_titles_and_bullets(tmp_path: Path):
    deck = _make_deck(2)
    output = render_pptx(deck, tmp_path / "deck_text.pptx")

    prs = Presentation(str(output))
    all_text = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                all_text.append(shape.text_frame.text)
    joined = "\n".join(all_text)

    assert "Slide 0" in joined
    assert "Slide 1" in joined
    assert "Point 0.a" in joined


def test_render_pptx_no_synthesized_title_slide_when_first_slide_is_title(tmp_path: Path):
    slides = (
        Slide(title="Deck Title", kind="title"),
        Slide(title="Content", bullets=("a", "b")),
    )
    deck = DeckContent(title="Deck Title", slides=slides)
    output = render_pptx(deck, tmp_path / "deck_with_title_slide.pptx")

    prs = Presentation(str(output))
    assert len(prs.slides._sldIdLst) == 2


def test_render_pptx_notes_are_attached(tmp_path: Path):
    slides = (Slide(title="Deck Title", kind="title", notes="Speaker note here"),)
    deck = DeckContent(title="Deck Title", slides=slides)
    output = render_pptx(deck, tmp_path / "deck_notes.pptx")

    prs = Presentation(str(output))
    slide = next(iter(prs.slides))
    assert "Speaker note here" in slide.notes_slide.notes_text_frame.text


def test_render_pptx_figure_is_embedded(tmp_path: Path):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig_path = tmp_path / "fig.png"
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    fig.savefig(fig_path)
    plt.close(fig)

    slides = (Slide(title="With figure", bullets=("a",), figure_path=fig_path),)
    deck = DeckContent(title="Deck", slides=slides)
    output = render_pptx(deck, tmp_path / "deck_with_figure.pptx")

    prs = Presentation(str(output))
    slide = list(prs.slides)[-1]
    picture_shapes = [s for s in slide.shapes if s.shape_type == 13]  # MSO_SHAPE_TYPE.PICTURE == 13
    assert len(picture_shapes) == 1


def test_render_pptx_stat_slide_shows_value_and_label(tmp_path: Path):
    deck = DeckContent(
        title="Deck",
        slides=(Slide(title="Proof", kind="stat", stat_value="89 tests", stat_label="91% coverage"),),
    )
    output = render_pptx(deck, tmp_path / "stat_deck.pptx")

    prs = Presentation(str(output))
    texts = [shape.text_frame.text for slide in prs.slides for shape in slide.shapes if shape.has_text_frame]
    joined = "\n".join(texts)
    assert "89 tests" in joined
    assert "91% coverage" in joined


def test_render_pptx_quote_slide_shows_quote_and_attribution(tmp_path: Path):
    deck = DeckContent(
        title="Deck",
        slides=(Slide(title="", kind="quote", quote_text="A real quote.", quote_attribution="Some Source"),),
    )
    output = render_pptx(deck, tmp_path / "quote_deck.pptx")

    prs = Presentation(str(output))
    texts = [shape.text_frame.text for slide in prs.slides for shape in slide.shapes if shape.has_text_frame]
    joined = "\n".join(texts)
    assert "A real quote." in joined
    assert "Some Source" in joined


def test_render_pptx_diagram_slide_embeds_figure(tmp_path: Path):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig_path = tmp_path / "fig.png"
    fig, ax = plt.subplots()
    ax.plot([0, 1], [1, 0])
    fig.savefig(fig_path)
    plt.close(fig)

    deck = DeckContent(title="Deck", slides=(Slide(title="Architecture", kind="diagram", figure_path=fig_path),))
    output = render_pptx(deck, tmp_path / "diagram_deck.pptx")

    prs = Presentation(str(output))
    slide = list(prs.slides)[-1]
    picture_shapes = [s for s in slide.shapes if s.shape_type == 13]
    assert len(picture_shapes) == 1


def test_render_pptx_source_citation_becomes_clickable_link(tmp_path: Path):
    deck = DeckContent(title="Deck", slides=(Slide(title="Fact slide", bullets=("x",), source="CLAUDE.md"),))
    output = render_pptx(
        deck, tmp_path / "cited_deck.pptx", source_base_url="https://github.com/org/repo/blob/main/"
    )

    prs = Presentation(str(output))
    content_slide = list(prs.slides)[-1]  # slide 0 is the synthesized title slide
    found_hyperlink = None
    found_text = False
    for shape in content_slide.shapes:
        if not shape.has_text_frame:
            continue
        for para in shape.text_frame.paragraphs:
            for run in para.runs:
                if "Source: CLAUDE.md" in run.text:
                    found_text = True
                if run.hyperlink.address:
                    found_hyperlink = run.hyperlink.address

    assert found_text
    assert found_hyperlink == "https://github.com/org/repo/blob/main/CLAUDE.md"


def test_render_pptx_custom_theme_changes_output(tmp_path: Path):
    """Different themes must actually change the rendered artifact (not a no-op parameter)."""
    deck = DeckContent(title="Deck", slides=(Slide(title="Title", kind="title"),))
    default_output = render_pptx(deck, tmp_path / "default_theme.pptx")
    custom_theme = DeckTheme(
        black="#123456", white="#FFFFFF", highlight_1="#ABCDEF", highlight_2="#ABCDEF", highlight_3="#ABCDEF"
    )
    custom_output = render_pptx(deck, tmp_path / "custom_theme.pptx", theme=custom_theme)
    assert default_output.read_bytes() != custom_output.read_bytes()


def test_render_pptx_empty_title_does_not_crash(tmp_path: Path):
    """Regression test: python-pptx leaves a paragraph with zero runs when
    text is set to "", so a naive `.text = title` + `runs[0]` access used to
    raise IndexError on any empty-string title (title/section/content/diagram
    slide kinds all accept one)."""
    deck = DeckContent(title="", slides=(Slide(title="", kind="title"), Slide(title="", bullets=("x",))))
    output = render_pptx(deck, tmp_path / "empty_title.pptx")
    assert output.is_file()


def test_render_pptx_missing_figure_warns_and_renders_without_it(tmp_path: Path, caplog):
    missing_path = tmp_path / "does_not_exist.png"
    deck = DeckContent(title="Deck", slides=(Slide(title="Content", bullets=("x",), figure_path=missing_path),))
    with caplog.at_level("WARNING"):
        output = render_pptx(deck, tmp_path / "missing_figure.pptx")
    assert output.is_file()
    assert any("does not exist" in record.message for record in caplog.records)


def test_render_pptx_missing_figure_on_diagram_slide_warns_and_renders(tmp_path: Path, caplog):
    missing_path = tmp_path / "does_not_exist.png"
    deck = DeckContent(title="Deck", slides=(Slide(title="Diagram", kind="diagram", figure_path=missing_path),))
    with caplog.at_level("WARNING"):
        output = render_pptx(deck, tmp_path / "missing_diagram_figure.pptx")
    assert output.is_file()
    assert any("does not exist" in record.message for record in caplog.records)


def test_render_pptx_draws_clickable_qr_code_when_qr_url_set(tmp_path: Path):
    qr_target = "https://github.com/org/repo/blob/main/slide.md"
    deck = DeckContent(title="Deck", slides=(Slide(title="Fact slide", bullets=("x",), qr_url=qr_target),))
    output = render_pptx(deck, tmp_path / "qr_deck.pptx")

    prs = Presentation(str(output))
    content_slide = list(prs.slides)[-1]
    picture_shapes = [s for s in content_slide.shapes if s.shape_type == 13]
    assert len(picture_shapes) == 1
    assert picture_shapes[0].click_action.hyperlink.address == qr_target


def test_render_pptx_no_qr_picture_when_qr_url_absent(tmp_path: Path):
    deck = DeckContent(title="Deck", slides=(Slide(title="No QR", bullets=("x",)),))
    output = render_pptx(deck, tmp_path / "no_qr_deck.pptx")
    prs = Presentation(str(output))
    content_slide = list(prs.slides)[-1]
    picture_shapes = [s for s in content_slide.shapes if s.shape_type == 13]
    assert len(picture_shapes) == 0


def test_render_pptx_qr_and_figure_coexist_as_two_pictures(tmp_path: Path):
    """A diagram slide has its own figure picture; the QR must be a second,
    distinct picture shape, not clobber the figure."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig_path = tmp_path / "fig.png"
    fig, ax = plt.subplots()
    ax.plot([0, 1], [1, 0])
    fig.savefig(fig_path)
    plt.close(fig)

    deck = DeckContent(
        title="Deck",
        slides=(
            Slide(
                title="Diagram",
                kind="diagram",
                figure_path=fig_path,
                qr_url="https://github.com/org/repo/blob/main/slide.md",
            ),
        ),
    )
    output = render_pptx(deck, tmp_path / "diagram_with_qr.pptx")
    prs = Presentation(str(output))
    content_slide = list(prs.slides)[-1]
    picture_shapes = [s for s in content_slide.shapes if s.shape_type == 13]
    assert len(picture_shapes) == 2


def test_fit_single_line_font_size_pt_keeps_start_size_for_short_title():
    assert _fit_single_line_font_size_pt("Short", 8.9, CONTENT_HEADER_FONT_SIZE) == CONTENT_HEADER_FONT_SIZE


def test_fit_single_line_font_size_pt_shrinks_a_long_title_to_fit():
    long_title = "Why this is a science-integrity problem, not just a tooling problem"
    size = _fit_single_line_font_size_pt(long_title, 8.9, CONTENT_HEADER_FONT_SIZE)
    assert size < CONTENT_HEADER_FONT_SIZE


def test_fit_single_line_font_size_pt_never_shrinks_below_the_floor():
    absurdly_long = "A title so long it could never fit on one line no matter how small the font gets, by design"
    assert _fit_single_line_font_size_pt(absurdly_long, 1.0, CONTENT_HEADER_FONT_SIZE) == 14


def test_render_pptx_content_slide_with_long_title_does_not_crash(tmp_path: Path):
    long_title = "Why this is a science-integrity problem, not just a tooling problem"
    deck = DeckContent(title="Deck", slides=(Slide(title=long_title, bullets=("x",)),))
    output = render_pptx(deck, tmp_path / "long_title.pptx")
    assert output.is_file()
