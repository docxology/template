"""Tests for modular manuscript rendering cache."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from infrastructure.rendering.render_cache import ManuscriptRenderCache, RenderCacheError


def test_render_cache_lifecycle(tmp_path: Path) -> None:
    cache_file = tmp_path / ".render_cache.json"
    cache = ManuscriptRenderCache(cache_file)

    src = tmp_path / "01_intro.md"
    src.write_text("# Intro\nContent here.\n", encoding="utf-8")

    out1 = tmp_path / "01_intro.html"
    out1.write_text("<p>Intro</p>\n", encoding="utf-8")
    out2 = tmp_path / "01_intro_slides.pdf"
    out2.write_text("%PDF-1.4\n", encoding="utf-8")

    # Initially not up to date
    assert not cache.is_up_to_date(src, [out1, out2])

    # Record rendered
    cache.record_rendered(src, [out1, out2])

    # Now up to date
    assert cache.is_up_to_date(src, [out1, out2])
    assert cache._entries[src.name].timestamp > 0

    # Modifying source invalidates cache
    src.write_text("# Intro modified\n", encoding="utf-8")
    assert not cache.is_up_to_date(src, [out1, out2])

    # Re-recording updates cache
    cache.record_rendered(src, [out1, out2])
    assert cache.is_up_to_date(src, [out1, out2])

    # Missing output invalidates cache
    out1.unlink()
    assert not cache.is_up_to_date(src, [out1, out2])


def test_render_cache_clear(tmp_path: Path) -> None:
    cache_file = tmp_path / ".render_cache.json"
    cache = ManuscriptRenderCache(cache_file)

    src = tmp_path / "02_methods.md"
    src.write_text("# Methods\n", encoding="utf-8")
    out = tmp_path / "02_methods.html"
    out.write_text("<p>Methods</p>\n", encoding="utf-8")

    cache.record_rendered(src, [out])
    assert cache_file.exists()

    cache.clear()
    assert not cache_file.exists()
    assert not cache.is_up_to_date(src, [out])


def test_render_cache_distinguishes_same_named_sections(tmp_path: Path) -> None:
    cache = ManuscriptRenderCache(tmp_path / ".render_cache.json")
    src_a = tmp_path / "part_a" / "section.md"
    src_b = tmp_path / "part_b" / "section.md"
    src_a.parent.mkdir()
    src_b.parent.mkdir()
    src_a.write_text("A\n", encoding="utf-8")
    src_b.write_text("B\n", encoding="utf-8")
    out_a = tmp_path / "part_a" / "section.html"
    out_b = tmp_path / "part_b" / "section.html"
    out_a.write_text("A\n", encoding="utf-8")
    out_b.write_text("B\n", encoding="utf-8")

    cache.record_rendered(src_a, [out_a])
    assert cache.is_up_to_date(src_a, [out_a])
    assert not cache.is_up_to_date(src_b, [out_b])

    cache.record_rendered(src_b, [out_b])
    assert cache.is_up_to_date(src_a, [out_a])
    assert cache.is_up_to_date(src_b, [out_b])


def test_render_cache_requires_exact_files_and_outputs(tmp_path: Path) -> None:
    cache = ManuscriptRenderCache(tmp_path / ".render_cache.json")
    src = tmp_path / "section.md"
    src.write_text("content\n", encoding="utf-8")
    out = tmp_path / "section.html"
    out.write_text("rendered\n", encoding="utf-8")

    cache.record_rendered(src, [out])
    assert not cache.is_up_to_date(src, [])
    out.unlink()
    out.mkdir()
    assert not cache.is_up_to_date(src, [out])


def test_render_cache_rejects_corrupt_state(tmp_path: Path) -> None:
    cache_file = tmp_path / ".render_cache.json"
    cache_file.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(RenderCacheError, match="Invalid render cache JSON"):
        ManuscriptRenderCache(cache_file)


def test_render_cache_rejects_malformed_entry(tmp_path: Path) -> None:
    cache_file = tmp_path / ".render_cache.json"
    cache_file.write_text(
        json.dumps({"schema_version": 1, "entries": [{"file_name": "section.md"}]}),
        encoding="utf-8",
    )

    with pytest.raises(RenderCacheError, match="invalid content hash"):
        ManuscriptRenderCache(cache_file)


def test_render_cache_rejects_non_hex_content_hash(tmp_path: Path) -> None:
    cache_file = tmp_path / ".render_cache.json"
    cache_file.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "entries": [
                    {
                        "file_name": "section.md",
                        "content_hash": "z" * 64,
                        "rendered_outputs": [],
                        "timestamp": 1.0,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(RenderCacheError, match="invalid content hash"):
        ManuscriptRenderCache(cache_file)


def test_render_cache_save_failure_is_reported(tmp_path: Path) -> None:
    parent = tmp_path / "cache-parent"
    parent.write_text("not a directory", encoding="utf-8")
    cache = ManuscriptRenderCache(parent / "cache.json")

    with pytest.raises(RenderCacheError, match="Could not save render cache"):
        cache.save()
