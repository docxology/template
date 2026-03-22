"""Pandoc raw-LaTeX fragments for multicolumn newspaper body text."""

from __future__ import annotations


def _escape_latex_fragment(text: str) -> str:
    out = (
        text.replace("\\", r"\textbackslash{}")
        .replace("{", r"\{")
        .replace("}", r"\}")
        .replace("&", r"\&")
        .replace("%", r"\%")
        .replace("$", r"\$")
        .replace("#", r"\#")
        .replace("_", r"\_")
        .replace("^", r"\textasciicircum{}")
        .replace("~", r"\textasciitilde{}")
    )
    return out


def multicol_begin(n: int) -> str:
    """Open a ``multicols`` environment (Pandoc ``{=latex}`` block)."""
    if n < 2:
        raise ValueError("column count must be at least 2")
    return f"```{{=latex}}\n\\begin{{multicols}}{{{n}}}\n```\n"


def multicol_end() -> str:
    """Close the ``multicols`` environment."""
    return f"```{{=latex}}\n\\end{{multicols}}\n```\n"


def headline(text: str, *, level: int = 1) -> str:
    """Insert a bold headline using a LaTeX size tier."""
    esc = _escape_latex_fragment(text)
    if level <= 1:
        inner = rf"\textbf{{\Large {esc}}}"
    elif level == 2:
        inner = rf"\textbf{{\large {esc}}}"
    else:
        inner = rf"\textbf{{{esc}}}"
    return f"```{{=latex}}\n{inner}\n\\par\\smallskip\n```\n"


def byline(author: str, *, dateline: str = "") -> str:
    """Italic byline with optional dateline on the following line."""
    a = _escape_latex_fragment(author)
    if dateline:
        d = _escape_latex_fragment(dateline)
        body = rf"\textit{{By {a}}}\\ \textit{{{d}}}"
    else:
        body = rf"\textit{{By {a}}}"
    return f"```{{=latex}}\n{body}\n\\par\\smallskip\n```\n"


def rule_line() -> str:
    """Thin full-width rule between blocks."""
    return "```{=latex}\n\\noindent\\rule{\\linewidth}{0.4pt}\\par\\smallskip\n```\n"


def dateline(text: str) -> str:
    """Italic dateline line (city / date)."""
    esc = _escape_latex_fragment(text)
    return f"```{{=latex}}\n\\textit{{{esc}}}\n\\par\\smallskip\n```\n"


def section_label(text: str) -> str:
    """Small caps section label (e.g. NATIONAL, BUSINESS)."""
    esc = _escape_latex_fragment(text)
    return f"```{{=latex}}\n\\textsc{{{esc}}}\n\\par\\smallskip\n```\n"


def pull_quote(text: str) -> str:
    """Indented quote block spanning column width."""
    esc = _escape_latex_fragment(text)
    inner = rf"\begin{{quote}}\itshape {esc}\end{{quote}}"
    return f"```{{=latex}}\n{inner}\n\\par\\smallskip\n```\n"


def classified_line(item: str, detail: str = "") -> str:
    """Single classified-style line: bold item plus optional detail."""
    i_esc = _escape_latex_fragment(item)
    if detail:
        d_esc = _escape_latex_fragment(detail)
        body = rf"\textbf{{{i_esc}}} — \textit{{{d_esc}}}"
    else:
        body = rf"\textbf{{{i_esc}}}"
    return f"```{{=latex}}\n{body}\n\\par\\smallskip\n```\n"
