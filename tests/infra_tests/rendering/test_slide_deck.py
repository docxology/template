"""Real-render tests for infrastructure.rendering.slide_deck (no mocks)."""

from __future__ import annotations

from pathlib import Path

import pytest
from pypdf import PdfReader

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering.slide_deck import (
    DEFAULT_THEME,
    CONTENT_HEADER_FONT_SIZE,
    MARGIN,
    PAGE_SIZE,
    DeckContent,
    DeckTheme,
    Slide,
    SlideBudget,
    _fit_single_line_font_size,
    filter_deck_for_budget,
    render_pdf,
    source_url,
)
from reportlab.pdfgen import canvas as rl_canvas


def _make_deck(n_slides: int) -> DeckContent:
    slides = tuple(
        Slide(title=f"Slide {i}", bullets=(f"Point {i}.a", f"Point {i}.b"), kind="content") for i in range(n_slides)
    )
    return DeckContent(title="Test Deck", subtitle="A subtitle", slides=slides)


def test_slide_defaults():
    slide = Slide(title="Only a title")
    assert slide.bullets == ()
    assert slide.kind == "content"
    assert slide.notes == ""
    assert slide.figure_path is None


def test_deck_sections_alias_matches_slides():
    deck = _make_deck(3)
    assert deck.sections == deck.slides
    assert len(deck.sections) == 3


def test_slide_budget_max_slides():
    assert SlideBudget.SHORT.max_slides == 11
    assert SlideBudget.MEDIUM.max_slides == 38
    assert SlideBudget.LONG.max_slides == 58


def test_filter_deck_for_budget_truncates():
    deck = _make_deck(30)
    short = filter_deck_for_budget(deck, SlideBudget.SHORT)
    assert len(short.slides) == 11
    assert short.slides[0].title == "Slide 0"
    assert short.title == deck.title
    assert short.subtitle == deck.subtitle


def test_filter_deck_for_budget_is_idempotent_and_pure():
    deck = _make_deck(45)
    first = filter_deck_for_budget(deck, SlideBudget.MEDIUM)
    second = filter_deck_for_budget(deck, SlideBudget.MEDIUM)
    assert first.slides == second.slides
    assert first.title == second.title
    assert len(first.slides) == 38
    # Original deck must be unmodified (purity).
    assert len(deck.slides) == 45


def test_filter_deck_for_budget_noop_when_under_budget():
    deck = _make_deck(5)
    filtered = filter_deck_for_budget(deck, SlideBudget.LONG)
    assert len(filtered.slides) == 5


def test_render_pdf_rejects_empty_deck(tmp_path: Path):
    empty_deck = DeckContent(title="Empty")
    with pytest.raises(RenderingError):
        render_pdf(empty_deck, tmp_path / "empty.pdf")


def test_render_pdf_produces_real_file_with_expected_page_count(tmp_path: Path):
    deck = _make_deck(4)
    output = render_pdf(deck, tmp_path / "deck.pdf")

    assert output.is_file()
    assert output.stat().st_size > 1000

    reader = PdfReader(str(output))
    # First authored slide isn't kind=="title" -> a synthesized title page is prepended.
    assert len(reader.pages) == 4 + 1


def test_render_pdf_no_synthesized_title_page_when_first_slide_is_title(tmp_path: Path):
    slides = (
        Slide(title="Deck Title", kind="title"),
        Slide(title="Content", bullets=("a", "b")),
    )
    deck = DeckContent(title="Deck Title", slides=slides)
    output = render_pdf(deck, tmp_path / "deck_with_title_slide.pdf")

    reader = PdfReader(str(output))
    assert len(reader.pages) == 2


def test_render_pdf_page_text_contains_slide_titles(tmp_path: Path):
    deck = _make_deck(2)
    output = render_pdf(deck, tmp_path / "deck_text.pdf")
    reader = PdfReader(str(output))
    full_text = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert "Slide 0" in full_text
    assert "Slide 1" in full_text
    assert "Point 0.a" in full_text


def test_render_pdf_section_slide_renders_without_bullets(tmp_path: Path):
    deck = DeckContent(
        title="Deck",
        slides=(
            Slide(title="Part One", kind="section"),
            Slide(title="Real content", bullets=("x",)),
        ),
    )
    output = render_pdf(deck, tmp_path / "section_deck.pdf")
    reader = PdfReader(str(output))
    assert len(reader.pages) == 2 + 1  # +1 synthesized title page
    full_text = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert "Part One" in full_text


def test_default_theme_is_black_white_plus_three_highlights():
    assert DEFAULT_THEME.black
    assert DEFAULT_THEME.white
    assert DEFAULT_THEME.highlight_1 and DEFAULT_THEME.highlight_2 and DEFAULT_THEME.highlight_3


def test_theme_color_properties_return_reportlab_colors():
    from reportlab.lib import colors

    theme = DeckTheme(black="#000000", white="#FFFFFF", highlight_1="#FF0000", highlight_2="#00FF00", highlight_3="#0000FF")
    assert theme.black_c == colors.HexColor("#000000")
    assert theme.highlight_2_c == colors.HexColor("#00FF00")


def test_source_url_none_when_no_source():
    assert source_url("", "https://github.com/org/repo/blob/main/") is None


def test_source_url_none_when_no_base_and_relative_source():
    assert source_url("CLAUDE.md", "") is None


def test_source_url_joins_relative_source_onto_base():
    url = source_url("CLAUDE.md", "https://github.com/org/repo/blob/main/")
    assert url == "https://github.com/org/repo/blob/main/CLAUDE.md"


def test_source_url_passes_through_absolute_url():
    absolute = "https://example.org/already/a/full/url.md"
    assert source_url(absolute, "https://github.com/org/repo/blob/main/") == absolute


def test_render_pdf_stat_slide_shows_value_and_label(tmp_path: Path):
    deck = DeckContent(
        title="Deck",
        slides=(Slide(title="Proof", kind="stat", stat_value="89 tests", stat_label="91% coverage"),),
    )
    output = render_pdf(deck, tmp_path / "stat_deck.pdf")
    reader = PdfReader(str(output))
    full_text = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert "89 tests" in full_text
    assert "91% coverage" in full_text


def test_render_pdf_quote_slide_shows_quote_and_attribution(tmp_path: Path):
    deck = DeckContent(
        title="Deck",
        slides=(Slide(title="", kind="quote", quote_text="A real quote.", quote_attribution="Some Source"),),
    )
    output = render_pdf(deck, tmp_path / "quote_deck.pdf")
    reader = PdfReader(str(output))
    full_text = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert "A real quote." in full_text
    assert "Some Source" in full_text


def test_render_pdf_diagram_slide_embeds_figure(tmp_path: Path):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig_path = tmp_path / "fig.png"
    fig, ax = plt.subplots()
    ax.plot([0, 1], [1, 0])
    fig.savefig(fig_path)
    plt.close(fig)

    deck = DeckContent(
        title="Deck", slides=(Slide(title="Architecture", kind="diagram", figure_path=fig_path),)
    )
    output = render_pdf(deck, tmp_path / "diagram_deck.pdf")
    reader = PdfReader(str(output))
    full_text = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert "Architecture" in full_text
    assert output.stat().st_size > 2000


def test_render_pdf_source_citation_becomes_clickable_link(tmp_path: Path):
    deck = DeckContent(
        title="Deck",
        slides=(Slide(title="Fact slide", bullets=("x",), source="CLAUDE.md"),),
    )
    output = render_pdf(deck, tmp_path / "cited_deck.pdf", source_base_url="https://github.com/org/repo/blob/main/")

    reader = PdfReader(str(output))
    content_page = reader.pages[1]  # page 0 is the synthesized title page
    full_text = content_page.extract_text() or ""
    assert "Source: CLAUDE.md" in full_text

    annots = content_page.get("/Annots")
    assert annots, "expected a clickable link annotation for the source citation"
    uris = [a.get_object().get("/A", {}).get("/URI") for a in annots]
    assert "https://github.com/org/repo/blob/main/CLAUDE.md" in uris


def test_render_pdf_no_footer_when_source_absent(tmp_path: Path):
    deck = DeckContent(title="Deck", slides=(Slide(title="No source", bullets=("x",)),))
    output = render_pdf(deck, tmp_path / "uncited_deck.pdf")
    reader = PdfReader(str(output))
    content_page = reader.pages[1]
    assert not content_page.get("/Annots")


def test_render_pdf_custom_theme_changes_output(tmp_path: Path):
    """Different themes must actually change the rendered artifact (not a no-op parameter)."""
    deck = DeckContent(title="Deck", slides=(Slide(title="Title", kind="title"),))
    default_output = render_pdf(deck, tmp_path / "default_theme.pdf")
    custom_theme = DeckTheme(black="#123456", white="#FFFFFF", highlight_1="#ABCDEF", highlight_2="#ABCDEF", highlight_3="#ABCDEF")
    custom_output = render_pdf(deck, tmp_path / "custom_theme.pdf", theme=custom_theme)
    assert default_output.read_bytes() != custom_output.read_bytes()


def test_render_pdf_empty_title_does_not_crash(tmp_path: Path):
    deck = DeckContent(title="", slides=(Slide(title="", kind="title"), Slide(title="", bullets=("x",))))
    output = render_pdf(deck, tmp_path / "empty_title.pdf")
    assert output.is_file()


def test_render_pdf_missing_figure_warns_and_renders_without_it(tmp_path: Path, caplog):
    missing_path = tmp_path / "does_not_exist.png"
    deck = DeckContent(title="Deck", slides=(Slide(title="Content", bullets=("x",), figure_path=missing_path),))
    with caplog.at_level("WARNING"):
        output = render_pdf(deck, tmp_path / "missing_figure.pdf")
    assert output.is_file()
    assert any("does not exist" in record.message for record in caplog.records)


def test_render_pdf_missing_figure_on_diagram_slide_warns_and_renders(tmp_path: Path, caplog):
    missing_path = tmp_path / "does_not_exist.png"
    deck = DeckContent(title="Deck", slides=(Slide(title="Diagram", kind="diagram", figure_path=missing_path),))
    with caplog.at_level("WARNING"):
        output = render_pdf(deck, tmp_path / "missing_diagram_figure.pdf")
    assert output.is_file()
    assert any("does not exist" in record.message for record in caplog.records)


def test_render_pdf_is_byte_identical_across_runs(tmp_path: Path):
    """Reproducibility is a core claim of this renderer's consumers (the
    pitch-deck project's own README). ReportLab stamps `/CreationDate` with
    wall-clock time by default, which would silently break "regenerate and
    diff" checks despite identical content — `invariant=1` fixes this."""
    import time

    deck = DeckContent(title="Deck", slides=(Slide(title="Content", bullets=("a", "b")),))
    first = render_pdf(deck, tmp_path / "first.pdf")
    first_bytes = first.read_bytes()
    time.sleep(1.1)  # ensure wall-clock second actually advances
    second = render_pdf(deck, tmp_path / "second.pdf")
    assert first_bytes == second.read_bytes()


def test_render_pdf_draws_clickable_qr_code_when_qr_url_set(tmp_path: Path):
    qr_target = "https://github.com/org/repo/blob/main/slide.md"
    deck = DeckContent(title="Deck", slides=(Slide(title="Fact slide", bullets=("x",), qr_url=qr_target),))
    output = render_pdf(deck, tmp_path / "qr_deck.pdf")

    reader = PdfReader(str(output))
    content_page = reader.pages[1]  # page 0 is the synthesized title page
    annots = content_page.get("/Annots")
    assert annots, "expected a clickable QR link annotation"
    uris = [a.get_object().get("/A", {}).get("/URI") for a in annots]
    assert qr_target in uris


def test_render_pdf_no_qr_annotation_when_qr_url_absent(tmp_path: Path):
    deck = DeckContent(title="Deck", slides=(Slide(title="No QR", bullets=("x",)),))
    output = render_pdf(deck, tmp_path / "no_qr_deck.pdf")
    reader = PdfReader(str(output))
    content_page = reader.pages[1]
    assert not content_page.get("/Annots")


def test_render_pdf_qr_and_source_annotations_coexist(tmp_path: Path):
    """The QR (bottom-right) and source citation (bottom-left) must not clobber each other."""
    deck = DeckContent(
        title="Deck",
        slides=(
            Slide(
                title="Fact slide",
                bullets=("x",),
                source="CLAUDE.md",
                qr_url="https://github.com/org/repo/blob/main/slide.md",
            ),
        ),
    )
    output = render_pdf(
        deck, tmp_path / "both_deck.pdf", source_base_url="https://github.com/org/repo/blob/main/"
    )
    reader = PdfReader(str(output))
    content_page = reader.pages[1]
    annots = content_page.get("/Annots")
    assert annots and len(annots) == 2
    uris = {a.get_object().get("/A", {}).get("/URI") for a in annots}
    assert uris == {
        "https://github.com/org/repo/blob/main/CLAUDE.md",
        "https://github.com/org/repo/blob/main/slide.md",
    }


def test_fit_single_line_font_size_keeps_start_size_for_short_title():
    c = rl_canvas.Canvas("__unused__.pdf", pagesize=PAGE_SIZE)
    size = _fit_single_line_font_size(c, "Short title", "Helvetica-Bold", 400, CONTENT_HEADER_FONT_SIZE)
    assert size == CONTENT_HEADER_FONT_SIZE


def test_fit_single_line_font_size_shrinks_a_long_title_to_fit(tmp_path: Path):
    """Real reproduction of the red-team-flagged clipping bug: a genuinely
    long title (the exact one that clipped in this deck's own long-form
    content) must shrink below the requested size to fit the available
    width, never silently overflow it."""
    c = rl_canvas.Canvas(str(tmp_path / "__unused__.pdf"), pagesize=PAGE_SIZE)
    long_title = "Why this is a science-integrity problem, not just a tooling problem"
    max_width = PAGE_SIZE[0] - 2 * MARGIN
    size = _fit_single_line_font_size(c, long_title, "Helvetica-Bold", max_width, CONTENT_HEADER_FONT_SIZE)
    assert size < CONTENT_HEADER_FONT_SIZE
    assert c.stringWidth(long_title, "Helvetica-Bold", size) <= max_width


def test_fit_single_line_font_size_never_shrinks_below_the_floor(tmp_path: Path):
    c = rl_canvas.Canvas(str(tmp_path / "__unused__.pdf"), pagesize=PAGE_SIZE)
    absurdly_long = "A title so long it could never fit on one line no matter how small the font gets, by design"
    size = _fit_single_line_font_size(c, absurdly_long, "Helvetica-Bold", 100, CONTENT_HEADER_FONT_SIZE)
    assert size == 14.0


def test_render_pdf_content_slide_with_long_title_does_not_crash(tmp_path: Path):
    """Smoke test: a content slide with the exact long title that clipped in
    this deck's real content renders without error and produces a real file
    (the font-shrink fix is exercised end-to-end, not just unit-tested)."""
    long_title = "Why this is a science-integrity problem, not just a tooling problem"
    deck = DeckContent(title="Deck", slides=(Slide(title=long_title, bullets=("x",)),))
    output = render_pdf(deck, tmp_path / "long_title.pdf")
    assert output.is_file()
    reader = PdfReader(str(output))
    assert long_title in (reader.pages[1].extract_text() or "")
