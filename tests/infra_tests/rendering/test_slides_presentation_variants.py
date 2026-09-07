"""Real-file, image, PDF-scale, and writer tests for presentation variants."""

from __future__ import annotations

import copy
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote, urlsplit

from PIL import Image, ImageDraw
import pytest
from reportlab.pdfgen.canvas import Canvas

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._slides_accessibility import AccessibleSlidePolicy, compose_accessible_pandoc_document
from infrastructure.rendering._slides_accessibility_figures import _image_nodes
from infrastructure.rendering._slides_presentation_variants import reject_small_embedded_labels
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.slides_renderer import SlidesRenderer


class _ImageTargets(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.sources: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "img":
            self.sources.append(dict(attrs)["src"] or "")


def _fixture(root: Path, *, panels: int = 1, minimum: float = 40) -> tuple[dict[str, Any], dict[str, Any]]:
    root.mkdir(exist_ok=True)
    Image.new("RGB", (90, 300), "white").save(root / "canonical.png")
    records = []
    for index in range(panels):
        target = root / f"panel-{index}.png"
        raster = Image.new("RGB", (600, 240), (20 + index, 50, 80))
        ImageDraw.Draw(raster).text((30, 80), f"Panel {index + 1}", fill="white", font_size=minimum)
        raster.save(target)
        records.append(
            {
                "src": target.name,
                "alt": f"Complete panel {index + 1}",
                "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                "minimum_label_px": minimum,
            }
        )
    manifest = {"schema_version": "1.0", "panels": records}
    (root / "panels.json").write_text(json.dumps(manifest))
    image = {
        "t": "Image",
        "c": [
            ["", [], [["data-slide-manifest", "panels.json"]]],
            [{"t": "Str", "c": "Canonical alternative"}],
            ["canonical.png", ""],
        ],
    }
    document = {
        "pandoc-api-version": [1, 23, 1],
        "meta": {},
        "blocks": [
            {"t": "Header", "c": [2, ["", [], []], [{"t": "Str", "c": "Evidence"}]]},
            {"t": "Figure", "c": [["fig:evidence", [], []], [None, []], [{"t": "Plain", "c": [image]}]]},
        ],
    }
    return document, manifest


def _compose(root: Path, document: dict[str, Any]) -> dict[str, Any]:
    return compose_accessible_pandoc_document(
        document,
        policy=AccessibleSlidePolicy(),
        source=str(root / "source.md"),
        authorized_image_roots=(root,),
        figure_image_root=root,
    ).document


def test_variant_panels_preserve_source_and_reading_order(tmp_path: Path) -> None:
    document, _ = _fixture(tmp_path, panels=2)
    original = copy.deepcopy(document)
    result = _compose(tmp_path, document)
    images = _image_nodes(result)
    assert document == original
    assert [image["c"][2][0] for image in images] == ["panel-0.png", "panel-1.png"]
    assert [image["c"][1][0]["c"] for image in images] == ["Complete panel 1", "Complete panel 2"]
    assert "fig:evidence-slide-panel-2" in str(result)


def test_variant_identifiers_are_unique_for_anonymous_and_colliding_figures(tmp_path: Path) -> None:
    document, _ = _fixture(tmp_path)
    original = document["blocks"][-1]
    for label in ("", "", "fig:evidence-slide-panel-1"):
        extra = copy.deepcopy(original)
        extra["c"][0][0] = label
        document["blocks"].append(extra)
    result = _compose(tmp_path, document)
    labels = [block["c"][0][0] for block in result["blocks"] if block["t"] == "Figure"]
    assert len(labels) == 4
    assert len(set(labels)) == 4
    assert all(labels)


def test_variant_identifiers_reserve_headings_and_nested_inline_anchors(tmp_path: Path) -> None:
    document, _ = _fixture(tmp_path)
    collision = "fig:evidence-slide-panel-1"
    document["blocks"][0]["c"][1][0] = collision
    document["blocks"].insert(
        1, {"t": "Para", "c": [{"t": "Span", "c": [[collision + "-variant", [], []], [{"t": "Str", "c": "Anchor"}]]}]}
    )
    result = _compose(tmp_path, document)
    figures = [block for block in result["blocks"] if block["t"] == "Figure"]
    assert figures[0]["c"][0][0] == collision + "-variant-variant"


@pytest.mark.parametrize("owner", ("image", "wrapper", "caption"))
def test_variant_rejects_nested_identifiers_before_cloning(tmp_path: Path, owner: str) -> None:
    document, _ = _fixture(tmp_path, panels=2)
    figure = document["blocks"][-1]
    image = _image_nodes(figure)[0]
    if owner == "image":
        image["c"][0][0] = "image-anchor"
    elif owner == "wrapper":
        figure["c"][2][0]["c"] = [{"t": "Span", "c": [["wrapper-anchor", [], []], [image]]}]
    else:
        figure["c"][1][1] = [
            {"t": "Plain", "c": [{"t": "Span", "c": [["caption-anchor", [], []], [{"t": "Str", "c": "Caption"}]]}]}
        ]
    with pytest.raises(RenderingError, match="cannot contain nested identifiers"):
        _compose(tmp_path, document)


@pytest.mark.slow
@pytest.mark.parametrize("filename", ("panel?1.png", "panel 1.png"))
def test_real_pair_preserves_uri_sensitive_panel_filenames(tmp_path: Path, filename: str) -> None:
    figures = tmp_path / "figures"
    _, manifest = _fixture(figures)
    (figures / "panel-0.png").rename(figures / filename)
    manifest["panels"][0]["src"] = quote(filename, safe="/")
    (figures / "panels.json").write_text(json.dumps(manifest))
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    source = manuscript / "source.md"
    source.write_text(
        "## Evidence\n\n![Canonical](../figures/canonical.png)"
        '{#fig:evidence data-slide-manifest="../figures/panels.json"}\n'
    )
    output = tmp_path / "slides"
    renderer = SlidesRenderer(RenderingConfig(slides_profile="accessible", slides_dir=str(output)))
    pdf, html = renderer.render_accessible_pair(source, manuscript_dir=manuscript, figures_dir=figures)
    assert pdf.exists()
    targets = _ImageTargets()
    targets.feed(html.read_text())
    assert len(targets.sources) == 1
    target = urlsplit(targets.sources[0])
    assert not target.query and not target.fragment
    linked = (html.parent / unquote(target.path)).resolve()
    assert linked == (figures / filename).resolve()
    assert linked.read_bytes() == (figures / filename).read_bytes()


@pytest.mark.parametrize("filename", ("panel#1.png", "panel%20.png", "panel{1}.png", "panel\\1.png"))
def test_variant_rejects_nonportable_writer_filenames(tmp_path: Path, filename: str) -> None:
    document, manifest = _fixture(tmp_path)
    (tmp_path / "panel-0.png").rename(tmp_path / filename)
    manifest["panels"][0]["src"] = quote(filename, safe="/")
    (tmp_path / "panels.json").write_text(json.dumps(manifest))
    with pytest.raises(RenderingError, match="filename is not portable"):
        _compose(tmp_path, document)


@pytest.mark.parametrize(
    "target", ("missing.json", "../escape.json", "file:///tmp/escape.json", "https://invalid.example/a")
)
def test_variant_manifest_requires_confined_existing_local_file(tmp_path: Path, target: str) -> None:
    document, _ = _fixture(tmp_path)
    _image_nodes(document)[0]["c"][0][2][0][1] = target
    with pytest.raises(RenderingError, match="slides.security.figure-path"):
        _compose(tmp_path, document)


@pytest.mark.parametrize("kind", ("manifest", "panel"))
def test_variant_symlinks_are_rejected(tmp_path: Path, kind: str) -> None:
    document, _ = _fixture(tmp_path)
    path = tmp_path / ("panels.json" if kind == "manifest" else "panel-0.png")
    real = path.with_name("actual-" + path.name)
    path.rename(real)
    path.symlink_to(real)
    with pytest.raises(RenderingError, match="symlink"):
        _compose(tmp_path, document)


@pytest.mark.parametrize("minimum", (0, -1, float("nan"), True, "40"))
def test_variant_rejects_invalid_label_measurements(tmp_path: Path, minimum: Any) -> None:
    document, manifest = _fixture(tmp_path)
    manifest["panels"][0]["minimum_label_px"] = minimum
    (tmp_path / "panels.json").write_text(json.dumps(manifest))
    with pytest.raises(RenderingError, match="minimum_label_px"):
        _compose(tmp_path, document)


def test_variant_rejects_tampered_bytes_and_duplicate_attributes(tmp_path: Path) -> None:
    document, _ = _fixture(tmp_path)
    (tmp_path / "panel-0.png").write_bytes(b"tampered")
    with pytest.raises(RenderingError, match="producer digest"):
        _compose(tmp_path, document)
    _image_nodes(document)[0]["c"][0][2].append(["data-slide-manifest", "panels.json"])
    with pytest.raises(RenderingError, match="unique string pairs"):
        _compose(tmp_path, document)


def test_variant_rejects_duplicate_json_keys_and_oversized_manifest(tmp_path: Path) -> None:
    document, _ = _fixture(tmp_path)
    path = tmp_path / "panels.json"
    path.write_text('{"schema_version":"1.0","schema_version":"1.0","panels":[]}')
    with pytest.raises(RenderingError, match="unique-key JSON"):
        _compose(tmp_path, document)
    with path.open("wb") as handle:
        handle.truncate(1024 * 1024 + 1)
    with pytest.raises(RenderingError, match="bounded no-follow"):
        _compose(tmp_path, document)


def test_variant_cannot_bypass_geometry_through_metadata(tmp_path: Path) -> None:
    document, _ = _fixture(tmp_path)
    document["meta"] = {"title": {"t": "MetaInlines", "c": [_image_nodes(document)[0]]}}
    with pytest.raises(RenderingError, match="headings or metadata"):
        _compose(tmp_path, document)


@pytest.mark.parametrize("case", ("unknown", "duplicate", "empty", "too-many", "missing-panel", "remote-panel"))
def test_variant_panel_inventory_fails_closed(tmp_path: Path, case: str) -> None:
    document, manifest = _fixture(tmp_path)
    panel = manifest["panels"][0]
    if case == "unknown":
        panel["unsupported"] = True
    elif case == "duplicate":
        manifest["panels"].append(copy.deepcopy(panel))
    elif case == "empty":
        manifest["panels"] = []
    elif case == "too-many":
        manifest["panels"] = [panel] * 65
    elif case == "missing-panel":
        panel["src"] = "missing.png"
    else:
        panel["src"] = "https://invalid.example/panel.png"
    (tmp_path / "panels.json").write_text(json.dumps(manifest))
    with pytest.raises(RenderingError):
        _compose(tmp_path, document)


@pytest.mark.parametrize("width,passes", ((300, True), (120, False), (0, False)))
def test_actual_pdf_embedding_enforces_label_floor_and_missing_image(tmp_path: Path, width: int, passes: bool) -> None:
    document, _ = _fixture(tmp_path)
    source = tmp_path / "composed.json"
    source.write_text(json.dumps(_compose(tmp_path, document)))
    pdf = tmp_path / "scale.pdf"
    canvas = Canvas(str(pdf))
    if width:
        canvas.drawImage(str(tmp_path / "panel-0.png"), 30, 50, width=width, height=width * 0.4)
    canvas.showPage()
    canvas.save()
    if passes:
        reject_small_embedded_labels(pdf, source, minimum_pt=16)
        assert pdf.exists()
    else:
        with pytest.raises(RenderingError, match="slides.density.figure-label-scale"):
            reject_small_embedded_labels(pdf, source, minimum_pt=16)
        assert not pdf.exists()


@pytest.mark.slow
@pytest.mark.parametrize("profile", ("accessible", "archive"))
def test_real_beamer_reveal_pair_selects_variants_only_when_accessible(tmp_path: Path, profile: str) -> None:
    figures = tmp_path / "figures"
    _fixture(figures, minimum=100)
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    source = manuscript / "source.md"
    source.write_text(
        '## Evidence\n\n![Canonical](../figures/canonical.png){#fig:evidence data-slide-manifest="../figures/panels.json"}\n'
    )
    output = tmp_path / "slides"
    renderer = SlidesRenderer(RenderingConfig(slides_profile=profile, output_dir=str(output), slides_dir=str(output)))  # type: ignore[arg-type]
    if profile == "accessible":
        pdf, html = renderer.render_accessible_pair(source, manuscript_dir=manuscript, figures_dir=figures)
        assert pdf.exists() and html.exists()
        assert "panel-0.png" in html.read_text()
        assert "Complete panel 1" in html.read_text()
        images = _ImageTargets()
        images.feed(html.read_text())
        assert len(images.sources) == 1
        linked = html.parent / unquote(images.sources[0])
        assert linked.resolve() == (figures / "panel-0.png").resolve()
        assert linked.read_bytes() == (figures / "panel-0.png").read_bytes()
    else:
        html = renderer.render(source, output_format="revealjs", manuscript_dir=manuscript, figures_dir=figures)
        assert "canonical.png" in html.read_text()
        assert "panel-0.png" not in html.read_text()


@pytest.mark.slow
def test_real_pair_rejects_small_labels_and_removes_both_derivatives(tmp_path: Path) -> None:
    figures = tmp_path / "figures"
    _fixture(figures, minimum=1)
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    source = manuscript / "source.md"
    source.write_text(
        "## Evidence\n\n![Canonical](../figures/canonical.png)"
        '{#fig:evidence data-slide-manifest="../figures/panels.json"}\n'
    )
    output = tmp_path / "slides"
    output.mkdir()
    (output / "source_slides.html").write_text("stale prior derivative")
    renderer = SlidesRenderer(RenderingConfig(slides_profile="accessible", slides_dir=str(output)))
    with pytest.raises(RenderingError, match="slides.density.figure-label-scale"):
        renderer.render_accessible_pair(source, manuscript_dir=manuscript, figures_dir=figures)
    assert not (output / "source_slides.pdf").exists()
    assert not (output / "source_slides.html").exists()
