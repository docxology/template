"""Integration tests: render the real edition to a PDF and assert on it."""

from __future__ import annotations

from pathlib import Path

from newspaper.content import Block, Box, Edition, Figure, Page, Story
from newspaper.config import NewspaperConfig
from newspaper.engine import RenderResult, build_and_render, render_edition


def _read_pdf_page_count(path: Path) -> int:
    """Count pages by scanning for /Type /Page tokens (no external dep)."""
    data = path.read_bytes()
    assert data.startswith(b"%PDF-"), "not a PDF"
    return data.count(b"/Type /Page") - data.count(b"/Type /Pages")


def test_render_real_edition(project_root, tmp_path) -> None:
    out = tmp_path / "triplicate.pdf"
    from newspaper.content import load_edition
    from newspaper.config import load_newspaper_config

    edition = load_edition(project_root / "content")
    config = load_newspaper_config(project_root / "content")
    result = render_edition(edition, config, project_root=project_root, output_path=out)

    assert out.exists()
    assert result.page_count == 12
    assert result.all_pages_fit, f"over-set pages: {result.oversets}"
    assert _read_pdf_page_count(out) == 12
    assert out.stat().st_size > 50_000  # a real 12-page paper is not trivially small


def test_render_edition_accepts_str_output_path(project_root, tmp_path) -> None:
    """`render_edition` accepts a str output_path symmetrically with `build_and_render`."""
    from newspaper.content import load_edition
    from newspaper.config import load_newspaper_config

    out = tmp_path / "triplicate.pdf"
    edition = load_edition(project_root / "content")
    config = load_newspaper_config(project_root / "content")
    result = render_edition(edition, config, project_root=project_root, output_path=str(out))
    assert out.exists()
    assert result.page_count == 12


def test_render_with_base14_fallback_fonts_still_fits(project_root, tmp_path) -> None:
    """Cross-platform guarantee (no mocks): rendering with the base-14 fallback
    Fonts (what a machine lacking the macOS faces resolves to) still produces a
    12-page paper with no over-set — the 'structurally identical' claim, tested."""
    from newspaper.content import load_edition
    from newspaper.config import load_newspaper_config
    from newspaper.typography import Fonts

    base14 = Fonts(
        display="Times-Roman",
        display_bold="Times-Bold",
        body="Times-Roman",
        body_bold="Times-Bold",
        body_italic="Times-Italic",
        body_bolditalic="Times-BoldItalic",
        sans="Helvetica",
        sans_bold="Helvetica-Bold",
    )
    out = tmp_path / "base14.pdf"
    edition = load_edition(project_root / "content")
    config = load_newspaper_config(project_root / "content")
    result = render_edition(edition, config, project_root=project_root, output_path=out, fonts=base14)
    assert result.page_count == 12
    assert result.all_pages_fit, f"base-14 render over-set: {result.oversets}"


def test_build_and_render_default_path(project_root, tmp_path) -> None:
    out = tmp_path / "out.pdf"
    result = build_and_render(project_root, output_path=out)
    assert result.output_path == out
    assert out.exists()
    assert result.to_dict()["page_count"] == 12


def test_build_and_render_auto_output_path(project_root, tmp_path) -> None:
    """build_and_render with output_path=None derives the path from project_root.

    The project_root here is a tmp copy with content/ symlinked so the edition
    loads but output/ goes to tmp_path. We pass a synthetic project_root that
    has a content/ subdirectory with the real edition, so no real output/ is
    written. The test verifies that the auto-derived path is returned.
    """

    # Build a minimal project root in tmp with content/ pointing at real content.
    fake_root = tmp_path / "fake_project"
    fake_root.mkdir()
    # Symlink the real content directory so the edition loads.
    (fake_root / "content").symlink_to(project_root / "content")
    # Let build_and_render derive the output path (line 101 in engine.py).
    result = build_and_render(fake_root, output_path=None)
    expected = fake_root / "output" / "pdf" / "the-triplicate.pdf"
    assert result.output_path == expected
    assert expected.exists()
    assert result.page_count == 12


def test_render_result_serializes_repository_relative_output(project_root) -> None:
    """Checked render evidence must not retain a machine-local checkout path."""
    output = project_root / "output" / "pdf" / "portable.pdf"
    result = RenderResult(output_path=output, page_count=1)

    assert result.to_dict(relative_to=project_root)["output_path"] == "output/pdf/portable.pdf"


def test_synthetic_minimal_edition(tmp_path) -> None:
    """A tiny hand-built edition exercises every template branch and renders."""
    pages = [
        Page(
            number=1,
            template="front",
            columns=3,
            rail=True,
            lead=Story(
                headline="Test lead",
                level="lead",
                kicker="Test",
                deck="A deck.",
                byline="By A. Tester",
                drop_cap=True,
                body=[
                    Block("p", "First paragraph of the lead story flows here."),
                    Block("subhead", "A subhead"),
                    Block("pull", "A memorable pull quote.", "Someone"),
                    Block("p", "Second paragraph continues the report."),
                ],
                figure=Figure(path="missing.png", caption="cap", credit="cr", height=120),
            ),
            rail_items=[
                Box(kind="index", title="Inside", items=["A · 2", "B · 3"]),
                Box(kind="weather", title="Weather", rows=[["", "Hi", "Lo"], ["Today", "60", "50"]]),
            ],
            main_items=[Story(headline="Second", level="secondary", body=[Block("p", "Body text.")])],
        ),
        Page(
            number=2,
            template="classified",
            columns=4,
            main_items=[
                Box(kind="generic", title="For Sale", items=["Item one", "Item two"]),
                Box(kind="display", title="House Ad", body=[Block("p", "Subscribe today.")]),
            ],
        ),
    ]
    edition = Edition(nameplate="Test Times", city="Nowhere", state="CA", date="Today", pages=pages)
    out = tmp_path / "synthetic.pdf"
    result = render_edition(edition, NewspaperConfig(), project_root=tmp_path, output_path=out)
    assert result.page_count == 2
    assert out.exists()


def test_overset_is_detected_not_silent(tmp_path) -> None:
    """An over-long story must be reported as over-set, not silently dropped.

    This is the flip-test that gives ``all_pages_fit`` its meaning: ReportLab
    frames discard flowables that do not fit, so the engine counts the remainder.
    Without this, a green render could be hiding lost copy.
    """
    flood = [Block("p", "A long paragraph repeated to overflow the page. " * 40) for _ in range(60)]
    page = Page(number=1, template="standard", columns=2, main_items=[Story(headline="Flood", body=flood)])
    edition = Edition(nameplate="T", city="C", state="S", date="D", pages=[page])
    out = tmp_path / "overset.pdf"
    result = render_edition(edition, NewspaperConfig(), project_root=tmp_path, output_path=out)
    assert not result.all_pages_fit
    assert result.oversets.get(1, 0) > 0


def test_render_is_deterministic(project_root, tmp_path) -> None:
    """The same content renders to identical bytes (invariant mode)."""
    import hashlib

    from newspaper.config import load_newspaper_config
    from newspaper.content import load_edition

    edition = load_edition(project_root / "content")
    config = load_newspaper_config(project_root / "content")
    a = tmp_path / "a.pdf"
    b = tmp_path / "b.pdf"
    render_edition(edition, config, project_root=project_root, output_path=a)
    render_edition(edition, config, project_root=project_root, output_path=b)
    assert hashlib.sha256(a.read_bytes()).hexdigest() == hashlib.sha256(b.read_bytes()).hexdigest()


def test_zero_page_edition_reports_zero(tmp_path) -> None:
    # The manifest loader already rejects an empty page list; a directly
    # constructed empty Edition renders to a zero-page result rather than raising.
    edition = Edition(nameplate="Empty", city="X", state="Y", date="Z", pages=[])
    out = tmp_path / "empty.pdf"
    result = render_edition(edition, NewspaperConfig(), project_root=tmp_path, output_path=out)
    assert result.page_count == 0
    assert result.all_pages_fit
