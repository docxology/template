"""Sanitize Pandoc-generated ``\\texorpdfstring`` calls in section titles.

Pandoc wraps section/subsection titles that contain math in
``\\texorpdfstring{<TeX>}{<bookmark>}``: the first arg is the typeset
form, the second is the plain string used by hyperref for PDF
bookmarks. When the heading contains math (e.g. ``$F[q_\\lambda]$``),
Pandoc's bookmark-string escaping emits literal ``\\textbackslash``,
``\\_``, ``\\^{}``, ``{[}``, ``{]}`` etc. Hyperref's ``pdfstring``
serializer then expands these as control sequences during the
``.aux`` write, which under heavy nesting blows the input-stack
("TeX capacity exceeded, sorry [input stack size=10000]") and aborts
the build mid-section.

This module rewrites the *second* (PDF-bookmark) argument of any
``\\texorpdfstring{X}{Y}`` to a plain ASCII string that contains no
control sequences — preserving the typeset form exactly while making
the bookmark text safe for hyperref to serialize.

Only the bookmark argument is rewritten; the typeset argument is
preserved byte-for-byte so the visible heading is unchanged.
"""

import re
from typing import Final

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

_TEXOR_RE: Final[re.Pattern[str]] = re.compile(
    r"\\texorpdfstring\s*"
    r"(?P<a>\{(?:[^{}]|\{[^{}]*\})*\})\s*"
    r"(?P<b>\{(?:[^{}]|\{[^{}]*\})*\})"
)

_PLAIN_REWRITES: Final[list[tuple[re.Pattern[str], str]]] = [
    # Common Pandoc plain-text escapes for special characters.
    (re.compile(r"\\textbackslash\s*\{?\s*\}?"), ""),
    (re.compile(r"\\_"), "_"),
    (re.compile(r"\\\^\s*\{?\s*\}?"), "^"),
    (re.compile(r"\\&"), "&"),
    (re.compile(r"\\\$"), "$"),
    (re.compile(r"\\#"), "#"),
    (re.compile(r"\\%"), "%"),
    (re.compile(r"\\\{"), "("),
    (re.compile(r"\\\}"), ")"),
    (re.compile(r"\\\["), "["),
    (re.compile(r"\\\]"), "]"),
    (re.compile(r"\{\[\}"), "["),
    (re.compile(r"\{\]\}"), "]"),
    (re.compile(r"\\textasciitilde\s*\{?\s*\}?"), "~"),
    (re.compile(r"\\textasciicircum\s*\{?\s*\}?"), "^"),
    # Strip remaining LaTeX text-mode commands like ``\text{...}`` →
    # ``...`` (drop the macro, keep the brace contents).
    (
        re.compile(
            r"\\(?:text|textit|textbf|textsf|texttt|emph|mathrm|mathbf|mathit|mathcal|mathbb|operatorname)"
            r"\s*\{([^{}]*)\}"
        ),
        r"\1",
    ),
    # Drop any other surviving LaTeX control word with optional brace arg.
    # ``\lambda``, ``\alpha``, ``\sum``, ``\langle``, etc. become a
    # space-padded version of the macro name (without the leading slash).
    (re.compile(r"\\([A-Za-z]+)"), r"\1"),
    # Collapse leftover braces.
    (re.compile(r"[{}]"), ""),
    # Collapse repeated whitespace.
    (re.compile(r"\s+"), " "),
]


def _sanitize_bookmark_arg(arg: str) -> str:
    """Return a hyperref-safe plain-text version of a bookmark argument.

    ``arg`` is expected to be the *brace-wrapped* second argument of a
    ``\\texorpdfstring`` call (including the outer ``{`` and ``}``).
    """
    if not (arg.startswith("{") and arg.endswith("}")):
        return arg
    inner = arg[1:-1]
    cleaned = inner
    for pattern, repl in _PLAIN_REWRITES:
        cleaned = pattern.sub(repl, cleaned)
    cleaned = cleaned.strip()
    return "{" + cleaned + "}"


def sanitize_texorpdfstring(tex_content: str) -> tuple[str, int]:
    """Replace every ``\\texorpdfstring{X}{Y}`` so ``Y`` is plain ASCII.

    Returns the rewritten content plus the number of substitutions made.
    The first (typeset) argument is preserved verbatim.
    """
    count = 0

    def _rewrite(match: re.Match[str]) -> str:
        nonlocal count
        a = match.group("a")
        b = match.group("b")
        new_b = _sanitize_bookmark_arg(b)
        if new_b != b:
            count += 1
        return f"\\texorpdfstring{a}{new_b}"

    new_content = _TEXOR_RE.sub(_rewrite, tex_content)
    if count:
        logger.info(
            "✓ Sanitized %d \\texorpdfstring bookmark argument(s) to prevent hyperref TeX-capacity overflow",
            count,
        )
    return new_content, count
