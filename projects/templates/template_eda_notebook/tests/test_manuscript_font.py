"""Compile the real manuscript font declaration and inspect its embedded faces."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest
from pypdf import PdfReader


@pytest.mark.timeout(90)
def test_manuscript_juliamono_uses_installed_family_and_embeds_all_faces(tmp_path: Path) -> None:
    preamble = Path(__file__).resolve().parents[1] / "manuscript/preamble.md"
    before = preamble.read_bytes()
    (declaration,) = re.findall(r"\\setmonofont\{[^}]+\}\[[^\]]*\]", before.decode())
    assert "Path" not in declaration and "JuliaMono" in declaration
    compiler = shutil.which("xelatex")
    assert compiler is not None, "prepare the declared native XeLaTeX provider"
    text = (
        r"\documentclass{article}\usepackage{fontspec}"
        + declaration
        + r"\begin{document}\ttfamily α μ ∂ ∇ "
        + r"\textbf{bold α}\textit{italic μ}\textbf{\textit{both ∇}}\end{document}"
    )
    source = tmp_path / "font.tex"
    source.write_text(text)
    command = [
        compiler,
        "-interaction=nonstopmode",
        "-no-shell-escape",
        "-output-directory",
        str(tmp_path),
        str(source),
    ]
    result = subprocess.run(command, cwd=tmp_path, capture_output=True, timeout=30, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Missing character" not in (tmp_path / "font.log").read_text()
    reader = PdfReader(tmp_path / "font.pdf")
    fonts = [font.get_object() for page in reader.pages for font in page["/Resources"]["/Font"].values()]
    faces = set()
    for font in fonts:
        name = str(font["/BaseFont"]).split("+")[-1]
        if not name.startswith("JuliaMono-"):
            continue
        faces.add(name)
        descendant = font["/DescendantFonts"][0].get_object()
        descriptor = descendant["/FontDescriptor"].get_object()
        assert descriptor["/FontFile2"].get_object().get_data()
    assert faces == {"JuliaMono-Regular", "JuliaMono-Bold", "JuliaMono-RegularItalic", "JuliaMono-BoldItalic"}
    source.write_text(text.replace("{JuliaMono}", "{MissingTemplateJuliaMonoFamily}"))
    negative = subprocess.run(command, cwd=tmp_path, capture_output=True, timeout=30, check=False)
    assert negative.returncode != 0
    diagnostic = " ".join((tmp_path / "font.log").read_text().replace("(fontspec)", "").split())
    assert 'font "MissingTemplateJuliaMonoFamily" cannot be found' in diagnostic
    assert preamble.read_bytes() == before
