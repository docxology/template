"""Tests for the EPUB XHTML well-formedness sanitizer.

Raw HTML in source markdown passes through Pandoc's writers verbatim and can
leave individual EPUB chapter documents not well-formed XML. Each documented
failure shape is repaired here: unclosed void/inline tags, stray ``<`` in text,
mismatched close tags, ``--`` sequences inside comments, and unrepresentable
control characters. Members that already parse are preserved byte-for-byte.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import defusedxml.ElementTree as safe_et

from infrastructure.rendering._epub_xhtml_sanitizer import (
    _repair_xhtml_bytes,
    sanitize_epub_xhtml,
)
from ._ebook_fallbacks_helpers import needs_pandoc
from infrastructure.rendering._epub_package_validation import validate_epub_package
from infrastructure.rendering.epub_renderer import render_epub

_XHTML_NS = "http://www.w3.org/1999/xhtml"


def _chapter(body: str) -> str:
    """Return a Pandoc-shaped XHTML chapter with *body* inserted."""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<!DOCTYPE html>\n"
        f'<html xmlns="{_XHTML_NS}" xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en">\n'
        "<head>\n<title>c</title>\n</head>\n"
        '<body epub:type="bodymatter">\n'
        f"{body}\n"
        "</body>\n</html>\n"
    )


def _write_epub(path: Path, members: dict[str, str | bytes]) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip")
        for name, payload in members.items():
            archive.writestr(name, payload)


def _parses(payload: bytes) -> bool:
    try:
        safe_et.fromstring(payload)
        return True
    except Exception:
        return False


class TestRepairShapes:
    """One test per raw-HTML failure shape observed in real manuscripts."""

    def test_unclosed_void_inline_tag_is_self_closed(self) -> None:
        """Raw ``<br>`` (ntqr_llm ch007) becomes XHTML ``<br />`` and parses."""
        raw = _chapter("<p>Line one<br>Line two<br><br>Line three</p>").encode()
        fixed = _repair_xhtml_bytes(raw)
        assert fixed is not None
        assert _parses(fixed)
        assert fixed.count(b"<br />") == 3
        assert b"<br>" not in fixed

    def test_stray_less_than_in_text_is_escaped(self) -> None:
        """A stray ``<`` in prose is escaped and the text survives."""
        raw = _chapter("<p>Density 5 &lt; 7 but 5 < 7 written raw</p>").encode()
        fixed = _repair_xhtml_bytes(raw)
        assert fixed is not None
        assert _parses(fixed)
        assert b"5 &lt; 7 written raw" in fixed

    def test_mismatched_close_tags_are_balanced(self) -> None:
        """Realizing-emptiness ch001: raw ``<img ...></figure>`` after an open
        ``<figure>`` becomes well-formed with the void image self-closed."""
        raw = _chapter(
            '<figure class="graphical-abstract"><img alt="abstract" src="../images/cover.png"></figure>'
        ).encode()
        fixed = _repair_xhtml_bytes(raw)
        assert fixed is not None
        assert _parses(fixed)
        assert b"<img " in fixed and fixed.count(b"/>") == 1
        assert b"</figure>" in fixed

    def test_unbalanced_inline_markup_is_closed_at_the_right_place(self) -> None:
        """A close tag matching an outer open element closes the inner ones."""
        raw = _chapter("<p><em><strong>text</p>").encode()
        fixed = _repair_xhtml_bytes(raw)
        assert fixed is not None
        assert _parses(fixed)
        assert b"<p><em><strong>text</strong></em></p>" in fixed

    def test_double_hyphen_inside_comment_is_repaired(self) -> None:
        """Thalia ch017: ``--citeproc`` inside an HTML comment breaks XML."""
        raw = _chapter("<!-- References are resolved by Pandoc --citeproc -->").encode()
        fixed = _repair_xhtml_bytes(raw)
        assert fixed is not None
        assert _parses(fixed)
        assert b"<!-- References are resolved by Pandoc - -citeproc -->" in fixed

    def test_hyphen_run_inside_comment_is_repaired(self) -> None:
        """Biology ch110: ``---`` inside a comment has overlapping ``--`` runs."""
        raw = _chapter("<!-- fall in a gray zone --- they evolve -->").encode()
        fixed = _repair_xhtml_bytes(raw)
        assert fixed is not None
        assert _parses(fixed)
        assert b"zone - - they evolve" in fixed

    def test_control_character_in_comment_is_dropped(self) -> None:
        """Biology ch112: a raw BEL byte inside a comment is unrepresentable."""
        raw = _chapter("<!-- answer 1.082\x07pprox +67 mV -->").encode()
        fixed = _repair_xhtml_bytes(raw)
        assert fixed is not None
        assert _parses(fixed)
        assert b"\x07" not in fixed
        assert b"1.082pprox" in fixed

    def test_control_character_in_text_is_dropped(self) -> None:
        """A raw BEL byte in visible text is dropped so the member parses."""
        raw = _chapter("<p>value 1.082\x07pprox +67</p>").encode()
        fixed = _repair_xhtml_bytes(raw)
        assert fixed is not None
        assert _parses(fixed)
        assert b"\x07" not in fixed


class TestNoOpAndScope:
    def test_well_formed_member_is_byte_identical(self) -> None:
        """A member that already parses is not rewritten at all."""
        raw = _chapter("<p>Clean <strong>markup</strong> with<br />a break.</p>").encode()
        assert _repair_xhtml_bytes(raw) is None

    def test_sanitize_epub_rewrites_only_damaged_members(self, tmp_path: Path) -> None:
        """Only the malformed member is replaced; the clean one is untouched."""
        clean = _chapter("<p>clean</p>").encode()
        damaged = _chapter("<p>broken<br>tag</p>").encode()
        epub = tmp_path / "book.epub"
        _write_epub(epub, {"EPUB/text/ch001.xhtml": clean, "EPUB/text/ch002.xhtml": damaged})
        before = epub.read_bytes()
        repaired = sanitize_epub_xhtml(epub)
        assert repaired == ["EPUB/text/ch002.xhtml"]
        with zipfile.ZipFile(epub) as archive:
            assert archive.read("EPUB/text/ch001.xhtml") == clean
            assert _parses(archive.read("EPUB/text/ch002.xhtml"))
        # A second pass is a byte-for-byte no-op.
        after_first = epub.read_bytes()
        assert sanitize_epub_xhtml(epub) == []
        assert epub.read_bytes() == after_first
        assert before != after_first

    def test_clean_epub_is_not_rewritten(self, tmp_path: Path) -> None:
        """A package with no damage is not touched at all (byte-for-byte)."""
        clean = _chapter("<p>clean</p>").encode()
        epub = tmp_path / "book.epub"
        _write_epub(epub, {"EPUB/text/ch001.xhtml": clean})
        before = epub.read_bytes()
        assert sanitize_epub_xhtml(epub) == []
        assert epub.read_bytes() == before

    def test_symlink_output_is_refused(self, tmp_path: Path) -> None:
        """Rewriting through a symlink is rejected, mirroring the cover pass."""
        target = tmp_path / "real.epub"
        _write_epub(target, {"EPUB/text/ch001.xhtml": _chapter("<p>x</p>")})
        link = tmp_path / "link.epub"
        link.symlink_to(target)
        import pytest

        with pytest.raises(ValueError, match="symlink"):
            sanitize_epub_xhtml(link)


class TestRendererIntegration:
    @needs_pandoc
    def test_render_epub_survives_raw_html_markdown(self, tmp_path: Path) -> None:
        """render_epub on raw-HTML markdown yields a package that validates."""
        (tmp_path / "images").mkdir()
        # A real 1x1 PNG so Pandoc can embed and manifest the raw <img> target;
        # raw-HTML image targets are collected into the EPUB media bag.
        (tmp_path / "images" / "chart.png").write_bytes(
            bytes.fromhex(
                "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
                "0000000d4944415478da63fcffff3f0300050201ffcfcc46e10000000049454e44ae426082"
            )
        )
        src = tmp_path / "combined.md"
        src.write_text(
            "# Chapter\n\n"
            "Line one<br>Line two with 5 < 7 and an unclosed tag.<br>\n\n"
            '<figure><img alt="chart" src="images/chart.png"></figure>\n',
            encoding="utf-8",
        )
        out = tmp_path / "out.epub"
        result = render_epub(src, out, title="t", author="a", language="en", extra_args=[f"--resource-path={tmp_path}"])
        assert result.size_bytes > 0
        with zipfile.ZipFile(out) as archive:
            # Every packaged XHTML member must be well-formed enough for the
            # full package contract — the same gate the pipeline summary uses.
            validate_epub_package(archive)
            damaged = [
                archive.read(name)
                for name in archive.namelist()
                if name.endswith(".xhtml") and (b"<br>" in archive.read(name) or b"\x07" in archive.read(name))
            ]
        assert damaged == []
