"""Exercise Mermaid figure destinations through the real Office writers."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path
from urllib.parse import unquote
from xml.etree import ElementTree

import pytest
from PIL import Image

from infrastructure.rendering._pandoc_args import combined_pandoc_args
from infrastructure.rendering._pdf_mermaid import (
    _MERMAID_BLOCK_RE,
    _normalise_mermaid_source,
    _source_hash,
    inline_mermaid_figure_markdown,
)
from infrastructure.rendering.docx_renderer import render_docx
from infrastructure.rendering.epub_renderer import render_epub
from infrastructure.rendering.office_mermaid_projection import project_office_mermaid_figures
from infrastructure.rendering.office_native_projection import W, office_semantics_filter_path

_LABEL = "fig:mermaid-owner"
_ALT = "An arrow connects two nodes."
_WORD_DRAWING = "{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}"
_XHTML = "{http://www.w3.org/1999/xhtml}"


def test_projected_mermaid_figure_resolves_in_docx_and_epub(tmp_path: Path) -> None:
    pandoc = shutil.which("pandoc")
    if pandoc is None or shutil.which("pandoc-crossref") is None:
        pytest.skip("Pandoc and pandoc-crossref are required for native figure references")
    source = (
        "# Introduction\n\n:::: {.context #outer-context}\n\n"
        f'::: {{#{_LABEL} .diagram data-owner="author"}}\n\n'
        f"```mermaid\ngraph TD\nA --> B\n```\n<!-- alt: {_ALT} -->\n\n"
        "*Visible **diagram** caption.*\n\n:::\n\n::::\n\n"
        f"See @{_LABEL}.\n"
    )
    match = _MERMAID_BLOCK_RE.search(source)
    assert match is not None
    diagram = _normalise_mermaid_source(match.group("source").strip())
    figures_dir = tmp_path / "figures"
    png = figures_dir / "mermaid_inline" / f"inline_mermaid_0001_{_source_hash(diagram)}.png"
    png.parent.mkdir(parents=True)
    Image.new("RGB", (40, 30), "blue").save(png)
    preprocessed = source[: match.start()] + inline_mermaid_figure_markdown(match, png.name) + source[match.end() :]
    combined = tmp_path / "manuscript" / "combined.md"
    combined.parent.mkdir()
    combined.write_text(project_office_mermaid_figures(preprocessed, source).content, encoding="utf-8")
    args = combined_pandoc_args([combined.parent, figures_dir, tmp_path], [], edition="Office")
    args.append("--metadata=linkReferences:true")

    docx = render_docx(
        combined,
        tmp_path / "reader.docx",
        pandoc_path=pandoc,
        extra_args=args,
        diagram_png_sha256=(hashlib.sha256(png.read_bytes()).hexdigest(),),
    )
    with zipfile.ZipFile(docx.output_path) as package:
        document = ElementTree.fromstring(package.read("word/document.xml"))
    [(bookmark, number)] = [
        (node.get(W + "anchor"), "".join(node.itertext()))
        for node in document.iter(W + "hyperlink")
        if node.get(W + "anchor")
    ]
    assert number == "1"
    elements = list(document.iter())
    [start] = [node for node in document.iter(W + "bookmarkStart") if node.get(W + "name") == bookmark]
    [end] = [node for node in document.iter(W + "bookmarkEnd") if node.get(W + "id") == start.get(W + "id")]
    [drawing] = list(document.iter(_WORD_DRAWING + "docPr"))
    assert elements.index(start) < elements.index(drawing) < elements.index(end)
    assert "Figure 1: Visible diagram caption." in "".join(document.itertext())
    assert drawing.get("descr") == _ALT

    epub = render_epub(
        combined, tmp_path / "reader.epub", title="Figure reference", pandoc_path=pandoc, extra_args=args
    )
    with zipfile.ZipFile(epub.output_path) as package:
        chapters = [
            ElementTree.fromstring(package.read(name)) for name in package.namelist() if name.endswith(".xhtml")
        ]
    [(chapter, link)] = [
        (chapter, node)
        for chapter in chapters
        for node in chapter.iter(_XHTML + "a")
        if unquote(node.get("href", "")) == f"#{_LABEL}"
    ]
    assert "".join(link.itertext()) == "1"
    [figure] = [node for node in chapter.iter() if node.get("id") == _LABEL]
    assert figure.tag == _XHTML + "figure"
    assert [node.get("alt") for node in figure.iter(_XHTML + "img")] == [_ALT]
    assert "Figure 1: Visible diagram caption." in "".join(figure.itertext())
    [outer] = [node for node in chapter.iter(_XHTML + "div") if node.get("id") == "outer-context"]
    [context] = [node for node in outer.iter(_XHTML + "div") if node.get("data-owner") == "author"]
    assert context.get("class") == "diagram"
    assert list(context.iter(_XHTML + "figure")) == [figure]


def test_office_mermaid_reference_projection_leaves_other_source_blocks_alone() -> None:
    pandoc = shutil.which("pandoc")
    if pandoc is None:
        pytest.skip("Pandoc is required for native Office AST projection")
    target = "../figures/mermaid_inline/inline_mermaid_0001_12abcdef3456.png"
    height = "data-template-max-height=4.2in"
    source = (
        f"::: {{#ordinary-context}}\n\n![Diagram.]({target}){{{height}}}\n\n:::\n\n"
        f"::: {{#fig:other-image}}\n\n![Other figure.](figure.png){{{height}}}\n\n:::\n\n"
        f"::: {{#fig:ordinary-asset}}\n\n![Ordinary image.]({target})\n\n:::\n\n"
        f"::: {{#fig:unmoved-wrapper}}\n\n![Already labeled.]({target}){{#fig:inner {height}}}\n\n:::\n\n"
        f"::: {{#fig:extra-context}}\n\n![Diagram.]({target}){{{height}}}\n\nAdditional text.\n\n:::\n\n"
        f"::: {{#fig:group .subfigures}}\n\n![Panel.]({target}){{{height}}}\n\n:::\n\n"
        "::: {#fig:mermaid-fallback}\n\n```mermaid\ngraph TD\nA --> B\n```\n\n:::\n"
    )
    command = [pandoc, "-f", "markdown", "-t", "json", "--metadata=office-native-target:docx"]
    original = subprocess.check_output(command, input=source, text=True, timeout=20)
    projected = subprocess.check_output(
        [*command, "--lua-filter", str(office_semantics_filter_path())], input=source, text=True, timeout=20
    )
    assert json.loads(projected)["blocks"] == json.loads(original)["blocks"]
