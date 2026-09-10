"""Shared helpers for the split transmission-validation test modules (formerly test_transmission_validation.py)."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import letter  # type: ignore[import-untyped]
from reportlab.pdfgen import canvas  # type: ignore[import-untyped]


def _make_manuscript(tmp_path: Path) -> Path:
    """Create a minimal manuscript directory with a clean .bib file."""
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "references.bib").write_text("@article{good_key, title={Ok}, year={2025}}\n", encoding="utf-8")
    return manuscript


def _write_md(manuscript: Path, name: str, content: str) -> Path:
    """Write a markdown file inside *manuscript* and return its path."""
    path = manuscript / name
    path.write_text(content, encoding="utf-8")
    return path


def _make_real_pdf(path: Path, texts: list[str]) -> Path:
    """Create a real multi-page PDF with the given text per page."""
    c = canvas.Canvas(str(path), pagesize=letter)
    for text in texts:
        c.drawString(100, 750, text)
        c.showPage()
    c.save()
    return path
