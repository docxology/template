"""Real pandoc tests for convert_latex_images.lua.

Follows No Mocks Policy - all tests invoke the real pandoc binary and Lua filter.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_FILTER_PATH = REPO_ROOT / "infrastructure" / "rendering" / "convert_latex_images.lua"
PANDOC_FORMAT = "markdown+tex_math_dollars+raw_tex+header_attributes"


def _pandoc_path() -> str:
    pandoc = shutil.which("pandoc")
    if pandoc is None:
        pytest.skip("pandoc not available on PATH")
    return pandoc


def _filter_path() -> Path:
    override = os.environ.get("TEMPLATE_TEST_LATEX_IMAGE_FILTER")
    if override:
        return Path(override)
    return DEFAULT_FILTER_PATH


def _run_pandoc(markdown: str) -> str:
    filter_path = _filter_path()
    assert filter_path.exists(), f"Lua filter not found: {filter_path}"

    cmd = [
        _pandoc_path(),
        "--from",
        PANDOC_FORMAT,
        "-t",
        "html5",
        f"--lua-filter={filter_path}",
    ]
    result = subprocess.run(
        cmd,
        input=markdown,
        text=True,
        capture_output=True,
        check=True,
        cwd=REPO_ROOT,
    )
    return result.stdout


class TestConvertLatexImagesFilter:
    """Exercise the real pandoc Lua filter without mocks."""

    @pytest.mark.parametrize(
        ("width_expr", "expected_width"),
        [
            ("0.8\\textwidth", "80%"),
            ("0.9\\textwidth", "90%"),
            ("0.7\\textwidth", "70%"),
            ("0.55\\textwidth", "55%"),
            ("0.625\\textwidth", "62.5%"),
            ("\\textwidth", "100%"),
            ("bogus\\textwidth", "100%"),
        ],
    )
    def test_raw_inline_textwidth_widths_emit_single_percent(self, width_expr: str, expected_width: str) -> None:
        markdown = f"`\\includegraphics[width={width_expr}]{{figures/plot.png}}`{{=tex}}\n"

        html = _run_pandoc(markdown)

        assert f"max-width: {expected_width};" in html
        assert "%%" not in html

    def test_raw_inline_caption_in_same_node_emits_figure_with_cleaned_caption(self) -> None:
        markdown = (
            "Prefix "
            "`\\includegraphics[width=0.55\\textwidth]{figures/plot.png}"
            "\\caption{Inline cap with \\eqref{eq:x} and \\ref{fig:y}}`{=tex} "
            "suffix\n"
        )

        html = _run_pandoc(markdown)

        assert '<figure class="figure"><img ' in html
        assert "max-width: 55%;" in html
        assert "<figcaption>Inline cap with (Equation) and (Ref)</figcaption>" in html
        assert "%%" not in html

    def test_raw_block_figure_with_caption_emits_figcaption_and_cleaned_refs(self) -> None:
        markdown = (
            "\\begin{figure}\n"
            "\\centering\n"
            "\\includegraphics[width=0.7\\textwidth]{figures/plot.png}\n"
            "\\caption{A test caption with \\eqref{eq:one} and \\ref{fig:two}.}\n"
            "\\label{fig:plot}\n"
            "\\end{figure}\n"
        )

        html = _run_pandoc(markdown)

        assert '<figure class="figure"><img ' in html
        assert "max-width: 70%;" in html
        assert "<figcaption>A test caption with (Equation) and (Ref).</figcaption>" in html
        assert '<div class="figure">' not in html
        assert "%%" not in html

    def test_raw_block_figure_without_caption_keeps_bare_div_output(self) -> None:
        markdown = (
            "\\begin{figure}\n"
            "\\centering\n"
            "\\includegraphics[width=0.9\\textwidth]{figures/plot.png}\n"
            "\\label{fig:plot}\n"
            "\\end{figure}\n"
        )

        html = _run_pandoc(markdown)

        assert '<div class="figure"><img ' in html
        assert "max-width: 90%;" in html
        assert "<figcaption>" not in html
        assert "%%" not in html
