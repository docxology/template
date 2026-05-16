r"""LaTeX-safe escaping for BibTeX field values.

BibTeX field values are interpreted by BibTeX/biber and ultimately by LaTeX,
which means a small set of characters must be escaped (``& % $ # _ { }``) and
that backslashes/tildes/carets need command-form replacements.

The exemplar references.bib file uses ``\&`` (e.g. ``Springer Science \&
Business Media``) and bare unicode for accented characters (e.g.
``Méthode``); we preserve that style: unicode is left alone (Pandoc / XeLaTeX
handle it), only the seven LaTeX special characters are touched.
"""

# Single-character → escape mapping. Multi-pass replace is unsafe (the
# escape for ``\`` would itself contain ``{``/``}`` that subsequent passes
# would re-escape), so we walk the input once.
_CHAR_ESCAPES: dict[str, str] = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}

# For unescape we apply the inverse. Multi-character sequences (e.g.
# ``\textbackslash{}``) come first; single-character escapes come last.
_UNESCAPE_PAIRS: tuple[tuple[str, str], ...] = (
    (r"\textbackslash{}", "\\"),
    (r"\textasciitilde{}", "~"),
    (r"\textasciicircum{}", "^"),
    (r"\&", "&"),
    (r"\%", "%"),
    (r"\$", "$"),
    (r"\#", "#"),
    (r"\_", "_"),
    (r"\{", "{"),
    (r"\}", "}"),
)


def escape_latex(text: str) -> str:
    """Escape LaTeX-special characters in *text*.

    Single-pass over the input so that escape sequences inserted for one
    character (e.g. ``\\`` → ``\\textbackslash{}``) are not re-escaped by a
    subsequent pass.

    Unicode is left untouched — Pandoc / XeLaTeX handle it natively, matching
    the convention of ``projects/template_code_project/manuscript/references.bib``.
    """
    if not text:
        return ""
    out: list[str] = []
    for ch in text:
        replacement = _CHAR_ESCAPES.get(ch)
        out.append(replacement if replacement is not None else ch)
    return "".join(out)


def unescape_latex(text: str) -> str:
    """Reverse the substitutions performed by :func:`escape_latex`.

    Used during BibTeX parsing so that round-tripping through
    parser → writer reproduces the original text.
    """
    if not text:
        return ""
    out = text
    for escaped, raw in _UNESCAPE_PAIRS:
        out = out.replace(escaped, raw)
    return out
