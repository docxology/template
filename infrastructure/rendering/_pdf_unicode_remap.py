"""Replace prose unicode glyphs that body fonts (lmroman) cannot render.

Pandoc emits literal unicode characters into the LaTeX output. The default
body-text font family (Latin Modern Roman, ``lmroman10-regular``/``lmroman10-bold``)
does not cover symbols such as ``✓``, ``≈``, ``α``, ``σ``, ``≪``, ``↔``,
``≥``, ``≠``, ``∎``, ``○``, ``∣``, ``⚠``. xelatex emits a "Missing character"
warning for each occurrence and the PDF shows a ``U+FFFD`` replacement glyph.

This module rewrites those glyphs into the equivalent LaTeX command (e.g.
``✓`` → ``\\ensuremath{\\checkmark}``) **outside literal Verbatim-style
blocks**.

The rewrite preserves byte-for-byte content inside any
``\\begin{Highlighting}[]...\\end{Highlighting}``,
``\\begin{verbatim}...\\end{verbatim}``,
``\\begin{lstlisting}...\\end{lstlisting}``,
or ``\\verb<delim>...<delim>`` segment.
"""

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


def _TEXT(latex_cmd: str, plain: str) -> str:
    """Wrap a text-mode LaTeX command in :latex:`\\texorpdfstring{…}{…}`."""
    return rf"\texorpdfstring{{{latex_cmd}}}{{{plain}}}"


_PROSE_GLYPH_REPLACEMENTS: Final[dict[str, str]] = {
    # ── Marks, ticks, miscellaneous ──────────────────────────────────────
    "✓": _T(r"\checkmark", "[ok]"),
    "∎": _T(r"\blacksquare", "[QED]"),
    "○": _T(r"\circ", "o"),
    "⚠": r"\texorpdfstring{\textbf{!}}{!}",
    "★": _TEXT(r"*", "*"),
    "☆": _T(r"\circ", "o"),
    "⚡": _TEXT(r"[energy]", "energy"),
    "🔬": _TEXT(r"", ""),
    "🫛": _TEXT(r"[pea genetics]", "pea genetics"),
    "📊": _TEXT(r"[data]", "data"),
    "🌿": _TEXT(r"[plant]", "plant"),
    "💧": _TEXT(r"[water]", "water"),
    "🌬️": _TEXT(r"[wind]", "wind"),
    "🌬": _TEXT(r"[wind]", "wind"),
    "☀️": _TEXT(r"[sunlight]", "sunlight"),
    "☀": _TEXT(r"[sunlight]", "sunlight"),
    "⚖️": _TEXT(r"[balance]", "balance"),
    "⚖": _TEXT(r"[balance]", "balance"),
    "️": _TEXT(r"", ""),
    "❤️": _TEXT(r"[heart]", "heart"),
    "🫁": _TEXT(r"[lungs]", "lungs"),
    "💉": _TEXT(r"[injection]", "injection"),
    "💨": _TEXT(r"[flow]", "flow"),
    "├": _TEXT(r"|--", "|--"),
    "└": _TEXT(r"`--", "`--"),
    "│": _TEXT(r"|", "|"),
    "─": _TEXT(r"-", "-"),
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
    "μ": _T(r"\mu", "mu"),  # U+03BC GREEK SMALL LETTER MU
    "µ": _T(r"\mu", "mu"),  # U+00B5 MICRO SIGN — visually identical, semantic differ
    "𝜇": _T(r"\mu", "mu"),  # U+1D707 MATHEMATICAL ITALIC SMALL MU
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
    "∼": _TEXT(r"about", "~"),
    "≠": _T(r"\neq", "!="),
    "≡": _T(r"\equiv", "=="),
    "≤": _T(r"\leq", "<="),
    "≥": _TEXT(r"\textgreater{}=", ">="),
    "≪": _T(r"\ll", "<<"),
    "≫": _T(r"\gg", ">>"),
    "⊥": _T(r"\perp", "perp"),
    "⊤": _T(r"\top", "top"),
    "⊣": _T(r"\dashv", "-|"),
    # ── Arrows ───────────────────────────────────────────────────────────
    "→": _T(r"\to", "->"),
    "←": _T(r"\leftarrow", "<-"),
    "↑": _T(r"\uparrow", "up"),
    "↓": _T(r"\downarrow", "down"),
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
    "∝": _T(r"\propto", "propto"),
    "√": _TEXT(r"\(\sqrt{\;}\)", "sqrt"),
    "∘": _T(r"\circ", "o"),  # U+2218 RING OPERATOR (function composition)
    # ∣ uses a literal text pipe rather than \ensuremath{\mid}; the latter
    # triggers a font-substitution chain under xelatex+unicode-math that ends
    # in a text font without U+2223.
    "∣": _TEXT(r"\textbar", "|"),
    "−": _T(r"-", "-"),  # U+2212 MINUS SIGN
    "·": _T(r"\cdot", "."),  # U+00B7 MIDDLE DOT
    "⋅": _T(r"\cdot", "."),
    "×": _T(r"\times", "x"),
    "÷": _T(r"\div", "/"),
    "±": _T(r"\pm", "+/-"),
    "⇌": _T(r"\rightleftharpoons", "<=>"),
    "′": _TEXT(r"'", "'"),
    "″": _TEXT(r"''", "''"),
    # ── Unicode super/subscripts emitted by prose or captions ───────────
    "⁰": _TEXT(r"\textsuperscript{0}", "0"),
    "¹": _TEXT(r"\textsuperscript{1}", "1"),
    "²": _TEXT(r"\textsuperscript{2}", "2"),
    "³": _TEXT(r"\textsuperscript{3}", "3"),
    "⁴": _TEXT(r"\textsuperscript{4}", "4"),
    "⁵": _TEXT(r"\textsuperscript{5}", "5"),
    "⁶": _TEXT(r"\textsuperscript{6}", "6"),
    "⁷": _TEXT(r"\textsuperscript{7}", "7"),
    "⁸": _TEXT(r"\textsuperscript{8}", "8"),
    "⁹": _TEXT(r"\textsuperscript{9}", "9"),
    "⁺": _TEXT(r"\textsuperscript{+}", "+"),
    "⁻": _TEXT(r"\textsuperscript{-}", "-"),
    "ⁿ": _TEXT(r"\textsuperscript{n}", "n"),
    "₀": _TEXT(r"\textsubscript{0}", "0"),
    "₁": _TEXT(r"\textsubscript{1}", "1"),
    "₂": _TEXT(r"\textsubscript{2}", "2"),
    "₃": _TEXT(r"\textsubscript{3}", "3"),
    "₄": _TEXT(r"\textsubscript{4}", "4"),
    "₅": _TEXT(r"\textsubscript{5}", "5"),
    "₆": _TEXT(r"\textsubscript{6}", "6"),
    "₇": _TEXT(r"\textsubscript{7}", "7"),
    "₈": _TEXT(r"\textsubscript{8}", "8"),
    "₉": _TEXT(r"\textsubscript{9}", "9"),
    "ₐ": _TEXT(r"\textsubscript{a}", "a"),
    "ₑ": _TEXT(r"\textsubscript{e}", "e"),
    "ₘ": _TEXT(r"\textsubscript{m}", "m"),
    "ₙ": _TEXT(r"\textsubscript{n}", "n"),
    "ₓ": _TEXT(r"\textsubscript{x}", "x"),
    "ᵢ": _TEXT(r"\textsubscript{i}", "i"),
    # ── Long arrows / implications (use longer forms when emitted by
    #    Pandoc as Unicode rather than via mathtools macros) ──────────────
    "⟹": _T(r"\Longrightarrow", "==>"),  # U+27F9
    "⟸": _T(r"\Longleftarrow", "<=="),  # U+27F8
    "⟺": _T(r"\Longleftrightarrow", "<=>"),  # U+27FA
    "⟶": _T(r"\longrightarrow", "->"),  # U+27F6
    "⟵": _T(r"\longleftarrow", "<-"),  # U+27F5
    # ── Mathematical italic (U+1D6xx range) — Pandoc occasionally emits
    #    these in math contexts that escape into prose mode ───────────────
    "𝛼": _TEXT(r"alpha", "alpha"),  # U+1D6FC
    "𝛽": _TEXT(r"beta", "beta"),  # U+1D6FD
    "𝛾": _T(r"\gamma", "gamma"),  # U+1D6FE
    "𝛿": _T(r"\delta", "delta"),  # U+1D6FF
    "𝜀": _T(r"\varepsilon", "epsilon"),  # U+1D700
    "𝜂": _T(r"\eta", "eta"),  # U+1D702
    "𝜃": _T(r"\theta", "theta"),  # U+1D703
    "𝜅": _T(r"\kappa", "kappa"),  # U+1D705
    "𝜆": _T(r"\lambda", "lambda"),  # U+1D706
    "𝜈": _T(r"\nu", "nu"),  # U+1D708
    "𝜉": _T(r"\xi", "xi"),  # U+1D709
    "𝜋": _T(r"\pi", "pi"),  # U+1D70B
    "𝜌": _T(r"\rho", "rho"),  # U+1D70C
    "𝜎": _T(r"\sigma", "sigma"),  # U+1D70E
    "𝜏": _T(r"\tau", "tau"),  # U+1D70F
    "𝜑": _T(r"\varphi", "phi"),  # U+1D711
    "𝜒": _T(r"\chi", "chi"),  # U+1D712
    "𝜓": _T(r"\psi", "psi"),  # U+1D713
    "𝜔": _T(r"\omega", "omega"),  # U+1D714
    # ── Blackboard bold (number sets) ────────────────────────────────────
    "ℕ": _T(r"\mathbb{N}", "N"),
    "ℝ": _T(r"\mathbb{R}", "R"),
    "ℤ": _T(r"\mathbb{Z}", "Z"),
    "ℚ": _T(r"\mathbb{Q}", "Q"),
    "ℂ": _T(r"\mathbb{C}", "C"),
    "ℙ": _T(r"\mathbb{P}", "P"),
    "𝔼": _T(r"\mathbb{E}", "E"),
}

_LATEX_TEXT_MACRO_REPLACEMENTS: Final[dict[str, str]] = {
    r"\textasciitilde{}": "about ",
    r"\textasciitilde": "about ",
    r"\textbar{}": "pipe",
    r"\textbar": "pipe",
    r"\$\rightarrow\$": "->",
    r"\$\sim\$": "about",
}

_TEXT_MODE_MATH_COMMAND_REPLACEMENTS: Final[dict[str, str]] = {
    "alpha": "alpha",
    "beta": "beta",
    "gamma": "gamma",
    "delta": "delta",
    "epsilon": "epsilon",
    "theta": "theta",
    "kappa": "kappa",
    "lambda": "lambda",
    "mu": "mu",
    "pi": "pi",
    "sigma": "sigma",
    "tau": "tau",
    "phi": "phi",
    "chi": "chi",
    "psi": "psi",
    "omega": "omega",
    "Delta": "Delta",
    "Psi": "Psi",
    "to": "->",
    "rightarrow": "->",
    "leftarrow": "<-",
    "leftrightarrow": "<->",
    "sim": "about",
    "approx": "about",
    "geq": ">=",
    "leq": "<=",
    "mid": "|",
}
_TEXT_MODE_MATH_COMMAND_RE: Final[re.Pattern[str]] = re.compile(
    r"\\(?P<name>"
    + "|".join(sorted(map(re.escape, _TEXT_MODE_MATH_COMMAND_REPLACEMENTS), key=len, reverse=True))
    + r")(?![A-Za-z])"
)

_MATH_ENVIRONMENTS: Final[tuple[str, ...]] = (
    "equation",
    "equation*",
    "align",
    "align*",
    "aligned",
    "gather",
    "gather*",
    "multline",
    "multline*",
    "split",
    "cases",
)
_MATH_BOUNDARY_RE: Final[re.Pattern[str]] = re.compile(
    r"\\\(|\\\[|\\begin\{(?:" + "|".join(re.escape(name) for name in _MATH_ENVIRONMENTS) + r")\}"
)
_TEXT_MODE_MATH_PROTECTED_RE: Final[re.Pattern[str]] = re.compile(
    r"\\texorpdfstring\{\\ensuremath\{[^{}]*\}\}\{[^{}]*\}"
    r"|\\texorpdfstring\{[^{}]*\}\{[^{}]*\}"
    r"|\\ensuremath\{[^{}]*\}"
)

# Verbatim-style environments and inline-verbatim that must be preserved
# byte-for-byte. Order matters: the regex is anchored on the longer
# environment names first to avoid premature matches.
_PROTECTED_BLOCK_RE: Final[re.Pattern[str]] = re.compile(
    r"""
    (
        # Block verbatim environments (including Pandoc's Highlighting)
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


def _rewrite_latex_text_macros(text: str) -> str:
    """Replace text-symbol macros that expand to unsupported glyphs."""
    parts: list[str] = []
    last_end = 0

    for protected in _TEXT_MODE_MATH_PROTECTED_RE.finditer(text):
        if protected.start() > last_end:
            segment = text[last_end : protected.start()]
            for macro, replacement in _LATEX_TEXT_MACRO_REPLACEMENTS.items():
                segment = segment.replace(macro, replacement)
            parts.append(segment)
        parts.append(protected.group(0))
        last_end = protected.end()

    if last_end < len(text):
        segment = text[last_end:]
        for macro, replacement in _LATEX_TEXT_MACRO_REPLACEMENTS.items():
            segment = segment.replace(macro, replacement)
        parts.append(segment)

    return "".join(parts)


def _rewrite_text_mode_math_commands(text: str) -> tuple[str, int]:
    """Replace math commands that Pandoc left in prose mode.

    Pandoc's Markdown parser treats fragments such as ``$\\sim$16`` and
    ``$\\alpha$1$\\to$4`` as literal text with bare LaTeX commands. Under
    ``unicode-math`` those commands expand to Unicode mathematical glyphs in
    the body font, producing missing-character warnings. Keep real math spans
    and math environments unchanged, but make accidental text-mode commands
    printable and screen-reader-friendly.
    """
    begin_doc = text.find(r"\begin{document}")
    if begin_doc < 0:
        return text, 0

    preamble = text[:begin_doc]
    body = text[begin_doc:]
    out: list[str] = []
    replacements = 0
    i = 0

    while i < len(body):
        boundary = _MATH_BOUNDARY_RE.search(body, i)
        if boundary is None:
            rewritten, count = _rewrite_text_mode_math_segment(body[i:])
            out.append(rewritten)
            replacements += count
            break

        if boundary.start() > i:
            rewritten, count = _rewrite_text_mode_math_segment(body[i : boundary.start()])
            out.append(rewritten)
            replacements += count
            i = boundary.start()
            continue

        math_start = _math_region_start(body, boundary.start())
        if math_start is not None:
            end_marker = math_start
            end = body.find(end_marker, boundary.end())
            if end >= 0:
                end += len(end_marker)
                out.append(body[i:end])
                i = end
                continue

        env_name = _math_environment_name(body, boundary.start())
        if env_name is not None:
            end_marker = rf"\end{{{env_name}}}"
            end = body.find(end_marker, boundary.end())
            if end >= 0:
                end += len(end_marker)
                out.append(body[i:end])
                i = end
                continue

        # Malformed math delimiter or environment: keep the byte and continue.
        out.append(body[i : i + 1])
        i += 1

    return preamble + "".join(out), replacements


def _rewrite_text_mode_math_segment(segment: str) -> tuple[str, int]:
    replacements = 0

    def replace(match: re.Match[str]) -> str:
        """Replace matched text."""
        nonlocal replacements
        replacements += 1
        return _TEXT_MODE_MATH_COMMAND_REPLACEMENTS[match.group("name")]

    parts: list[str] = []
    last_end = 0
    for protected in _TEXT_MODE_MATH_PROTECTED_RE.finditer(segment):
        if protected.start() > last_end:
            parts.append(_TEXT_MODE_MATH_COMMAND_RE.sub(replace, segment[last_end : protected.start()]))
        parts.append(protected.group(0))
        last_end = protected.end()
    if last_end < len(segment):
        parts.append(_TEXT_MODE_MATH_COMMAND_RE.sub(replace, segment[last_end:]))
    return "".join(parts), replacements


def _math_region_open(text: str, index: int) -> str:
    if text.startswith(r"\(", index):
        return r"\("
    if text.startswith(r"\[", index):
        return r"\["
    return ""


def _math_region_start(text: str, index: int) -> str | None:
    if text.startswith(r"\(", index):
        return r"\)"
    if text.startswith(r"\[", index):
        return r"\]"
    return None


def _math_environment_name(text: str, index: int) -> str | None:
    for name in _MATH_ENVIRONMENTS:
        if text.startswith(rf"\begin{{{name}}}", index):
            return name
    return None


def remap_prose_unicode(tex_content: str) -> UnicodeRemapResult:
    """Rewrite prose-only glyphs to LaTeX commands, skipping verbatim blocks.

    The function tokenises ``tex_content`` into alternating
    ``(prose, protected, prose, protected, …)`` segments using
    :data:`_PROTECTED_BLOCK_RE`. Prose segments receive LaTeX-safe replacements.
    ``Highlighting``, verbatim, ``\\verb``, ``lstlisting``, and
    ``\\passthrough{…}`` regions are returned byte-for-byte unchanged.

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

    rewritten = _rewrite_latex_text_macros("".join(parts))
    rewritten, text_mode_math_count = _rewrite_text_mode_math_commands(rewritten)
    total = sum(counts.values())
    if total:
        summary = ", ".join(f"{g}×{n}" for g, n in sorted(counts.items(), key=lambda kv: -kv[1]))
        logger.info("✓ Remapped %d Unicode glyph(s) to PDF-safe output: %s", total, summary)
    else:
        logger.debug("No prose unicode glyphs required remapping")
    if text_mode_math_count:
        logger.info("✓ Rewrote %d text-mode math command(s) to PDF-safe text", text_mode_math_count)
    return UnicodeRemapResult(rewritten, total, counts)
