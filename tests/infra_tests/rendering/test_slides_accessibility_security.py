"""Security-boundary regressions for accessible slide composition."""

from __future__ import annotations

from pathlib import Path
import struct
from typing import Any
from urllib.parse import quote
import zlib

from PIL import Image
import pytest

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._slides_accessibility import (
    AccessibleSlidePolicy,
    compose_accessible_pandoc_document,
)
from infrastructure.rendering._slides_accessibility_composition import _with_inline_writer_fallbacks
from infrastructure.rendering._slides_accessibility_image_io import (
    MAX_INTRINSIC_IMAGE_BYTES,
    MAX_INTRINSIC_IMAGE_PIXELS,
)
from infrastructure.rendering._slides_accessibility_limits import (
    MAX_ACCESSIBLE_PANDOC_AST_DEPTH,
    MAX_ACCESSIBLE_PANDOC_AST_NODES,
    validate_accessible_ast_limits,
)
from infrastructure.rendering._slides_accessibility_raw_tex import _math_fragments
from infrastructure.rendering._slides_math_header import write_slides_math_header
from infrastructure.rendering.security import RenderSecurityProfile


def _header() -> dict[str, Any]:
    return {"t": "Header", "c": [2, ["", [], []], [{"t": "Str", "c": "Security"}]]}


def _document(block: dict[str, Any]) -> dict[str, Any]:
    return {"pandoc-api-version": [1, 23, 1], "meta": {}, "blocks": [_header(), block]}


def _formal_raw(body: str) -> dict[str, Any]:
    return {"t": "RawBlock", "c": ["latex", rf"\begin{{theorem}}{body}\end{{theorem}}"]}


def _figure(target: str) -> dict[str, Any]:
    image = {
        "t": "Image",
        "c": [["", [], []], [{"t": "Str", "c": "Figure alternative"}], [target, ""]],
    }
    return {
        "t": "Figure",
        "c": [["fig:security", [], []], [None, []], [{"t": "Plain", "c": [image]}]],
    }


def _png_with_declared_size(path: Path, width: int, height: int) -> None:
    """Write a tiny PNG whose IHDR declares dimensions without pixel allocation."""

    def chunk(kind: bytes, payload: bytes) -> bytes:
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload))

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IEND", b""))


@pytest.mark.parametrize(
    "translation",
    (
        "^^5cinput{canary}",
        "^^5Cinput{canary}",
        "^^^^005cinput{canary}",
        "^^Minput{canary}",
        "^^Jinput{canary}",
        "^^\ninput{canary}",
    ),
)
def test_tex_lexical_translation_forms_fail_before_writer_fallback(translation: str) -> None:
    with pytest.raises(RenderingError, match=r"\[slides\.density\.unsupported-raw-geometry\]") as exc_info:
        compose_accessible_pandoc_document(
            _document(_formal_raw(f"Admitted math ${translation}$ must fail.")),
            policy=AccessibleSlidePolicy(),
            source="manuscript/security.md",
        )

    assert exc_info.value.context["unsupported_command"] == "tex-lexical-translation"


def test_single_caret_math_and_allowlisted_references_remain_admitted() -> None:
    raw = _formal_raw(r"For $x^2 \ge 0$, see \ref{eq:bound}.")

    result = compose_accessible_pandoc_document(
        _document(raw),
        policy=AccessibleSlidePolicy(),
        source="manuscript/security.md",
    )

    raw_blocks = [block for block in result.document["blocks"] if block.get("t") == "RawBlock"]
    assert raw_blocks[0] == raw
    assert raw_blocks[1]["c"][0] == "html"


def test_tex_lexical_translation_in_ordinary_pandoc_math_is_rejected() -> None:
    paragraph = {
        "t": "Para",
        "c": [
            {"t": "Str", "c": "Unsafe"},
            {"t": "Space"},
            {"t": "Math", "c": [{"t": "InlineMath"}, "^^5cinput{canary}"]},
        ],
    }

    with pytest.raises(RenderingError, match=r"\[slides\.density\.unsupported-math-geometry\]") as exc_info:
        compose_accessible_pandoc_document(
            _document(paragraph),
            policy=AccessibleSlidePolicy(),
            source="manuscript/security.md",
        )

    assert exc_info.value.context["unsupported_commands"] == ["tex-lexical-translation"]


@pytest.mark.parametrize("node_type", ("RawInline", "Math"))
def test_writer_visible_metadata_receives_complete_tex_preflight(node_type: str) -> None:
    node = (
        {"t": "RawInline", "c": ["latex", "^^5cinput{canary}"]}
        if node_type == "RawInline"
        else {"t": "Math", "c": [{"t": "InlineMath"}, "^^5cinput{canary}"]}
    )
    document = _document({"t": "Para", "c": [{"t": "Str", "c": "Body"}]})
    document["meta"] = {"title": {"t": "MetaInlines", "c": [node]}}

    with pytest.raises(RenderingError) as exc_info:
        compose_accessible_pandoc_document(
            document,
            policy=AccessibleSlidePolicy(),
            source="manuscript/security.md",
        )

    assert "tex-lexical-translation" in str(exc_info.value.context)


@pytest.mark.parametrize("translation", ("^^5cinput{canary}", "^^^^005cinput{canary}", "^^Mcanary"))
def test_accessible_preamble_rejects_tex_translation_before_header_write(
    tmp_path: Path,
    translation: str,
) -> None:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "preamble.md").write_text(
        f"```latex\n\\usepackage{{amsmath}}\n{translation}\n```\n",
        encoding="utf-8",
    )
    output = tmp_path / "slides"

    with pytest.raises(RenderingError, match=r"\[slides\.security\.tex-lexical-translation\]"):
        write_slides_math_header(manuscript, output, accessible_policy=AccessibleSlidePolicy())

    assert not (output / "_slides_math_header.tex").exists()


def test_untrusted_archive_source_rejects_tex_translation(tmp_path: Path) -> None:
    source = tmp_path / "slides.md"
    source.write_text("Archive payload ^^5cinput{canary}\n", encoding="utf-8")

    with pytest.raises(RenderingError, match="file or command inclusion"):
        RenderSecurityProfile(name="untrusted", temp_root=tmp_path).validate_source(source)


def test_unmatched_math_openers_are_scanned_once_and_remain_unadmitted() -> None:
    source = r"\[" * 20_000

    assert _math_fragments(source) == ()


def test_accessible_ast_depth_limit_precedes_recursive_projection() -> None:
    nested: object = {"t": "Str", "c": "leaf"}
    for _ in range(MAX_ACCESSIBLE_PANDOC_AST_DEPTH + 1):
        nested = [{"t": "Span", "c": [["", [], []], [nested]]}]
    document = {"blocks": nested}

    with pytest.raises(RenderingError, match=r"\[slides\.schema\.pandoc-limits\]") as exc_info:
        validate_accessible_ast_limits(document, source="manuscript/deep.md")

    assert exc_info.value.context["maximum_depth"] == MAX_ACCESSIBLE_PANDOC_AST_DEPTH


def test_accessible_ast_node_limit_bounds_writer_fallback_allocation() -> None:
    document = {"blocks": [None] * MAX_ACCESSIBLE_PANDOC_AST_NODES}

    with pytest.raises(RenderingError, match=r"\[slides\.schema\.pandoc-limits\]") as exc_info:
        validate_accessible_ast_limits(document, source="manuscript/wide.md")

    assert exc_info.value.context["maximum_nodes"] == MAX_ACCESSIBLE_PANDOC_AST_NODES


def test_writer_fallback_reconstructs_nested_content_without_losing_inline_peer() -> None:
    value: object = {"t": "RawInline", "c": ["tex", r"\ref{eq:bound}"]}
    for _ in range(48):
        value = {"t": "Span", "c": [["", [], []], [value]]}

    projected = _with_inline_writer_fallbacks(value)
    cursor = projected
    for _ in range(48):
        assert isinstance(cursor, dict) and cursor["t"] == "Span"
        cursor = cursor["c"][1][0]
    assert cursor == {"t": "RawInline", "c": ["tex", r"\ref{eq:bound}"]}
    assert projected != value


def test_absolute_and_encoded_absolute_rasters_are_rejected_before_inspection(tmp_path: Path) -> None:
    manuscript = tmp_path / "project" / "manuscript"
    manuscript.mkdir(parents=True)
    outside = tmp_path / "outside.png"
    Image.new("RGB", (13, 17), "white").save(outside)

    for target in (str(outside), quote(str(outside), safe="")):
        with pytest.raises(RenderingError, match=r"\[slides\.security\.figure-path\]") as exc_info:
            compose_accessible_pandoc_document(
                _document(_figure(target)),
                policy=AccessibleSlidePolicy(),
                source=str(manuscript / "results.md"),
            )
        assert "absolute" in str(exc_info.value)


@pytest.mark.parametrize("container", ("header", "metadata"))
def test_non_figure_writer_images_receive_path_confinement(tmp_path: Path, container: str) -> None:
    outside = tmp_path / "outside.png"
    Image.new("RGB", (13, 17), "white").save(outside)
    document = _document({"t": "Para", "c": [{"t": "Str", "c": "Body"}]})
    image = _figure(str(outside))["c"][2][0]["c"][0]
    if container == "header":
        document["blocks"][0]["c"][2] = [image]
    else:
        document["meta"] = {"title": {"t": "MetaInlines", "c": [image]}}

    with pytest.raises(RenderingError, match=r"\[slides\.security\.figure-path\]"):
        compose_accessible_pandoc_document(
            document,
            policy=AccessibleSlidePolicy(),
            source=str(tmp_path / "manuscript" / "results.md"),
        )


@pytest.mark.parametrize("target", ("../../outside.png", "%2e%2e/%2e%2e/outside.png"))
def test_traversal_outside_every_authorized_root_is_rejected(tmp_path: Path, target: str) -> None:
    manuscript = tmp_path / "project" / "manuscript"
    manuscript.mkdir(parents=True)

    with pytest.raises(RenderingError, match=r"\[slides\.security\.figure-path\]") as exc_info:
        compose_accessible_pandoc_document(
            _document(_figure(target)),
            policy=AccessibleSlidePolicy(),
            source=str(manuscript / "results.md"),
            authorized_image_roots=(manuscript,),
        )

    assert "escapes every authorized image root" in str(exc_info.value)


@pytest.mark.parametrize("link_kind", ("directory", "file"))
def test_every_symlink_component_is_rejected_before_pillow(tmp_path: Path, link_kind: str) -> None:
    manuscript = tmp_path / "project" / "manuscript"
    outside = tmp_path / "outside"
    manuscript.mkdir(parents=True)
    outside.mkdir()
    image = outside / "canary.png"
    Image.new("RGB", (13, 17), "white").save(image)
    try:
        if link_kind == "directory":
            (manuscript / "linked").symlink_to(outside, target_is_directory=True)
            target = "linked/canary.png"
        else:
            (manuscript / "linked.png").symlink_to(image)
            target = "linked.png"
    except OSError as exc:
        pytest.skip(f"symlink creation is unavailable: {exc}")

    with pytest.raises(RenderingError, match=r"\[slides\.security\.figure-path\]") as exc_info:
        compose_accessible_pandoc_document(
            _document(_figure(target)),
            policy=AccessibleSlidePolicy(),
            source=str(manuscript / "results.md"),
            authorized_image_roots=(manuscript,),
        )

    assert "symlink component" in str(exc_info.value)


def test_configured_sibling_figure_root_preserves_normal_project_layout(tmp_path: Path) -> None:
    manuscript = tmp_path / "project" / "manuscript"
    figures = tmp_path / "project" / "output" / "figures"
    manuscript.mkdir(parents=True)
    figures.mkdir(parents=True)
    Image.new("RGB", (240, 600), "white").save(figures / "portrait.png")

    result = compose_accessible_pandoc_document(
        _document(_figure("../output/figures/portrait.png")),
        policy=AccessibleSlidePolicy(),
        source=str(manuscript / "results.md"),
        authorized_image_roots=(figures,),
    )

    text = str(result.document)
    assert "data-slide-figure-intrinsic-status" in text
    assert "validated" in text
    assert "portrait.png" in text


def test_hydrated_source_preserves_authored_output_figure_alias(tmp_path: Path) -> None:
    project = tmp_path / "project"
    hydrated = project / "output" / "manuscript"
    figures = project / "output" / "figures"
    authored = project / "manuscript"
    hydrated.mkdir(parents=True)
    figures.mkdir(parents=True)
    authored.mkdir()
    Image.new("RGB", (320, 180), "white").save(figures / "descent_comparison.png")

    result = compose_accessible_pandoc_document(
        _document(_figure("../output/figures/descent_comparison.png")),
        policy=AccessibleSlidePolicy(),
        source=str(hydrated / "27_supplement.md"),
        authorized_image_roots=(hydrated, authored, figures),
        figure_image_root=figures,
    )

    assert "data-slide-figure-intrinsic-status" in str(result.document)
    assert "validated" in str(result.document)


def test_explicit_figure_alias_uses_figure_root_not_same_named_source_file(tmp_path: Path) -> None:
    hydrated = tmp_path / "output" / "manuscript"
    figures = tmp_path / "output" / "figures"
    hydrated.mkdir(parents=True)
    figures.mkdir(parents=True)
    Image.new("RGB", (13, 17), "white").save(hydrated / "selected.png")
    Image.new("RGB", (320, 180), "white").save(figures / "selected.png")

    result = compose_accessible_pandoc_document(
        _document(_figure("../output/figures/selected.png")),
        policy=AccessibleSlidePolicy(),
        source=str(hydrated / "results.md"),
        authorized_image_roots=(hydrated, figures),
        figure_image_root=figures,
    )

    assert "['data-slide-figure-intrinsic-width', '320']" in str(result.document)
    assert "['data-slide-figure-intrinsic-height', '180']" in str(result.document)


def test_protocol_relative_remote_image_remains_nonlocal() -> None:
    result = compose_accessible_pandoc_document(
        _document(_figure("//cdn.example.invalid/figure.png")),
        policy=AccessibleSlidePolicy(),
        source="manuscript/results.md",
        authorized_image_roots=(Path("manuscript"),),
    )

    assert "data-slide-figure-intrinsic-status', 'unresolved" in str(result.document)


@pytest.mark.parametrize("target", ("file:///tmp/figure.png", "file://localhost/tmp/figure.png"))
def test_local_file_urls_are_rejected_even_when_they_have_an_authority(target: str) -> None:
    with pytest.raises(RenderingError, match=r"\[slides\.security\.figure-path\]") as exc_info:
        compose_accessible_pandoc_document(
            _document(_figure(target)),
            policy=AccessibleSlidePolicy(),
            source="manuscript/results.md",
            authorized_image_roots=(Path("manuscript"),),
        )

    assert "local figure URLs are forbidden" in str(exc_info.value)


def test_encoded_fragment_and_query_characters_remain_local_filename_data(tmp_path: Path) -> None:
    figures = tmp_path / "figures"
    figures.mkdir()
    Image.new("RGB", (31, 19), "white").save(figures / "figure#part?.png")

    result = compose_accessible_pandoc_document(
        _document(_figure("figure%23part%3F.png")),
        policy=AccessibleSlidePolicy(),
        source=str(tmp_path / "manuscript" / "results.md"),
        authorized_image_roots=(figures,),
    )

    assert "['data-slide-figure-intrinsic-width', '31']" in str(result.document)


@pytest.mark.parametrize("target", (r"C:\\outside.png", r"..\\..\\outside.png", r"\\server\\share\\x.png"))
def test_windows_absolute_unc_and_backslash_traversal_are_rejected(tmp_path: Path, target: str) -> None:
    with pytest.raises(RenderingError, match=r"\[slides\.security\.figure-path\]"):
        compose_accessible_pandoc_document(
            _document(_figure(target)),
            policy=AccessibleSlidePolicy(),
            source=str(tmp_path / "manuscript" / "results.md"),
            authorized_image_roots=(tmp_path / "manuscript",),
        )


def test_declared_lifecycle_symlink_root_is_canonicalized_once(tmp_path: Path) -> None:
    real_figures = tmp_path / "private" / "output" / "figures"
    real_figures.mkdir(parents=True)
    Image.new("RGB", (320, 180), "white").save(real_figures / "figure.png")
    declared = tmp_path / "workspace-figures"
    try:
        declared.symlink_to(real_figures, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlink creation is unavailable: {exc}")

    result = compose_accessible_pandoc_document(
        _document(_figure("figure.png")),
        policy=AccessibleSlidePolicy(),
        source=str(tmp_path / "hydrated" / "results.md"),
        authorized_image_roots=(declared,),
    )

    assert "data-slide-figure-intrinsic-status" in str(result.document)
    assert "validated" in str(result.document)


def test_intrinsic_image_metadata_read_is_byte_bounded(tmp_path: Path) -> None:
    manuscript = tmp_path / "project" / "manuscript"
    figures = tmp_path / "project" / "output" / "figures"
    manuscript.mkdir(parents=True)
    figures.mkdir(parents=True)
    oversized = figures / "oversized.png"
    with oversized.open("wb") as handle:
        handle.truncate(MAX_INTRINSIC_IMAGE_BYTES + 1)

    with pytest.raises(RenderingError, match=r"\[slides\.security\.figure-resource\]") as exc_info:
        compose_accessible_pandoc_document(
            _document(_figure("../output/figures/oversized.png")),
            policy=AccessibleSlidePolicy(),
            source=str(manuscript / "results.md"),
            authorized_image_roots=(figures,),
        )

    assert exc_info.value.context["maximum_bytes"] == MAX_INTRINSIC_IMAGE_BYTES


def test_intrinsic_image_declared_pixel_area_is_bounded_before_decode(tmp_path: Path) -> None:
    figures = tmp_path / "figures"
    figures.mkdir()
    oversized = figures / "oversized.png"
    side = int(MAX_INTRINSIC_IMAGE_PIXELS**0.5) + 1
    _png_with_declared_size(oversized, side, side)

    with pytest.raises(RenderingError, match=r"\[slides\.security\.figure-resource\]") as exc_info:
        compose_accessible_pandoc_document(
            _document(_figure("oversized.png")),
            policy=AccessibleSlidePolicy(),
            source=str(tmp_path / "manuscript" / "results.md"),
            authorized_image_roots=(figures,),
        )

    assert exc_info.value.context["maximum_pixels"] == MAX_INTRINSIC_IMAGE_PIXELS
