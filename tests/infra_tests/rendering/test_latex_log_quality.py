"""Tests for LaTeX render-log quality parsing."""

from __future__ import annotations

import shutil
import subprocess

import pytest

from infrastructure.rendering.latex_log_quality import (
    collect_latex_log_findings,
    format_latex_findings,
    parse_latex_log_findings,
    summarize_latex_findings,
)
from infrastructure.rendering.latex_texttt import (
    LONG_TEXTTT_BREAK_MIN_CHARACTERS,
    constrain_includegraphics_textheight,
    long_texttt_source_is_breakable,
    make_known_literals_breakable,
    make_long_texttt_breakable,
    make_pandoc_reference_tokens_breakable,
)


def test_parse_layout_and_reference_findings(tmp_path):
    log = tmp_path / "paper.log"
    log.write_text(
        "\n".join(
            [
                "Package pdftexcmds Info: \\pdfdraftmode not found.",
                "Overfull \\hbox (12.0pt too wide) in paragraph at lines 10--11",
                "Underfull \\hbox (badness 10000) in paragraph at lines 12--13",
                "Underfull \\vbox (badness 1112) detected at line 14",
                "LaTeX Warning: Reference `fig:x' on page 1 undefined on input line 20.",
                "Package natbib Warning: Citation `smith2020' on page 2 undefined.",
            ]
        ),
        encoding="utf-8",
    )

    findings = parse_latex_log_findings(log)

    assert [finding.kind for finding in findings] == [
        r"Overfull \hbox",
        r"Underfull \hbox",
        "Undefined reference/citation",
        "Undefined reference/citation",
    ]


def test_collect_and_format_findings(tmp_path):
    first = tmp_path / "first.log"
    second = tmp_path / "second.log"
    first.write_text("Overfull \\vbox (1pt too high) detected at line 9\n", encoding="utf-8")
    second.write_text("! LaTeX Error: File `missing.png' not found.\n", encoding="utf-8")

    findings = collect_latex_log_findings([first, second])
    counts = summarize_latex_findings(findings)
    formatted = format_latex_findings(findings)

    assert counts[r"Overfull \vbox"] == 1
    assert counts["Missing LaTeX file"] == 1
    assert "first.log:1" in formatted
    assert "second.log:1" in formatted


def test_latex_texttt_helpers_make_paths_and_labels_breakable():
    tex = (
        "\\documentclass{article}\\begin{document}"
        "\\texttt{output/figures/agency/cascade\\_waterfall.png} "
        "MILD\\_SURPRISE CATASTROPHIC"
        "\\includegraphics[width=\\linewidth,height=\\textheight]{x.png}"
        "\\end{document}"
    )

    tex, path_count = make_long_texttt_breakable(tex)
    tex, label_count = make_known_literals_breakable(tex)
    tex, graphics_count = constrain_includegraphics_textheight(tex, "0.68")

    assert path_count == 1
    assert label_count == 2
    assert graphics_count == 1
    assert "\\breaktt{output/figures/agency/cascade\\_waterfall.png}" in tex
    assert "\\breakseq{MILD\\_SURPRISE}" in tex
    assert "height=0.68\\textheight" in tex


def test_front_matter_figure_can_use_a_distinct_height_fraction():
    tex = (
        r"\includegraphics[width=\linewidth,height=\textheight]{front.png}"
        r"\includegraphics[width=\linewidth,height=\textheight]{body.png}"
    )

    tex, graphics_count = constrain_includegraphics_textheight(
        tex,
        "0.68",
        first_fraction="0.64",
    )

    assert graphics_count == 2
    assert tex.count(r"height=0.64\textheight") == 1
    assert tex.count(r"height=0.68\textheight") == 1


def test_long_camelcase_identifier_is_breakable_short_is_not():
    # Separator-less CamelCase rule names (no slash/underscore/dot) overflow
    # narrow table columns because Pandoc's \texttt{} is unbreakable. They must
    # now be made breakable; short identifiers must be left intact.
    tex = (
        "\\documentclass{article}\\begin{document}\\texttt{SingletonAccessRule} and \\texttt{NodeKind}.\\end{document}"
    )

    tex, count = make_long_texttt_breakable(tex)

    assert count == 1  # only the 19-char identifier, not the 8-char one
    assert "\\breaktt{SingletonAccessRule}" in tex
    assert "\\texttt{NodeKind}" in tex  # short span untouched


def test_long_texttt_source_and_latex_rewrite_share_the_exact_threshold() -> None:
    below = "a" * (LONG_TEXTTT_BREAK_MIN_CHARACTERS - 1)
    at = "a" * LONG_TEXTTT_BREAK_MIN_CHARACTERS
    escaped_at = "a_b_c_d_e_f_g_hi"
    escaped_latex = escaped_at.replace("_", r"\_")

    assert len(escaped_at) == LONG_TEXTTT_BREAK_MIN_CHARACTERS
    assert not long_texttt_source_is_breakable(below)
    assert long_texttt_source_is_breakable(at)
    assert long_texttt_source_is_breakable(escaped_at)

    tex = rf"\begin{{document}}\texttt{{{below}}}\texttt{{{at}}}\texttt{{{escaped_latex}}}\end{{document}}"
    updated, count = make_long_texttt_breakable(tex)

    assert count == 2
    assert rf"\texttt{{{below}}}" in updated
    assert rf"\breaktt{{{at}}}" in updated
    assert rf"\breaktt{{{escaped_latex}}}" in updated


def test_long_texttt_braced_literal_serializations_remain_indivisible() -> None:
    unsafe_sources = [
        "abcdefghijklmnop{",
        "abcdefghijklmnop\\",
        "abcdefghijklmnop~",
        "abcdefghijklmnop<",
    ]
    for source in unsafe_sources:
        assert not long_texttt_source_is_breakable(source)

    tex = (
        r"\begin{document}"
        r"\texttt{abcdefghijklmnop\{}"
        r"\texttt{abcdefghijklmnop\textbackslash{}}"
        r"\texttt{abcdefghijklmnop\textasciitilde{}}"
        r"\texttt{abcdefghijklmnop\textless{}}"
        r"\end{document}"
    )
    updated, count = make_long_texttt_breakable(tex)

    assert count == 0
    assert updated == tex


@pytest.mark.parametrize(
    ("literal", "latex_literal"),
    [
        ("'", r"\textquotesingle{}"),
        ("[", "{[}"),
        ("]", "{]}"),
    ],
)
def test_long_texttt_non_simple_printable_ascii_stays_indivisible_across_threshold(
    literal: str,
    latex_literal: str,
) -> None:
    below = "a" * (LONG_TEXTTT_BREAK_MIN_CHARACTERS - 2) + literal
    at = "a" * (LONG_TEXTTT_BREAK_MIN_CHARACTERS - 1) + literal
    assert len(below) == LONG_TEXTTT_BREAK_MIN_CHARACTERS - 1
    assert len(at) == LONG_TEXTTT_BREAK_MIN_CHARACTERS
    assert not long_texttt_source_is_breakable(below)
    assert not long_texttt_source_is_breakable(at)

    serialized_below = r"\texttt{" + "a" * (LONG_TEXTTT_BREAK_MIN_CHARACTERS - 2) + latex_literal + "}"
    serialized_at = r"\texttt{" + "a" * (LONG_TEXTTT_BREAK_MIN_CHARACTERS - 1) + latex_literal + "}"
    tex = r"\begin{document}" + serialized_below + serialized_at + r"\end{document}"
    updated, count = make_long_texttt_breakable(tex)

    assert count == 0
    assert updated == tex


def test_long_texttt_control_space_shares_source_and_latex_rewrite_contract() -> None:
    below = "a" * (LONG_TEXTTT_BREAK_MIN_CHARACTERS - 2) + " "
    at = "a" * (LONG_TEXTTT_BREAK_MIN_CHARACTERS - 1) + " "
    assert not long_texttt_source_is_breakable(below)
    assert long_texttt_source_is_breakable(at)

    serialized_below = r"\texttt{" + "a" * (LONG_TEXTTT_BREAK_MIN_CHARACTERS - 2) + r"\ }"
    serialized_at = r"\texttt{" + "a" * (LONG_TEXTTT_BREAK_MIN_CHARACTERS - 1) + r"\ }"
    tex = r"\begin{document}" + serialized_below + serialized_at + r"\end{document}"
    updated, count = make_long_texttt_breakable(tex)

    assert count == 1
    assert serialized_below in updated
    assert rf"\breaktt{{{'a' * (LONG_TEXTTT_BREAK_MIN_CHARACTERS - 1)}\ }}" in updated


@pytest.mark.slow
@pytest.mark.requires_latex
def test_long_texttt_control_space_wraps_in_real_archive_latex(tmp_path) -> None:
    compiler = next((name for name in ("xelatex", "lualatex", "pdflatex") if shutil.which(name)), None)
    if compiler is None or shutil.which("kpsewhich") is None:
        pytest.skip("A LaTeX compiler and kpsewhich are required")
    seqsplit = subprocess.run(
        ["kpsewhich", "seqsplit.sty"],
        check=False,
        capture_output=True,
        text=True,
    )
    if seqsplit.returncode != 0 or not seqsplit.stdout.strip():
        pytest.skip("seqsplit.sty is required for the real wrapping regression")
    token = "a" * 100 + r"\ " + "b" * 100
    tex = (
        r"\documentclass{article}"
        "\n"
        r"\usepackage[paperwidth=10cm,paperheight=5cm,margin=1cm]{geometry}"
        "\n"
        r"\begin{document}\noindent\parbox{3cm}{\texttt{" + token + r"}}\end{document}"
        "\n"
    )
    updated, count = make_long_texttt_breakable(tex)
    tex_path = tmp_path / "control-space.tex"
    tex_path.write_text(updated, encoding="utf-8")

    result = subprocess.run(
        [compiler, "-interaction=nonstopmode", "-halt-on-error", tex_path.name],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )

    assert count == 1
    assert result.returncode == 0, result.stdout + result.stderr
    log = tex_path.with_suffix(".log").read_text(encoding="utf-8", errors="ignore")
    assert "Overfull \\hbox" not in log


def test_make_pandoc_reference_tokens_breakable():
    tex, count = make_pandoc_reference_tokens_breakable(
        r"See {[}@fig:matrix-heatmaps{]} and {[}@sec:mechanism-localization{]}."
        "\n\\begin{document}\nBody\n\\end{document}\n"
    )

    assert count == 2
    assert r"\breakseq{[@fig:matrix-heatmaps]}" in tex
    assert r"\breakseq{[@sec:mechanism-localization]}" in tex
    assert r"\protected\def\breakseq" in tex
