"""Real Pandoc controls for source-specific Mermaid sizing in DOCX."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from zipfile import ZipFile

import pytest
from defusedxml.ElementTree import fromstring
from PIL import Image

from infrastructure.rendering.docx_renderer import render_docx
from infrastructure.rendering.office_diagram_layout import MAX_HEIGHT_EMU, W, WP

pytestmark = pytest.mark.skipif(shutil.which("pandoc") is None, reason="requires the real DOCX Pandoc writer")


def _make_manuscript(tmp_path: Path, *, same_uri: bool = True) -> tuple[Path, str]:
    web = tmp_path / "output" / "web"
    diagrams = web.parent / "figures" / "mermaid_inline"
    web.mkdir(parents=True)
    diagrams.mkdir(parents=True)
    image = diagrams / "inline_mermaid_0001_a2bb1595c3a4.png"
    Image.new("RGB", (400, 1000), "navy").save(image)
    digest = hashlib.sha256(image.read_bytes()).hexdigest()
    generated_uri = f"../figures/mermaid_inline/{image.name}"
    normal_uri = generated_uri
    if not same_uri:
        (web / "repeat.png").write_bytes(image.read_bytes())
        normal_uri = "repeat.png"
    manuscript = web / "_combined_manuscript.md"
    manuscript.write_text(
        f'![Regular caption]({normal_uri} "Regular & title")'
        '{width=75% alt="Same alternative without an identifier."}\n\n'
        f'![Rendered caption]({generated_uri} "Rendered & title")'
        '{#fig:rendered width=82% alt="Same alternative without an identifier." '
        "data-template-max-height=4.2in}\n",
        encoding="utf-8",
    )
    return manuscript, digest


def _read_document(path: Path) -> tuple[list[tuple[tuple[int, int], str, str]], str]:
    with ZipFile(path) as native:
        for name in native.namelist():
            assert b"template-docx-mermaid-" not in native.read(name), name
        document = fromstring(native.read("word/document.xml"))
    drawings = []
    for node in document.iter(WP + "inline"):
        extent = node.find(WP + "extent")
        properties = node.find(WP + "docPr")
        assert extent is not None and properties is not None
        dimensions = (int(extent.attrib["cx"]), int(extent.attrib["cy"]))
        drawings.append((dimensions, properties.attrib["title"], properties.attrib["descr"]))
    return drawings, " ".join(node.text or "" for node in document.iter(W + "t"))


@pytest.mark.parametrize("same_uri", [False, True], ids=["equal-bytes", "equal-uri"])
def test_docx_only_sizes_the_generated_mermaid_occurrence(tmp_path: Path, same_uri: bool) -> None:
    source, digest = _make_manuscript(tmp_path, same_uri=same_uri)
    options = [f"--resource-path={source.parent}"]
    if crossref := shutil.which("pandoc-crossref"):
        options.append(f"--filter={crossref}")
    ordinary = tmp_path / "ordinary.docx"
    render_docx(source, ordinary, extra_args=options)
    baseline, _ = _read_document(ordinary)
    assert len(baseline) == 2 and baseline[0][0][1] > MAX_HEIGHT_EMU and baseline[1][0][1] > MAX_HEIGHT_EMU
    assert baseline[0][2] == baseline[1][2] == "Same alternative without an identifier."

    output = tmp_path / "verified.docx"
    render_docx(source, output, extra_args=options, diagram_png_sha256=(digest,), mark_mermaid_occurrences=True)
    drawings, text = _read_document(output)
    assert len(drawings) == 2
    assert drawings[0] == baseline[0]
    assert drawings[1][1:] == baseline[1][1:] == ("Rendered & title", "Same alternative without an identifier.")
    (old_width, old_height), _, _ = baseline[1]
    assert drawings[1][0] == (old_width * MAX_HEIGHT_EMU // old_height, MAX_HEIGHT_EMU)
    assert "Regular caption" in text and "Rendered caption" in text
    assert not list(tmp_path.glob(".docx-writer-*"))


@pytest.mark.parametrize("prior_output", [False, True], ids=["new-destination", "existing-destination"])
def test_docx_invalid_layout_does_not_publish_the_intermediate_package(tmp_path: Path, prior_output: bool) -> None:
    source, digest = _make_manuscript(tmp_path)
    options = [f"--resource-path={source.parent}"]
    output = tmp_path / "verified.docx"
    previous = None
    if prior_output:
        previous_source = tmp_path / "previous.md"
        previous_source.write_text("# Previously verified contents\n", encoding="utf-8")
        render_docx(previous_source, output)
        previous = output.read_bytes()
    bad_digest = "0" * 64
    assert bad_digest != digest

    with pytest.raises(ValueError, match="(?i)(source PNG|source occurrence)"):
        render_docx(source, output, extra_args=options, diagram_png_sha256=(bad_digest,), mark_mermaid_occurrences=True)

    assert (output.read_bytes() if output.exists() else None) == previous
    assert not list(tmp_path.glob(".docx-writer-*"))


def test_docx_keeps_digest_only_layout_for_existing_callers(tmp_path: Path) -> None:
    source, digest = _make_manuscript(tmp_path, same_uri=False)
    source.write_text(
        '![Legacy image](repeat.png "Legacy title"){width=82% alt="Legacy alternative"}\n', encoding="utf-8"
    )
    output = tmp_path / "legacy.docx"
    render_docx(source, output, extra_args=[f"--resource-path={source.parent}"], diagram_png_sha256=(digest,))
    drawings, _ = _read_document(output)
    assert len(drawings) == 1
    assert drawings[0][0][1] == MAX_HEIGHT_EMU
    assert drawings[0][1:] == ("Legacy title", "Legacy alternative")

    marked_destination = tmp_path / "missing-marker.docx"
    with pytest.raises(ValueError, match="dropped or duplicated"):
        render_docx(
            source,
            marked_destination,
            extra_args=[f"--resource-path={source.parent}"],
            diagram_png_sha256=(digest,),
            mark_mermaid_occurrences=True,
        )
    assert not marked_destination.exists()
