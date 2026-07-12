"""Tests for LaTeX render-log quality parsing."""

from __future__ import annotations

from infrastructure.rendering.latex_log_quality import (
    collect_latex_log_findings,
    format_latex_findings,
    parse_latex_log_findings,
    summarize_latex_findings,
)
from infrastructure.rendering.latex_texttt import (
    constrain_includegraphics_textheight,
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
        "\\documentclass{article}\\begin{document}"
        "\\texttt{SingletonAccessRule} and \\texttt{NodeKind}."
        "\\end{document}"
    )

    tex, count = make_long_texttt_breakable(tex)

    assert count == 1  # only the 19-char identifier, not the 8-char one
    assert "\\breaktt{SingletonAccessRule}" in tex
    assert "\\texttt{NodeKind}" in tex  # short span untouched


def test_make_pandoc_reference_tokens_breakable():
    tex, count = make_pandoc_reference_tokens_breakable(
        r"See {[}@fig:matrix-heatmaps{]} and {[}@sec:mechanism-localization{]}."
        "\n\\begin{document}\nBody\n\\end{document}\n"
    )

    assert count == 2
    assert r"\breakseq{[@fig:matrix-heatmaps]}" in tex
    assert r"\breakseq{[@sec:mechanism-localization]}" in tex
    assert r"\protected\def\breakseq" in tex
