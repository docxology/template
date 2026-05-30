"""Tests for the self-contained standalone PDF renderer's pure helpers.

The full render shells out to pandoc/xelatex (covered by manual/CI runs, too slow for
the unit timeout); here we bind the project-owned typography-source parsing so the
standalone renderer reads margins and font from the same files the manuscript declares.

The pure helper functions (extract_preamble, geometry_string) live in
``src/manuscript/render_helpers.py`` — tested directly here so the suite has a clean
import path without exec_module gymnastics on the script.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Add project src to path so manuscript.render_helpers resolves stand-alone.
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from manuscript.render_helpers import extract_preamble, geometry_string  # noqa: E402


def test_extract_preamble_reads_fenced_latex(tmp_path: Path) -> None:
    f = tmp_path / "preamble.md"
    f.write_text("intro\n```latex\n\\changefontsize[11pt]{9pt}\n```\n", encoding="utf-8")
    assert "\\changefontsize[11pt]{9pt}" in extract_preamble(f)


def test_extract_preamble_missing_returns_empty(tmp_path: Path) -> None:
    assert extract_preamble(tmp_path / "nope.md") == ""


def test_geometry_from_config(tmp_path: Path) -> None:
    f = tmp_path / "config.yaml"
    f.write_text("metadata:\n  geometry: margin=0.5in\n", encoding="utf-8")
    assert geometry_string(f) == "margin=0.5in"


def test_geometry_default_when_absent(tmp_path: Path) -> None:
    f = tmp_path / "config.yaml"
    f.write_text("metadata:\n  license: MIT\n", encoding="utf-8")
    assert geometry_string(f) == "margin=0.5in"


def test_render_pdf_imports_no_infrastructure() -> None:
    """The renderer script must not import the monorepo infrastructure."""
    src = (PROJECT_ROOT / "scripts" / "render_pdf.py").read_text(encoding="utf-8")
    assert "import infrastructure" not in src
    assert "from infrastructure" not in src


def test_render_helpers_imports_no_infrastructure() -> None:
    """render_helpers.py is self-contained — no monorepo infrastructure import."""
    src = (PROJECT_ROOT / "src" / "manuscript" / "render_helpers.py").read_text(encoding="utf-8")
    assert "import infrastructure" not in src
    assert "from infrastructure" not in src
