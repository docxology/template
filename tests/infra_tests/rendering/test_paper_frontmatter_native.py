"""Required real compiler contracts; pure admission remains in smoke."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering.manuscript_discovery import discover_manuscript_files
from tests.infra_tests.rendering.test_paper_frontmatter import _native_project


@pytest.mark.requires_latex
@pytest.mark.timeout(120)
def test_real_pdf_and_html_keep_three_complete_pages_before_contents(tmp_path: Path) -> None:
    from html.parser import HTMLParser
    from pypdf import PdfReader

    manuscript, manager = _native_project(tmp_path)
    sources = discover_manuscript_files(manuscript)
    pdf = manager.render_combined_pdf(sources, manuscript, "frontmatter_fixture")
    web = manager.render_combined_web(sources, manuscript, "frontmatter_fixture")
    pages = PdfReader(pdf).pages
    assert len(pages) == 6
    texts = [" ".join(page.extract_text().split()) for page in pages]
    assert "Engineering frontmatter" in texts[0]
    for index, name in enumerate(("Alpha", "Beta", "Gamma"), 1):
        assert f"Panel {name}" in texts[index]
        assert f"Terminal caption {name}." in texts[index]
        assert len(pages[index].images) == 1
        source = Image.open(tmp_path / "output/figures" / f"plate-{name.lower()}.png").convert("RGB")
        assert pages[index].images[0].image.convert("RGB").tobytes() == source.tobytes()
    assert "Contents" in texts[4]
    assert "Engineering body" in texts[5]

    class Reader(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.ids: list[str] = []
            self.alts: list[str] = []
            self.text_parts: list[str] = []

        def handle_data(self, data: str) -> None:
            self.text_parts.append(data)

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            attributes = dict(attrs)
            if attributes.get("id"):
                self.ids.append(str(attributes["id"]))
            if tag == "img":
                self.alts.append(str(attributes.get("alt")))

    text = web.read_text(encoding="utf-8")
    parsed = Reader()
    parsed.feed(text)
    plain = " ".join(" ".join(parsed.text_parts).split())
    ordered = ["paper-cover", "paper-frontmatter-1", "paper-frontmatter-2", "paper-frontmatter-3", "TOC", "paper-body"]
    assert all(parsed.ids.count(identifier) == 1 for identifier in ordered)
    assert [parsed.ids.index(identifier) for identifier in ordered] == sorted(parsed.ids.index(i) for i in ordered)
    assert "Engineering cover alternative." in parsed.alts
    for name in ("Alpha", "Beta", "Gamma"):
        assert f"Concise alternative for {name}." in parsed.alts
        assert f"Complete first paragraph for {name}." in text
        assert f"Complete second paragraph for {name}." in text
        caption = f"Engineering panel {name}. Complete caption retained at ordinary text size. Terminal caption {name}."
        assert caption in plain


@pytest.mark.requires_latex
@pytest.mark.timeout(120)
def test_real_tex_overflow_is_a_failed_render(tmp_path: Path) -> None:
    manuscript, manager = _native_project(tmp_path, overflow=True)
    with pytest.raises(RenderingError):
        manager.render_combined_pdf(discover_manuscript_files(manuscript), manuscript, "overflow_fixture")
    log = tmp_path / "output/pdf/_combined_manuscript.log"
    assert "paper.frontmatter page overflow" in log.read_text(encoding="utf-8")
