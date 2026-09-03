"""Helpers for breakable monospace spans in generated LaTeX."""

from __future__ import annotations

import re
import string

_TEXTTT_RE = re.compile(r"\\texttt\{(?P<value>[^{}]+)\}")
_PANDOC_REF_RE = re.compile(r"\{\[\}@(?P<target>[^{}]+)\{\]\}")
_BREAKTT_PREAMBLE = r"""
\IfFileExists{seqsplit.sty}{\usepackage{seqsplit}}{\newcommand{\seqsplit}[1]{#1}}
\protected\def\breakseq#1{\seqsplit{#1}}
\protected\def\breaktt#1{\begingroup\ttfamily\seqsplit{#1}\endgroup}
""".strip()
_BREAKABLE_LITERALS = (
    r"MILD\_SURPRISE",
    "CATASTROPHIC",
)
LONG_TEXTTT_BREAK_MIN_CHARACTERS = 16
_SIMPLE_TEXTTT_SOURCE_CHARACTERS = frozenset(string.ascii_letters + string.digits + ' !"#$%&()*+,-./:;=?@_')
_SIMPLE_LATEX_TEXTTT_ESCAPE_RE = re.compile(r"\\([#$%&_])")
_SIMPLE_LATEX_TEXTTT_CONTROL_SPACE_RE = re.compile(r"\\ ")


def long_texttt_source_is_breakable(
    value: str,
    *,
    min_chars: int = LONG_TEXTTT_BREAK_MIN_CHARACTERS,
) -> bool:
    """Return whether Pandoc emits a ``texttt`` body this pass can rewrite.

    This allow-list is the exact printable-ASCII subset that Pandoc serializes
    inside one simple, brace-free ``\\texttt{...}`` body. Apostrophes, square
    brackets, and the other TeX-special literals become braced commands. Pandoc
    serializes an ordinary source space as the brace-free control-space
    ``\\ ``; the downstream decoder and source predicate intentionally share
    that exact case. Ordinary identifiers, paths, punctuation, spaces, and
    simple escapes such as underscores remain eligible.
    """

    return len(value) >= min_chars and all(character in _SIMPLE_TEXTTT_SOURCE_CHARACTERS for character in value)


def _simple_latex_texttt_source(value: str) -> str | None:
    """Recover source characters from one regex-safe Pandoc ``texttt`` body.

    The outer matcher deliberately excludes braces. Pandoc's simple escapes
    for ``#``, ``$``, ``%``, ``&``, and ``_`` therefore remain the only TeX
    syntax accepted here. A residual backslash means the serialized body is
    outside the same narrow contract used by the source-AST estimator.
    """

    source = _SIMPLE_LATEX_TEXTTT_CONTROL_SPACE_RE.sub(" ", value)
    source = _SIMPLE_LATEX_TEXTTT_ESCAPE_RE.sub(r"\1", source)
    return None if "\\" in source else source


def _ensure_breaktt_preamble(tex_content: str) -> str:
    if r"\protected\def\breaktt" in tex_content:
        return tex_content
    begin_doc = tex_content.find(r"\begin{document}")
    if begin_doc <= 0:
        return tex_content
    return tex_content[:begin_doc] + _BREAKTT_PREAMBLE + "\n" + tex_content[begin_doc:]


def make_long_texttt_breakable(
    tex_content: str,
    *,
    min_chars: int = LONG_TEXTTT_BREAK_MIN_CHARACTERS,
) -> tuple[str, int]:
    r"""Convert long ``\texttt{...}`` spans to a breakable monospace macro.

    Pandoc emits inline code as ``\texttt{...}``, which is intentionally
    unbreakable.  That is desirable for short identifiers but a common source
    of overfull boxes in narrow table columns and dense slides — not only for
    paths and globs but also for long separator-less CamelCase identifiers
    (e.g. ``MutatingSubsystemRule``, ``SingletonAccessRule``), which carry no
    slash/underscore/dot to break on and therefore run off the right margin.
    This function rewrites every monospace span above a small length threshold
    and injects the macro required to typeset it. ``\seqsplit`` only *adds*
    break opportunities — a span that already fits is rendered unchanged and no
    characters are inserted — so spans that copy cleanly stay copyable.
    """
    replacements = 0

    def _replace(match: re.Match[str]) -> str:
        nonlocal replacements
        value = match.group("value")
        source = _simple_latex_texttt_source(value)
        if source is None or not long_texttt_source_is_breakable(source, min_chars=min_chars):
            return match.group(0)
        replacements += 1
        return rf"\breaktt{{{value}}}"

    updated = _TEXTTT_RE.sub(_replace, tex_content)
    if replacements:
        updated = _ensure_breaktt_preamble(updated)
    return updated, replacements


def constrain_includegraphics_textheight(
    tex_content: str,
    fraction: str,
    *,
    first_fraction: str | None = None,
) -> tuple[str, int]:
    """Replace Pandoc's full-textheight image bounds with safe configured fractions.

    The first source-owned figure is the graphical abstract in the combined paper path, so it can
    receive a distinct front-matter bound while all later figures use the ordinary figure bound.
    """
    target = r"height=\textheight"
    occurrences = tex_content.count(target)
    if not occurrences:
        return tex_content, 0
    replacements = [first_fraction if first_fraction is not None else fraction] + [fraction] * (occurrences - 1)
    parts = tex_content.split(target)
    updated = parts[0]
    for index, part in enumerate(parts[1:]):
        updated += rf"height={replacements[index]}\textheight" + part
    return updated, occurrences


def make_known_literals_breakable(tex_content: str) -> tuple[str, int]:
    """Make recurring long table labels breakable without changing wording."""
    replacements = 0
    updated = tex_content
    for literal in _BREAKABLE_LITERALS:
        pattern = re.compile(rf"(?<![A-Za-z]){re.escape(literal)}(?![A-Za-z])")

        def _sub(_match: re.Match[str], value: str = literal) -> str:
            return rf"\breakseq{{{value}}}"

        updated, count = pattern.subn(_sub, updated)
        replacements += count
    if replacements:
        updated = _ensure_breaktt_preamble(updated)
    return updated, replacements


def make_pandoc_reference_tokens_breakable(tex_content: str) -> tuple[str, int]:
    """Make unresolved Pandoc cross-reference tokens breakable in slides.

    Section slides are rendered one file at a time, so cross-section
    references can legitimately remain as Pandoc's escaped ``{[}@key{]}``
    tokens.  In Beamer these tokens are unbreakable enough to create
    overfull hboxes in dense scientific frames, so render them through the
    same protected break sequence macro used for long labels.
    """

    def _replace(match: re.Match[str]) -> str:
        target = match.group("target")
        return rf"\breakseq{{[@{target}]}}"

    updated, replacements = _PANDOC_REF_RE.subn(_replace, tex_content)
    if replacements:
        updated = _ensure_breaktt_preamble(updated)
    return updated, replacements
