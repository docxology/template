"""Tests for infrastructure/rendering/web_renderer.py split by area.

Tests web/HTML rendering functionality using real implementations.
Follows No Mocks Policy - all tests use real data and real execution.
"""

from html.parser import HTMLParser
from pathlib import Path

import pytest
from PIL import Image

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.web_renderer import WebRenderer

from ._web_renderer_test_helpers import _make_renderer


class TestHtmlRendering:
    """Test HTML rendering functionality."""

    def test_render_html(self, tmp_path):
        """WebRenderer.render writes HTML that contains the source heading."""
        md = tmp_path / "doc.md"
        md.write_text("# Title\n\nContent", encoding="utf-8")
        renderer = _make_renderer(tmp_path)
        result = renderer.render(md)
        assert result.exists()
        html = result.read_text(encoding="utf-8")
        assert "Title" in html
        assert "Content" in html

    def test_render_html_uses_configured_web_dir(self, tmp_path):
        """Output lands under the configured web_dir, not a hidden default."""
        md = tmp_path / "doc.md"
        md.write_text("# Title", encoding="utf-8")
        renderer = _make_renderer(tmp_path)
        result = renderer.render(md)
        assert result.parent == Path(renderer.config.web_dir)


@pytest.mark.parametrize("invalid", ["empty", "encoding", "missing"])
def test_combined_invalid_manuscript_refuses_to_publish_html(tmp_path: Path, invalid: str) -> None:
    """Invalid actual source files must not produce a successful HTML edition."""
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    source = manuscript / "01_section.md"
    if invalid != "missing":
        source.write_bytes(b"" if invalid == "empty" else b"\x80\x81\x82")
    renderer = _make_renderer(tmp_path)

    with pytest.raises((RenderingError, OSError)):
        renderer.render_combined([source], manuscript, "invalid-proof")

    assert not list(Path(renderer.config.web_dir).glob("*.html"))


@pytest.mark.parametrize("publication", ["preview", "combined"])
@pytest.mark.parametrize(
    "names",
    [
        pytest.param(("first/unit/chapter.md", "second/unit/chapter.md"), id="repeated-parent"),
        pytest.param(("chapter+a.md", "chapter a.md"), id="sanitized-name"),
    ],
)
def test_distinct_sources_retain_their_own_published_pages(
    tmp_path: Path, publication: str, names: tuple[str, str]
) -> None:
    manuscript = tmp_path / "manuscript"
    sources = []
    for name, own, other in zip(names, ("first", "second"), ("second", "first"), strict=True):
        source = manuscript / name
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(
            f'# {own.title()} {{#{own}}}\n\n<a data-proof="other" href="#{other}">Other source</a>\n',
            encoding="utf-8",
        )
        sources.append(source)
    web_dir = tmp_path / "output/web"
    renderer = WebRenderer(
        RenderingConfig(
            manuscript_dir=str(manuscript),
            figures_dir=str(tmp_path / "output/figures"),
            output_dir=str(tmp_path / "output"),
            web_dir=str(web_dir),
        )
    )

    class Document(HTMLParser):
        def __init__(self, page: Path) -> None:
            super().__init__()
            self.headings: set[str] = set()
            self.other: str | None = None
            self.feed(page.read_text(encoding="utf-8"))
            self.close()

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            attributes = dict(attrs)
            identifier = attributes.get("id")
            if tag in {"h1", "h2", "h3", "h4", "h5", "h6"} and identifier:
                self.headings.add(identifier)
            if tag == "a" and attributes.get("data-proof") == "other":
                self.other = attributes.get("href")

    if publication == "preview":
        pages = [renderer.render(source) for source in sources]
        assert pages[0] != pages[1]
        assert [Document(page).headings for page in pages] == [{"first"}, {"second"}]
    else:
        combined = renderer.render_combined(sources, manuscript, "distinct-source-pages")
        pages = [page for page in web_dir.glob("*.html") if page != combined]
        owned = {own: page for page in pages for own in Document(page).headings if own in {"first", "second"}}
        assert set(owned) == {"first", "second"} and owned["first"] != owned["second"]
        assert Document(combined).headings >= {"first", "second"}
        for own, other in (("first", "second"), ("second", "first")):
            document = Document(owned[own])
            assert document.headings == {own}
            assert document.other == f"{owned[other].name}#{other}"


@pytest.mark.parametrize(
    "relative_image",
    ["../../../../figures/plots/dense.png", "../../../../../output/figures/plots/dense.png"],
)
@pytest.mark.parametrize("combined", [False, True])
def test_nested_manuscript_figures_keep_registry_identity_and_literal_paths(
    tmp_path: Path, combined: bool, relative_image: str
) -> None:
    output = tmp_path / "output"
    manuscript = output / "manuscript"
    source = manuscript / "parts" / "unit" / "chapter" / "overview.md"
    source.parent.mkdir(parents=True)
    figures = output / "figures"
    (figures / "plots").mkdir(parents=True)
    Image.new("RGB", (8, 8), color=(30, 60, 90)).save(figures / "plots" / "dense.png")
    (figures / "figure_registry.json").write_text(
        '{"fig:dense":{"filename":"plots/dense.png","alt_text":"A blue square; synthetic layout fixture."}}',
        encoding="utf-8",
    )
    literal_tag = f'<img src="{relative_image}">'
    source.write_text(
        f"# Results\n\n![Caption]({relative_image}){{#fig:dense}}\n\n"
        f"`{literal_tag}`\n\n```html\n{literal_tag}\n```\n\n`{relative_image}`\n",
        encoding="utf-8",
    )
    renderer = WebRenderer(
        RenderingConfig(output_dir=str(output), figures_dir=str(figures), web_dir=str(output / "web"))
    )
    rendered_path = renderer.render_combined([source], manuscript, "test") if combined else renderer.render(source)
    rendered = rendered_path.read_text(encoding="utf-8")
    assert 'src="../figures/plots/dense.png"' in rendered
    assert 'alt="A blue square; synthetic layout fixture."' in rendered

    class CodeReader(HTMLParser):
        def __init__(self):
            super().__init__()
            self.active = False
            self.code: list[str] = []

        def handle_starttag(self, tag, attrs):
            if tag == "code":
                self.active = True
                self.code.append("")

        def handle_endtag(self, tag):
            if tag == "code":
                self.active = False

        def handle_data(self, text):
            if self.active:
                self.code[-1] += text

    reader = CodeReader()
    reader.feed(rendered)
    assert [code.strip() for code in reader.code] == [literal_tag, literal_tag, relative_image]


@pytest.mark.parametrize("combined", [False, True])
def test_render_preserves_planted_temporary_symlink(tmp_path: Path, combined: bool) -> None:
    """Real Pandoc rendering must not overwrite a predictable temp link's target."""
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    source = manuscript / "section.md"
    source.write_text("# Safe publication\n\nBody text.\n", encoding="utf-8")
    web = tmp_path / "output" / "web"
    web.mkdir(parents=True)
    protected = tmp_path / "unrelated.txt"
    protected.write_text("keep original bytes", encoding="utf-8")
    trap = web / "_combined_manuscript.md.tmp" if combined else source.with_suffix(".md.web.tmp")
    trap.symlink_to(protected)
    renderer = WebRenderer(RenderingConfig(web_dir=str(web), output_dir=str(web.parent)))

    result = renderer.render_combined([source], manuscript) if combined else renderer.render(source)

    assert "Safe publication" in result.read_text(encoding="utf-8")
    assert protected.read_text(encoding="utf-8") == "keep original bytes"
    assert trap.is_symlink()
    assert source.read_text(encoding="utf-8") == "# Safe publication\n\nBody text.\n"
    assert not list(web.glob(".web-source-*"))


def test_render_cleans_private_source_after_pandoc_failure(tmp_path: Path) -> None:
    """Failed subprocesses leave no preprocessed manuscript copies behind."""
    source = tmp_path / "section.md"
    source.write_text("# Private source\n", encoding="utf-8")
    web = tmp_path / "web"
    renderer = WebRenderer(RenderingConfig(web_dir=str(web), pandoc_path="/usr/bin/false"))
    with pytest.raises(RenderingError):
        renderer.render(source)
    assert not list(web.glob(".web-source-*"))
    assert not source.with_suffix(".md.web.tmp").exists()


@pytest.mark.parametrize("source_kind", ["missing", "directory"])
def test_render_source_io_failure_keeps_rendering_error_contract(tmp_path: Path, source_kind: str) -> None:
    """Input I/O failures retain the public error type and remove private copies."""
    source = tmp_path / "invalid.md"
    if source_kind == "directory":
        source.mkdir()
    web = tmp_path / "web"
    renderer = WebRenderer(RenderingConfig(web_dir=str(web)))
    with pytest.raises(RenderingError) as caught:
        renderer.render(source)
    assert isinstance(caught.value.__cause__, OSError)
    assert not list(web.glob(".web-source-*"))
    assert not list(web.glob("*.html"))


def test_individual_render_preserves_existing_page_permissions(tmp_path: Path) -> None:
    """Re-rendering a page must not widen its existing permission mode."""
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    source = manuscript_dir / "03_results.md"
    source.write_text("# Results\n\nA short prose paragraph for rendering.\n", encoding="utf-8")
    web_dir = tmp_path / "output" / "web"
    renderer = WebRenderer(RenderingConfig(web_dir=str(web_dir), output_dir=str(tmp_path / "output")))
    target = renderer._output_file_for_source(source)
    web_dir.mkdir(parents=True)
    target.write_text("<html><body>old</body></html>", encoding="utf-8")
    target.chmod(0o600)

    renderer.render(source)

    assert target.is_file()
    assert (target.stat().st_mode & 0o777) == 0o600
