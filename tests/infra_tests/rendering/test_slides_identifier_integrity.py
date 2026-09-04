"""Rendered regression coverage for code-token integrity in slide profiles."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.slides_renderer import SlidesRenderer


@pytest.mark.slow
@pytest.mark.requires_latex
def test_accessible_identifier_stays_contiguous_while_archive_contract_is_preserved(
    tmp_path: Path,
) -> None:
    """Accessible projection never inserts arbitrary identifier breakpoints."""

    if not shutil.which("pandoc") or not shutil.which("pdftotext"):
        pytest.skip("Pandoc and pdftotext are required")
    compiler = next((name for name in ("xelatex", "lualatex", "pdflatex") if shutil.which(name)), None)
    if compiler is None:
        pytest.skip("No LaTeX compiler available")

    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    source = manuscript / "identifier.md"
    identifier = "bayesian_model_reduction.reduce"
    source.write_text(
        f"## Projected identifier\n\nCall `{identifier}` for this bounded operation.\n",
        encoding="utf-8",
    )

    accessible_dir = tmp_path / "accessible"
    accessible = SlidesRenderer(
        RenderingConfig(
            output_dir=str(accessible_dir),
            slides_dir=str(accessible_dir),
            slides_profile="accessible",
            latex_compiler=compiler,
        )
    )
    accessible_pdf = accessible.render(
        source,
        output_format="beamer",
        manuscript_dir=manuscript,
    )
    accessible_tex = accessible_pdf.with_suffix(".tex").read_text(encoding="utf-8")
    extracted = subprocess.run(
        ["pdftotext", "-layout", str(accessible_pdf), "-"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert r"\breaktt{" not in accessible_tex
    assert r"\texttt{bayesian\_model\_reduction.reduce}" in accessible_tex
    assert identifier in extracted

    archive_dir = tmp_path / "archive"
    archive = SlidesRenderer(
        RenderingConfig(
            output_dir=str(archive_dir),
            slides_dir=str(archive_dir),
            slides_profile="archive",
            latex_compiler=compiler,
        )
    )
    archive_pdf = archive.render(
        source,
        output_format="beamer",
        manuscript_dir=manuscript,
    )
    archive_tex = archive_pdf.with_suffix(".tex").read_text(encoding="utf-8")
    assert r"\breaktt{bayesian\_model\_reduction.reduce}" in archive_tex
