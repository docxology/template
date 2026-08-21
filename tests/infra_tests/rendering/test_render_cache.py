"""Tests for modular manuscript rendering cache."""

from __future__ import annotations

from pathlib import Path

from infrastructure.rendering.render_cache import ManuscriptRenderCache


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
