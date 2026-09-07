"""Shared helpers extracted from ``test_slides_renderer_core.py``.

Follows the No Mocks Policy — helpers build real manuscripts and invoke
the real Pandoc + LaTeX toolchain (or skip when it is absent).
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest


def _require_beamer_toolchain() -> str:
    """Return the available LaTeX compiler or skip when Beamer tools are absent."""
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    if shutil.which("xelatex"):
        return "xelatex"
    if shutil.which("pdflatex"):
        return "pdflatex"
    else:
        pytest.skip("No LaTeX compiler available")


def _multi_bibliography_slide_fixture(tmp_path: Path) -> tuple[Path, Path]:
    """Write one slide whose two citations live in separate bibliography files."""
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    (manuscript_dir / "references.bib").write_text(
        "@article{alpha2020primary,\n"
        "  author={Alpha, Ada},\n"
        "  title={Primary Source},\n"
        "  journal={Journal One},\n"
        "  year={2020}\n"
        "}\n",
        encoding="utf-8",
    )
    (manuscript_dir / "z_supplemental.bib").write_text(
        "@article{omega2021supplement,\n"
        "  author={Omega, Orla},\n"
        "  title={Supplemental Source},\n"
        "  journal={Journal Two},\n"
        "  year={2021}\n"
        "}\n",
        encoding="utf-8",
    )
    source = tmp_path / "multi_bibliography.md"
    source.write_text(
        "# Evidence\n\nBoth sources matter [@alpha2020primary; @omega2021supplement].\n",
        encoding="utf-8",
    )
    return source, manuscript_dir
