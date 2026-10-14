"""Exact plain-cell projection and conservative TeX-boundary controls."""

from __future__ import annotations

import re

import pytest

from infrastructure.rendering._pdf_combined_latex import postprocess_latex
from infrastructure.rendering.latex_texttt import make_plain_table_paths_breakable


# Actual Gold Table 2 paragraph widths and overflowing validator strings.
_COLUMNS = (
    "@{}\n"
    + "\n".join(
        r">{\raggedright\arraybackslash}p{(\linewidth - 8\tabcolsep) * \real{" + width + "}}"
        for width in ("0.0833", "0.2292", "0.3125", "0.1458", "0.2292")
    )
    + "@{}"
)
_PATHS = (
    r"tests/test\_manuscript\_variables.py",
    r"output/reports/claim\_support\_registry.json",
    "infrastructure.reference.citation",
)


def _table(body: str, columns: str = _COLUMNS) -> str:
    return r"\begin{longtable}[]{" + columns + "}\n" + body + "\n" + r"\end{longtable}"


def _document(content: str) -> str:
    return r"\documentclass{article}\begin{document}" + content + r"\end{document}"


def test_actual_gold_plain_paths_preserve_cells_columns_font_and_characters() -> None:
    body = (
        r"\caption{Source-owned scientific-integrity dimensions.}\label{tbl:integrity_dimensions}\tabularnewline" + "\n"
    )
    body += r"\toprule\noalign{}" + "\n"
    body += (
        r"\begin{minipage}[b]{\linewidth}\raggedright ID\end{minipage} & Dimension & Risk & Owner & Validator \\" + "\n"
    )
    body += r"\midrule\noalign{}" + "\n" + r"\endfirsthead" + "\n"
    body += "\n".join(
        "I" + str(index) + " & Claim support & 10 & evidence assay & " + path + r" \\"
        for index, path in enumerate(_PATHS)
    )
    original = _document(_table(body))
    projected, count = make_plain_table_paths_breakable(original)
    assert count == 3
    assert _COLUMNS in projected
    assert r"\ttfamily" not in projected.split(r"\begin{document}", 1)[1]
    for path in _PATHS:
        assert r"\breakseq{" + path + "}" in projected
    recovered = re.sub(r"\\breakseq\{([^{}]*)\}", r"\1", projected.split(r"\begin{document}", 1)[1])
    assert recovered == original.split(r"\begin{document}", 1)[1]
    assert make_plain_table_paths_breakable(projected) == (projected, 0)
    assert r"\protected\def\breakseq" in projected
    assert postprocess_latex(original) == projected


@pytest.mark.parametrize(
    "content",
    [
        _table(" & ".join(_PATHS) + r" \\", "@{}lll@{}"),
        _table("A & B & C & D & " + _PATHS[0] + r" \\", "@{}p{2cm}p{2cm}p{2cm}p{2cm}p{2cm}@{}"),
        "% " + _table("A & B & C & D & " + _PATHS[0] + r" \\").replace("\n", "\n% "),
        r"\newcommand{\example}{" + _table("A & B & C & D & " + _PATHS[0] + r" \\") + "}",
        r"\begin{verbatim}" + _table("A & B & C & D & " + _PATHS[0] + r" \\") + r"\end{verbatim}",
        r"\verb|" + _table("A & B & C & D & " + _PATHS[0] + r" \\") + "|",
        "$" + _table("A & B & C & D & " + _PATHS[0] + r" \\") + "$",
        "$% ignored dollar $\n" + _table("A & B & C & D & " + _PATHS[0] + r" \\") + "$",
        r"\[" + _table("A & B & C & D & " + _PATHS[0] + r" \\") + r"\]",
        r"\begin{unfamiliar}" + _table("A & B & C & D & " + _PATHS[0] + r" \\") + r"\end{unfamiliar}",
        r"\begin{equation*}" + _table("A & B & C & D & " + _PATHS[0] + r" \\") + r"\end{equation*}",
        r"\begin{verbatim*}" + _table("A & B & C & D & " + _PATHS[0] + r" \\") + r"\end{verbatim*}",
        r"\begin{unfamiliar-env}" + _table("A & B & C & D & " + _PATHS[0] + r" \\") + r"\end{unfamiliar-env}",
        r"\begin {equation}" + _table("A & B & C & D & " + _PATHS[0] + r" \\") + r"\end{equation}",
        "\\begin\n{unfamiliar}" + _table("A & B & C & D & " + _PATHS[0] + r" \\") + r"\end{unfamiliar}",
    ],
)
def test_outside_paragraph_cells_remains_exact(content: str) -> None:
    original = _document(_PATHS[0] + "\n" + content)
    assert make_plain_table_paths_breakable(original) == (original, 0)


@pytest.mark.parametrize(
    "body",
    [
        "A & B & C & D & $" + _PATHS[0] + r"$ \\",
        "A & B & C & D & " + _PATHS[0] + r" % comment \\",
        r"A & B & C & D & \unknown{" + _PATHS[0] + r"} \\",
        r"\begin{verbatim}" + "\nA & B & C & D & " + _PATHS[0] + r" \\" + "\n" + r"\end{verbatim}",
        r"\caption{A & B & C & D & " + _PATHS[0] + r" \\" + "\ncontinued}",
        "A & B & C & D & {" + _PATHS[0] + r" \\",
        r"A & B & C & D & safe\&" + _PATHS[0] + r" \\",
        r"\begin{minipage}[b]{\linewidth}" + "\nA & B & C & D & " + _PATHS[0] + r" \\",
        r"$A & B & C & D & " + _PATHS[0] + r" \\" + "\ncontinued$",
        "A & B & " + _PATHS[0] + r" \\",
        r"\begin {equation}" + "\nA & B & C & D & " + _PATHS[0] + r" \\" + "\n" + r"\end {equation}",
    ],
)
def test_unfamiliar_or_unbalanced_table_body_abstains(body: str) -> None:
    original = _document(_table(body))
    assert make_plain_table_paths_breakable(original) == (original, 0)


def test_bounded_parser_abstains_on_unclosed_and_oversized_inputs() -> None:
    original = _document(_table("A & B & C & D & " + _PATHS[0] + r" \\")).replace(r"\end{longtable}", "")
    assert make_plain_table_paths_breakable(original) == (original, 0)
    oversized = " " * (16 * 1024 * 1024 + 1) + original
    assert make_plain_table_paths_breakable(oversized) == (oversized, 0)


def test_plain_prose_short_identifiers_and_escaped_math_do_not_change() -> None:
    body = r"A & Ordinary prose & 1 & CamelCaseIdentifier & short/path \\"
    original = _document(_table(body))
    assert make_plain_table_paths_breakable(original) == (original, 0)
    math = r"$escaped \$ " + _table("A & B & C & D & " + _PATHS[0] + r" \\") + "$"
    original = _document(math)
    assert make_plain_table_paths_breakable(original) == (original, 0)
