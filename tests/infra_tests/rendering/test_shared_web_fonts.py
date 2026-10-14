"""Real shared Source font publication, confinement, and byte-budget checks."""

from __future__ import annotations

import base64
import gzip
import hashlib
import json
from pathlib import Path

import pytest

from infrastructure.rendering._shared_web_fonts import SOURCE_WEB_FONT_ASSET, shared_web_font_script
from infrastructure.rendering._web_assets import embed_css
from infrastructure.rendering._web_font_assets import (
    FONT_BODIES,
    FONT_BUFFER_SCHEMA,
    LICENSE_SHA256,
    source_web_font_bundle,
    source_web_font_directory,
    source_web_font_javascript,
    source_web_font_script,
)


def test_shared_asset_retains_all_exact_font_bodies_and_full_license(tmp_path: Path) -> None:
    shared_web_font_script(tmp_path)
    script = (tmp_path / SOURCE_WEB_FONT_ASSET).read_text()
    payload, _ = json.JSONDecoder().raw_decode(script.split("node.textContent=JSON.stringify(", 1)[1])
    assert len(payload["faces"]) == len(FONT_BODIES) == 12
    assert payload["license"].encode() == (source_web_font_directory() / "OFL.txt").read_bytes()
    assert hashlib.sha256(payload["license"].encode()).hexdigest() == LICENSE_SHA256
    for face in payload["faces"]:
        original = FONT_BODIES[face["postscript_name"]]
        assert face["encoding"] == "gzip-base64"
        packed = base64.b64decode(face["data"], validate=True)
        assert packed[4:8] == b"\0\0\0\0"  # No build-time gzip timestamp.
        assert packed[9] == 255  # No platform-dependent gzip OS marker.
        body = gzip.decompress(packed)
        assert body == (source_web_font_directory() / original["filename"]).read_bytes()
        assert len(body) == face["bytes"] == original["bytes"]
        assert hashlib.sha256(body).hexdigest() == face["sha256"] == original["sha256"]
        assert face["schema_version"] == FONT_BUFFER_SCHEMA
        assert all(face[key] == original[key] for key in ("family", "style", "weight"))
    inline = source_web_font_script()
    loader = inline.split("<script data-template-source-font-loader>\n", 1)[1].removesuffix("</script>\n")
    assert script.endswith(loader)


def test_shared_transport_is_deterministic_and_preserves_raw_bundle_api() -> None:
    first = source_web_font_javascript()
    assert source_web_font_javascript() == first
    # Ten canonical web exports must fit the existing aggregate evidence budget.
    assert len(first.encode()) < 3_200_000
    assert len(first.encode()) < 0.6 * len(source_web_font_script().encode())
    raw_faces, _ = source_web_font_bundle()
    inline = source_web_font_script().split('id="template-source-font-bodies">', 1)[1].split("</script>", 1)[0]
    assert json.loads(inline)["faces"] == raw_faces
    for face in raw_faces:
        assert "encoding" not in face
        assert (
            base64.b64decode(face["data"], validate=True)
            == (source_web_font_directory() / FONT_BODIES[face["postscript_name"]]["filename"]).read_bytes()
        )


def test_multiple_real_html_pages_share_one_idempotent_bounded_asset(tmp_path: Path) -> None:
    css = tmp_path / "style.css"
    css.write_text("body { color: black; }")
    pages = [tmp_path / f"section-{index}.html" for index in range(3)]
    authored = '<script>window.authoredValue="Preserved";</script>'
    old_inline = source_web_font_script()
    for index, page in enumerate(pages):
        legacy_fonts = old_inline if index == 0 else ""
        page.write_text("<html><head>" + authored + legacy_fonts + "</head><body>Readable publication.</body></html>")
        embed_css(page, css)
        text = page.read_text()
        assert f'src="{SOURCE_WEB_FONT_ASSET}"' in text
        assert "template-source-font-bodies" not in text
        assert "Readable publication." in text
        assert authored in text
        assert text.count("data-template-source-font-loader") == 1
        assert old_inline not in text
    asset = tmp_path / SOURCE_WEB_FONT_ASSET
    before = asset.stat()
    shared_web_font_script(tmp_path)
    assert (asset.stat().st_ino, asset.stat().st_mtime_ns) == (before.st_ino, before.st_mtime_ns)
    assert list((tmp_path / "assets").iterdir()) == [asset]
    embed_css(pages[0], css)
    assert pages[0].read_text().count("data-template-source-font-loader src=") == 1
    shared_bytes = asset.stat().st_size + sum(page.stat().st_size for page in pages)
    assert shared_bytes < 2 * len(source_web_font_script().encode())


@pytest.mark.parametrize("redirect", ["asset", "assets-directory", "output-directory", "ancestor"])
def test_shared_asset_refuses_actual_symlinks_without_writing_outside(tmp_path: Path, redirect: str) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "sentinel.js"
    sentinel.write_text("Human-owned content")
    output = tmp_path / "output"
    output.mkdir()
    if redirect == "asset":
        (output / "assets").mkdir()
        (output / SOURCE_WEB_FONT_ASSET).symlink_to(sentinel)
    elif redirect == "assets-directory":
        (output / "assets").symlink_to(outside, target_is_directory=True)
    elif redirect == "output-directory":
        output = tmp_path / "linked-output"
        output.symlink_to(outside, target_is_directory=True)
    else:
        (outside / "real-output").mkdir()
        link = tmp_path / "linked-parent"
        link.symlink_to(outside, target_is_directory=True)
        output = link / "real-output"
    with pytest.raises(ValueError):
        shared_web_font_script(output)
    assert sentinel.read_text() == "Human-owned content"
    assert not (outside / "assets").exists()
