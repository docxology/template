"""Tests for the self-contained standalone PDF renderer's pure helpers.

The full render shells out to pandoc/xelatex (covered by manual/CI runs, too slow for
the unit timeout); here we bind the project-owned typography-source parsing so the
standalone renderer reads margins and font from the same files the manuscript declares.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("_render_pdf", PROJECT_ROOT / "scripts" / "render_pdf.py")
assert _spec and _spec.loader
render_pdf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(render_pdf)


def test_extract_preamble_reads_fenced_latex(tmp_path: Path) -> None:
    f = tmp_path / "preamble.md"
    f.write_text("intro\n```latex\n\\changefontsize[11pt]{9pt}\n```\n", encoding="utf-8")
    assert "\\changefontsize[11pt]{9pt}" in render_pdf._extract_preamble(f)


def test_extract_preamble_missing_returns_empty(tmp_path: Path) -> None:
    assert render_pdf._extract_preamble(tmp_path / "nope.md") == ""


def test_geometry_from_config(tmp_path: Path) -> None:
    f = tmp_path / "config.yaml"
    f.write_text("metadata:\n  geometry: margin=0.5in\n", encoding="utf-8")
    assert render_pdf._geometry(f) == "margin=0.5in"


def test_geometry_default_when_absent(tmp_path: Path) -> None:
    f = tmp_path / "config.yaml"
    f.write_text("metadata:\n  license: MIT\n", encoding="utf-8")
    assert render_pdf._geometry(f) == "margin=0.5in"


def test_render_pdf_imports_no_infrastructure() -> None:
    """The renderer itself must not import the monorepo infrastructure."""
    src = (PROJECT_ROOT / "scripts" / "render_pdf.py").read_text(encoding="utf-8")
    assert "import infrastructure" not in src
    assert "from infrastructure" not in src
