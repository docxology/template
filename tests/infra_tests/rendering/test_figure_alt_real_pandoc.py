"""Real-pandoc tagged-PDF structure-tree alt-text test (split from test_figure_alt_wiring.py)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
import pytest
from infrastructure.rendering._pdf_figure_alts import apply_pdf_figure_alts
from infrastructure.rendering._pdf_combined_latex import postprocess_latex
from ._figure_alt_helpers import (
    _run_lualatex,
    _pdf_structure_alt_texts,
)


@pytest.mark.requires_latex
@pytest.mark.timeout(60)
def test_registry_alt_reaches_real_tagged_pdf_structure_tree(tmp_path: Path) -> None:
    if shutil.which("lualatex") is None:
        pytest.skip("lualatex is not installed")

    pdf_dir = tmp_path / "output" / "pdf"
    figures_dir = tmp_path / "output" / "figures"
    pdf_dir.mkdir(parents=True)
    figures_dir.mkdir(parents=True)
    probe_tex = postprocess_latex(
        r"\documentclass{article}\begin{document}probe\end{document}",
        tagged_pdf=True,
        language="en",
    )
    probe = _run_lualatex(pdf_dir, "tagged-figure-probe", probe_tex)
    if probe.returncode != 0:
        pytest.skip("installed LuaLaTeX does not support the repository's tagged-PDF metadata mode")

    from PIL import Image

    Image.new("RGB", (8, 8), color=(30, 60, 90)).save(figures_dir / "dense.png")
    registry_path = figures_dir / "figure_registry.json"
    rich_alt = "Blue & amber curves fall from 9% to 1_000 units # reproducibly."
    registry_path.write_text(
        json.dumps({"fig:dense": {"filename": "dense.png", "alt": rich_alt}}),
        encoding="utf-8",
    )
    tex = postprocess_latex(
        r"\documentclass{article}\usepackage{graphicx}\begin{document}"
        r"\begin{figure}\includegraphics[alt={Short caption}]{../figures/dense.png}"
        r"\caption{Short caption}\label{fig:dense}\end{figure}"
        r"\end{document}",
        tagged_pdf=True,
        language="en",
    )
    tex = apply_pdf_figure_alts(tex, registry_path, tagged_pdf=True)

    compiled = _run_lualatex(pdf_dir, "tagged-registry-alt", tex)

    assert compiled.returncode == 0, compiled.stdout
    assert _pdf_structure_alt_texts(pdf_dir / "tagged-registry-alt.pdf") == [rich_alt]
