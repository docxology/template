"""Shared constants and helpers for the split ebook fallback test modules (formerly test_docx_epub_fallbacks.py)."""

from __future__ import annotations

import shutil
from pathlib import Path
from zipfile import ZipFile

import defusedxml.ElementTree as safe_et
import pytest


_PANDOC = shutil.which("pandoc")
_CALIBRE = shutil.which("ebook-convert")
# 'true' and 'false' are guaranteed-present POSIX binaries used as real
# non-pandoc / always-fail-exit substitutions to exercise the binary-missing
# fallback path without mocking.
_TRUE = shutil.which("true")
_FALSE = shutil.which("false")

needs_pandoc = pytest.mark.skipif(_PANDOC is None, reason="pandoc not installed")

SAMPLE_MD = """\
# Chapter 1

A paragraph of text in the first chapter.

# Chapter 2

A second chapter with **bold** and *italic* text.
"""

_MINIMAL_MD = "# Title\n\nSome content.\n"


def _ebook_archive_text(path: Path) -> str:
    """Return decoded XML/XHTML text from a DOCX or EPUB archive."""
    with ZipFile(path) as archive:
        members = [name for name in archive.namelist() if name.endswith((".xml", ".xhtml", ".html", ".opf"))]
        return "\n".join(archive.read(name).decode("utf-8", errors="ignore") for name in members)


def _epub_package_identifiers(path: Path) -> tuple[str, str]:
    """Return the OPF and NCX identifiers from one real ebook-stage EPUB."""

    with ZipFile(path) as archive:
        opf_name = next(name for name in archive.namelist() if name.endswith(".opf"))
        ncx_name = next(name for name in archive.namelist() if name.endswith(".ncx"))
        opf = safe_et.fromstring(archive.read(opf_name))
        ncx = safe_et.fromstring(archive.read(ncx_name))
    package_identifier = opf.find(".//{http://purl.org/dc/elements/1.1/}identifier")
    assert package_identifier is not None and package_identifier.text is not None
    navigation_identifier = next(
        node.get("content")
        for node in ncx.findall(".//{http://www.daisy.org/z3986/2005/ncx/}meta")
        if node.get("name") == "dtb:uid"
    )
    assert navigation_identifier is not None
    return package_identifier.text, navigation_identifier
