"""Real shared Source font publication, confinement, and byte-budget checks."""

from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import lzma
from pathlib import Path

import pytest
from infrastructure.rendering._shared_web_fonts import SOURCE_WEB_FONT_ASSET, shared_web_font_script
from infrastructure.rendering._web_assets import embed_css
from infrastructure.rendering._web_font_assets import (
    FONT_BODIES,
    FONT_BUFFER_SCHEMA,
    LICENSE_SHA256,
    LZMA_DECODER_SHA256,
    LZMA_LICENSE_SHA256,
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
    stream = payload["stream"]
    assert stream["encoding"] == "lzma-alone-base64-v1"
    packed = base64.b64decode(stream["data"], validate=True)
    expected = sum(face["bytes"] for face in payload["faces"])
    assert 0 < expected == stream["bytes"] <= 6 * 1024 * 1024
    assert 13 <= len(packed) <= 4 * 1024 * 1024
    assert packed[:5] == b"\x5d\x00\x00\x80\x00"  # Fixed properties and 8-MiB dictionary.
    assert int.from_bytes(packed[5:13], "little") == expected  # No unknown/unbounded output header.
    decoded = lzma.decompress(packed, format=lzma.FORMAT_ALONE)
    assert len(decoded) == expected
    offset = 0
    for face in payload["faces"]:
        original = FONT_BODIES[face["postscript_name"]]
        assert "data" not in face and "encoding" not in face
        body = decoded[offset : offset + face["bytes"]]
        offset += face["bytes"]
        assert body == (source_web_font_directory() / original["filename"]).read_bytes()
        assert len(body) == face["bytes"] == original["bytes"]
        assert hashlib.sha256(body).hexdigest() == face["sha256"] == original["sha256"]
        assert face["schema_version"] == FONT_BUFFER_SCHEMA
        assert all(face[key] == original[key] for key in ("family", "style", "weight"))
    assert offset == len(decoded)
    assets = source_web_font_directory().parent
    assert hashlib.sha256((assets / "lzma-d-min.js").read_bytes()).hexdigest() == LZMA_DECODER_SHA256
    mit = (assets / "LZMA-JS-LICENSE.txt").read_bytes()
    assert hashlib.sha256(mit).hexdigest() == LZMA_LICENSE_SHA256 and mit.decode() in script
    inline = source_web_font_script()
    loader = inline.split("<script data-template-source-font-loader>\n", 1)[1].removesuffix("</script>\n")
    assert script.endswith(loader)

    # A genuine module/assets copy exercises physical reads even after its pure compression cache is populated.
    from infrastructure.rendering import _web_font_assets

    copied = tmp_path / "source-copy"
    copied.mkdir()
    copied_module = copied / "_web_font_assets.py"
    copied_module.write_bytes(Path(_web_font_assets.__file__).read_bytes())
    copied_assets = copied / "assets/fonts"
    (copied_assets / "liberation").mkdir(parents=True)
    for relative in [
        *("liberation/" + face["filename"] for face in FONT_BODIES.values()),
        "liberation/OFL.txt",
        "lzma-d-min.js",
        "LZMA-JS-LICENSE.txt",
    ]:
        (copied_assets / relative).write_bytes((assets / relative).read_bytes())
    spec = importlib.util.spec_from_file_location("real_source_font_copy", copied_module)
    assert spec is not None and spec.loader is not None
    actual = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(actual)
    assert actual.source_web_font_javascript() == script
    for relative, diagnostic in [
        ("liberation/LiberationMono-Regular.ttf", "exact nomination"),
        ("lzma-d-min.js", "transport decoder/license"),
        ("LZMA-JS-LICENSE.txt", "transport decoder/license"),
    ]:
        path = copied_assets / relative
        before = path.read_bytes()
        path.write_bytes(bytes([before[0] ^ 1]) + before[1:])
        with pytest.raises(ValueError, match=diagnostic):
            actual.source_web_font_javascript()
        path.write_bytes(before)


def test_shared_transport_is_deterministic_and_preserves_raw_bundle_api() -> None:
    first = source_web_font_javascript()
    assert source_web_font_javascript() == first
    # Each of 25 font-only cohorts stays below 2 MB (<50 MB total); whole-publication acceptance is separate.
    assert len(first.encode()) < 2_000_000
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
