"""Replace prose unicode glyphs that body fonts (lmroman) cannot render.

Pandoc emits literal unicode characters into the LaTeX output. The default
body-text font family (Latin Modern Roman, ``lmroman10-regular``/``lmroman10-bold``)
does not cover symbols such as ``✓``, ``≈``, ``α``, ``σ``, ``≪``, ``↔``,
``≥``, ``≠``, ``∎``, ``○``, ``∣``, ``⚠``. xelatex emits a "Missing character"
warning for each occurrence and the PDF shows a ``U+FFFD`` replacement glyph.

This module rewrites those glyphs into the equivalent LaTeX command (e.g.
``✓`` → ``\\ensuremath{\\checkmark}``) **only outside Verbatim/Highlighting
blocks**, so Lean code listings (rendered through ``\\setmonofont{DejaVuSansMono}``
in :mod:`infrastructure.rendering._pdf_combined_renderer`) keep their literal
glyphs intact.

The rewrite preserves byte-for-byte content inside any
``\\begin{Highlighting}...\\end{Highlighting}``,
``\\begin{verbatim}...\\end{verbatim}``,
``\\begin{lstlisting}...\\end{lstlisting}``,
or ``\\verb<delim>...<delim>`` segment.
"""

from __future__ import annotations

import re
from typing import Final

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


# Map glyphs missing in lmroman/lmsans/lmtt to LaTeX commands that the
# Computer-Modern + amssymb font set CAN render.
# Verified empirically by scanning lmroman10-regular's cmap (see fontTools
# inspection on 2026-04-22). Each replacement is whitespace-neutral.
#
# Wrapped in ``\texorpdfstring{<typeset>}{<bookmark>}`` so the substitution is
# safe inside moving arguments — ``\section{…}``, ``\subsection{…}``,
# ``\caption{…}``, ``\addcontentsline{…}`` — without triggering the LaTeX
# ``Extra \fi`` errors that arise when ``\ensuremath`` is expanded during
# auxiliary-file write. ``\texorpdfstring`` is provided by hyperref (already
# loaded in :file:`preamble.md`); in body text it expands to its first
# argument, in PDF bookmarks/outlines it expands to the second (plain ASCII).


def _T(latex_cmd: str, plain: str) -> str:
    """Wrap a math-mode LaTeX command in :latex:`\\texorpdfstring{…}{…}`."""
    return rf"\texorpdfstring{{\ensuremath{{{latex_cmd}}}}}{{{plain}}}"


_PROSE_GLYPH_REPLACEMENTS: Final[dict[str, str]] = {
    # ── Marks, ticks, miscellaneous ──────────────────────────────────────
    "✓": _T(r"\checkmark", "[ok]"),
    "∎": _T(r"\blacksquare", "[QED]"),
    "○": _T(r"\circ", "o"),
    "⚠": r"\texorpdfstring{\textbf{!}}{!}",
    # ── Lower-case Greek (lmroman lacks these) ───────────────────────────
    "α": _T(r"\alpha", "alpha"),
    "β": _T(r"\beta", "beta"),
    "γ": _T(r"\gamma", "gamma"),
    "δ": _T(r"\delta", "delta"),
    "ε": _T(r"\varepsilon", "epsilon"),
    "ζ": _T(r"\zeta", "zeta"),
    "η": _T(r"\eta", "eta"),
    "θ": _T(r"\theta", "theta"),
    "ι": _T(r"\iota", "iota"),
    "κ": _T(r"\kappa", "kappa"),
    "λ": _T(r"\lambda", "lambda"),
    "μ": _T(r"\mu", "mu"),   # U+03BC GREEK SMALL LETTER MU
    "µ": _T(r"\mu", "mu"),   # U+00B5 MICRO SIGN — visually identical, semantic differ
    "𝜇": _T(r"\mu", "mu"),   # U+1D707 MATHEMATICAL ITALIC SMALL MU
    "ν": _T(r"\nu", "nu"),
    "ξ": _T(r"\xi", "xi"),
    "π": _T(r"\pi", "pi"),
    "ρ": _T(r"\rho", "rho"),
    "σ": _T(r"\sigma", "sigma"),
    "τ": _T(r"\tau", "tau"),
    "υ": _T(r"\upsilon", "upsilon"),
    "φ": _T(r"\varphi", "phi"),
    "χ": _T(r"\chi", "chi"),
    "ψ": _T(r"\psi", "psi"),
    "ω": _T(r"\omega", "omega"),
    # ── Upper-case Greek (those that differ from Latin letters) ──────────
    "Γ": _T(r"\Gamma", "Gamma"),
    "Δ": _T(r"\Delta", "Delta"),
    "Θ": _T(r"\Theta", "Theta"),
    "Λ": _T(r"\Lambda", "Lambda"),
    "Ξ": _T(r"\Xi", "Xi"),
    "Π": _T(r"\Pi", "Pi"),
    "Σ": _T(r"\Sigma", "Sigma"),
    "Φ": _T(r"\Phi", "Phi"),
    "Ψ": _T(r"\Psi", "Psi"),
    "Ω": _T(r"\Omega", "Omega"),
    # ── Set theory / logic ───────────────────────────────────────────────
    "∃": _T(r"\exists", "exists"),
    "∀": _T(r"\forall", "forall"),
    "∈": _T(r"\in", "in"),
    "∉": _T(r"\notin", "notin"),
    "∅": _T(r"\emptyset", "emptyset"),
    "⊆": _T(r"\subseteq", "subseteq"),
    "⊂": _T(r"\subset", "subset"),
    "⊇": _T(r"\supseteq", "supseteq"),
    "⊃": _T(r"\supset", "supset"),
    "∪": _T(r"\cup", "union"),
    "∩": _T(r"\cap", "intersection"),
    # ── Relations ────────────────────────────────────────────────────────
    "≈": _T(r"\approx", "~"),
    "≠": _T(r"\neq", "!="),
    "≡": _T(r"\equiv", "=="),
    "≤": _T(r"\leq", "<="),
    "≥": _T(r"\geq", ">="),
    "≪": _T(r"\ll", "<<"),
    "≫": _T(r"\gg", ">>"),
    "⊥": _T(r"\perp", "perp"),
    "⊤": _T(r"\top", "top"),
    # ── Arrows ───────────────────────────────────────────────────────────
    "→": _T(r"\to", "->"),
    "←": _T(r"\leftarrow", "<-"),
    "↔": _T(r"\leftrightarrow", "<->"),
    "↦": _T(r"\mapsto", "|->"),
    "⇒": _T(r"\Rightarrow", "=>"),
    "⇐": _T(r"\Leftarrow", "<="),
    "⇔": _T(r"\Leftrightarrow", "<=>"),
    # ── Operators ────────────────────────────────────────────────────────
    "∂": _T(r"\partial", "d"),
    "∫": _T(r"\int", "int"),
    "∇": _T(r"\nabla", "nabla"),
    "∞": _T(r"\infty", "inf"),
    # ∣ uses \textbar (text-mode pipe present in lmroman) rather than
    # \ensuremath{\mid} — the latter triggers a font-substitution chain
    # under xelatex+unicode-math that ends in lmroman, which lacks U+2223.
    "∣": r"\texorpdfstring{\textbar{}}{|}",
    "−": _T(r"-", "-"),  # U+2212 MINUS SIGN
    "·": _T(r"\cdot", "."),  # U+00B7 MIDDLE DOT
    "×": _T(r"\times", "x"),
    "÷": _T(r"\div", "/"),
    "±": _T(r"\pm", "+/-"),
    # ── Blackboard bold (number sets) ────────────────────────────────────
    "ℕ": _T(r"\mathbb{N}", "N"),
    "ℝ": _T(r"\mathbb{R}", "R"),
    "ℤ": _T(r"\mathbb{Z}", "Z"),
    "ℚ": _T(r"\mathbb{Q}", "Q"),
    "ℂ": _T(r"\mathbb{C}", "C"),
    "ℙ": _T(r"\mathbb{P}", "P"),
    "𝔼": _T(r"\mathbb{E}", "E"),
}


# Verbatim-style environments and inline-verbatim that must be preserved
# byte-for-byte. Order matters: the regex is anchored on the longer
# environment names first to avoid premature matches.
_PROTECTED_BLOCK_RE: Final[re.Pattern[str]] = re.compile(
    r"""
    (
        # Block verbatim environments (Pandoc's Highlighting wraps Lean code)
        \\begin\{Highlighting\}\[\][^\x00]*?\\end\{Highlighting\}
        | \\begin\{verbatim\}[^\x00]*?\\end\{verbatim\}
        | \\begin\{Verbatim\}\[?[^\]]*\]?[^\x00]*?\\end\{Verbatim\}
        | \\begin\{lstlisting\}\[?[^\]]*\]?[^\x00]*?\\end\{lstlisting\}
        # Inline verbatim: \verb followed by delimiter, content, same delimiter
        | \\verb \* ? (?P<delim>[^a-zA-Z\s]) .*? (?P=delim)
        # Pandoc's \passthrough{...} (used for inline code)
        | \\passthrough \{ [^{}]* \}
    )
    """,
    re.VERBOSE | re.DOTALL,
)


class UnicodeRemapResult:
    """Outcome of :func:`remap_prose_unicode`.

    Attributes:
        content: Rewritten LaTeX source.
        replacements: Total glyph→command substitutions applied.
        per_glyph_counts: Counts keyed by source glyph for diagnostics/logging.
    """

    __slots__ = ("content", "replacements", "per_glyph_counts")

    def __init__(
        self,
        content: str,
        replacements: int,
        per_glyph_counts: dict[str, int],
    ) -> None:
        self.content = content
        self.replacements = replacements
        self.per_glyph_counts = per_glyph_counts


def _rewrite_segment(text: str, counts: dict[str, int]) -> str:
    for glyph, replacement in _PROSE_GLYPH_REPLACEMENTS.items():
        if glyph in text:
            n = text.count(glyph)
            counts[glyph] = counts.get(glyph, 0) + n
            text = text.replace(glyph, replacement)
    return text


def remap_prose_unicode(tex_content: str) -> UnicodeRemapResult:
    """Rewrite prose-only glyphs to LaTeX commands, skipping verbatim blocks.

    The function tokenises ``tex_content`` into alternating
    ``(prose, protected, prose, protected, …)`` segments using
    :data:`_PROTECTED_BLOCK_RE` and only mutates the prose segments. Verbatim,
    Highlighting, ``\\verb``, ``lstlisting``, and ``\\passthrough{…}`` regions
    are returned byte-for-byte unchanged.

    Args:
        tex_content: Raw LaTeX source produced by Pandoc.

    Returns:
        :class:`UnicodeRemapResult` with the rewritten content and counts.
    """
    counts: dict[str, int] = {}
    parts: list[str] = []
    last_end = 0

    for match in _PROTECTED_BLOCK_RE.finditer(tex_content):
        prose_segment = tex_content[last_end : match.start()]
        if prose_segment:
            parts.append(_rewrite_segment(prose_segment, counts))
        parts.append(match.group(0))
        last_end = match.end()

    tail = tex_content[last_end:]
    if tail:
        parts.append(_rewrite_segment(tail, counts))

    rewritten = "".join(parts)
    total = sum(counts.values())
    if total:
        summary = ", ".join(f"{g}×{n}" for g, n in sorted(counts.items(), key=lambda kv: -kv[1]))
        logger.info("✓ Remapped %d prose unicode glyph(s) to LaTeX commands: %s", total, summary)
    else:
        logger.debug("No prose unicode glyphs required remapping")
    return UnicodeRemapResult(rewritten, total, counts)
