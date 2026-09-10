"""EPUB accessibility regressions for packaged images and SVG covers."""

from __future__ import annotations
from pathlib import Path
import pytest
from infrastructure.validation.output.render_formats import validate_enabled_render_outputs
from tests.infra_tests.validation._render_formats_helpers import _write_epub


@pytest.mark.parametrize("alt_attribute", ["", ' alt=""'])
def test_enabled_epub_rejects_missing_or_blank_non_decorative_image_alt(
    tmp_path: Path,
    alt_attribute: str,
) -> None:
    """Packaged XHTML images require explicit, non-blank accessibility text."""

    output_dir = tmp_path / "output"
    _write_epub(
        output_dir / "epub" / "demo_combined.epub",
        xhtml=(
            '<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Chapter</title></head>'
            f'<body><img src="../images/figure.png"{alt_attribute}/></body></html>'
        ),
        extra_manifest_item='<item id="figure" href="images/figure.png" media-type="image/png"/>',
        extra_members={"EPUB/images/figure.png": b"real-image-payload"},
    )

    assert validate_enabled_render_outputs(output_dir, "demo", {"epub"}) is False


def test_enabled_epub_rejects_pandoc_svg_cover_without_accessible_name(tmp_path: Path) -> None:
    """Regression: Pandoc's raw SVG cover shape cannot ship without config alt."""

    output_dir = tmp_path / "output"
    _write_epub(
        output_dir / "epub" / "demo_combined.epub",
        xhtml=(
            '<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Cover</title></head><body>'
            '<svg xmlns="http://www.w3.org/2000/svg" '
            'xmlns:xlink="http://www.w3.org/1999/xlink">'
            '<image xlink:href="../images/cover.png"/></svg></body></html>'
        ),
        extra_manifest_item=(
            '<item id="cover" href="images/cover.png" media-type="image/png" properties="cover-image"/>'
        ),
        extra_members={"EPUB/images/cover.png": b"real-cover-payload"},
    )

    assert validate_enabled_render_outputs(output_dir, "demo", {"epub"}) is False


def test_enabled_epub_accepts_named_svg_cover_with_hidden_bitmap_primitive(tmp_path: Path) -> None:
    """The cover SVG is one named graphic; its bitmap primitive is not re-announced."""

    output_dir = tmp_path / "output"
    _write_epub(
        output_dir / "epub" / "demo_combined.epub",
        xhtml=(
            '<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Cover</title></head><body>'
            '<svg xmlns="http://www.w3.org/2000/svg" '
            'xmlns:xlink="http://www.w3.org/1999/xlink" role="img" aria-labelledby="cover-title">'
            '<title id="cover-title">A meaningful cover description.</title>'
            '<image xlink:href="../images/cover.png" aria-hidden="true" focusable="false"/>'
            "</svg></body></html>"
        ),
        extra_manifest_item=(
            '<item id="cover" href="images/cover.png" media-type="image/png" properties="cover-image"/>'
        ),
        extra_members={"EPUB/images/cover.png": b"real-cover-payload"},
    )

    assert validate_enabled_render_outputs(output_dir, "demo", {"epub"}) is True
