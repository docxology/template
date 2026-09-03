"""Shared contracts and geometry constants for accessible slide rendering.

Keeping policy objects and stable diagnostic construction in this dependency
leaf lets the AST, table, composition, and Reveal helpers remain cohesive
without importing one another cyclically.
"""

from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass
from typing import Any

from infrastructure.core.exceptions import RenderingError


# Stable 16:9 projection geometry for the opt-in accessible profile. The
# public policy's 80-word value is an absolute ceiling, not a promise that 80
# unusually long words fit on every frame. These conservative estimates are
# calibrated against the profile's 28/20/16-point native floors.
BASE_BODY_LINES_16_9 = 8
BODY_CHARACTERS_PER_LINE_20PT = 43
LIST_CHARACTERS_PER_LINE_20PT = 34
TITLE_CHARACTERS_PER_LINE_28PT = 36
MAX_TITLE_LINES_16_9 = 4
BODY_LINES_PER_EXTRA_TITLE_LINE = 2
BIBLIOGRAPHIC_CITATION_CHARACTERS = 32
# One-line title capacity at the 28-point floor. The continuation compactor
# subtracts the complete `` (part N)`` suffix before selecting visible words.
# The authored heading remains the frame's accessible name.
CONTINUATION_TITLE_TARGET_CHARS = TITLE_CHARACTERS_PER_LINE_28PT
TABLE_INTERCOLUMN_GUTTER_CHARACTERS = 1
TABLE_LIST_INDENT_WIDTH_UNITS = 3
TABLE_RULE_PADDING_LINES = 1
TABLE_MINIMUM_COLUMN_CHARACTERS = 2
TABLE_TOKEN_SAFETY_CHARACTERS = 1
_NARROW_PROPORTIONAL_GLYPHS = frozenset("fijltI1.,:;!|'\"")
_EXTRA_WIDE_PROPORTIONAL_GLYPHS = frozenset("MW")
_WIDE_PROPORTIONAL_GLYPHS = frozenset("m@%&")
_MEDIUM_WIDE_PROPORTIONAL_GLYPHS = frozenset("w")
# Latin Modern Sans spaces are narrower than the ordinary ``a`` unit, but a
# conservative 0.8 debit is needed once interword glue and author-year
# punctuation are composed across a complete 20-point prose line.  It keeps
# the measured 72-pair wide-glyph boundary inside eight lines while moving the
# known 80-pair and citation-rich overflow cases to preflight.
_PROPORTIONAL_SPACE_WIDTH_UNITS = 0.8
_TEX_MATH_SUPPORTED_ENVIRONMENTS = frozenset({"aligned"})
_TEX_MATH_COMMAND_WIDTH_UNITS = {
    # Display-style operators and arrows carry substantial side bearings in
    # Latin Modern Math. These calibrated ceilings make the last accepted
    # repetitions fit the same 43-unit one-column projection boundary.
    "sum": 3.0,
    "prod": 3.0,
    "coprod": 3.0,
    "bigcap": 3.0,
    "bigcup": 3.0,
    "int": 2.5,
    "oint": 2.5,
    "rightarrow": 2.2,
    "leftarrow": 2.2,
    "leftrightarrow": 3.0,
    "Rightarrow": 2.5,
    "Leftarrow": 2.5,
    "Leftrightarrow": 3.2,
    "longrightarrow": 3.0,
    "longleftarrow": 3.0,
    "longleftrightarrow": 3.8,
    # Font/style commands do not add a glyph; their braced content is still
    # priced character by character by the scanner below.
    "rm": 0.0,
    "mathrm": 0.0,
    "mathbf": 0.0,
    "mathit": 0.0,
    "mathsf": 0.0,
    "mathtt": 0.0,
    "operatorname": 0.0,
    "text": 0.0,
    "textrm": 0.0,
    "textsf": 0.0,
    "texttt": 0.0,
    "textnormal": 0.0,
    "mathbb": 0.0,
    "mathcal": 0.0,
    "boldsymbol": 0.0,
    "bm": 0.0,
    "frac": 0.0,
    "dfrac": 0.0,
    "tfrac": 0.0,
    "sqrt": 0.0,
    "left": 0.0,
    "right": 0.0,
    "big": 0.0,
    "Big": 0.0,
    "bigg": 0.0,
    "Bigg": 0.0,
    "bigl": 0.0,
    "bigr": 0.0,
    "Bigl": 0.0,
    "Bigr": 0.0,
    "biggl": 0.0,
    "biggr": 0.0,
    "Biggl": 0.0,
    "Biggr": 0.0,
    "limits": 0.0,
    "nolimits": 0.0,
    "substack": 0.0,
    "hat": 0.0,
    "widehat": 0.0,
    "bar": 0.0,
    "overline": 0.0,
    "underline": 0.0,
    "vec": 0.0,
    "dot": 0.0,
    "ddot": 0.0,
    "tilde": 0.0,
    "widetilde": 0.0,
    "underbrace": 0.0,
    "overbrace": 0.0,
    "alpha": 1.2,
    "beta": 1.2,
    "gamma": 1.2,
    "delta": 1.2,
    "epsilon": 1.2,
    "varepsilon": 1.2,
    "zeta": 1.2,
    "eta": 1.2,
    "theta": 1.2,
    "vartheta": 1.2,
    "iota": 1.2,
    "kappa": 1.2,
    "lambda": 1.2,
    "mu": 1.2,
    "nu": 1.2,
    "xi": 1.2,
    "pi": 1.2,
    "varpi": 1.2,
    "rho": 1.2,
    "varrho": 1.2,
    "sigma": 1.2,
    "varsigma": 1.2,
    "tau": 1.2,
    "upsilon": 1.2,
    "phi": 1.2,
    "varphi": 1.2,
    "chi": 1.2,
    "psi": 1.2,
    "omega": 1.2,
    "Gamma": 1.5,
    "Delta": 1.5,
    "Theta": 1.5,
    "Lambda": 1.5,
    "Xi": 1.5,
    "Pi": 1.5,
    "Sigma": 1.5,
    "Upsilon": 1.5,
    "Phi": 1.5,
    "Psi": 1.5,
    "Omega": 1.5,
    "log": 3.0,
    "ln": 2.0,
    "exp": 3.0,
    "sin": 3.0,
    "cos": 3.0,
    "tan": 3.0,
    "min": 3.0,
    "max": 3.0,
    "argmin": 6.0,
    "argmax": 6.0,
    "lim": 3.0,
    "Pr": 2.0,
    "mid": 0.8,
    "vert": 0.8,
    "Vert": 1.2,
    "parallel": 1.5,
    "perp": 1.5,
    "le": 1.5,
    "leq": 1.5,
    "ge": 1.5,
    "geq": 1.5,
    "neq": 1.5,
    "approx": 1.5,
    "sim": 1.5,
    "simeq": 1.5,
    "equiv": 1.5,
    "propto": 1.5,
    "in": 1.2,
    "notin": 1.5,
    "subset": 1.5,
    "subseteq": 1.5,
    "supset": 1.5,
    "supseteq": 1.5,
    "cup": 1.5,
    "cap": 1.5,
    "cdot": 1.0,
    "times": 1.5,
    "pm": 1.5,
    "mp": 1.5,
    "oplus": 1.5,
    "otimes": 1.5,
    "partial": 1.2,
    "nabla": 1.5,
    "infty": 1.5,
    "ell": 1.0,
    "to": 2.2,
    "mapsto": 2.2,
    "quad": 2.0,
    "qquad": 4.0,
    "calD": 1.5,
    "cogstate": 1.5,
    "gen": 1.5,
    "rank": 4.0,
}
SEMANTIC_BREAK_SUFFIXES = (".", "?", "!", ";", ":", "—")
CROSS_REFERENCE_LABELS = {
    "alg": "alg.",
    "cor": "cor.",
    "def": "def.",
    "eq": "eq.",
    "ex": "ex.",
    "fig": "fig.",
    "lem": "lem.",
    "lst": "lst.",
    "prop": "prop.",
    "rem": "rem.",
    "sec": "sec.",
    "subsec": "sec.",
    "tbl": "tbl.",
    "thm": "thm.",
}
CLAUSE_COORDINATORS = {
    "although",
    "and",
    "because",
    "but",
    "so",
    "whereas",
    "while",
    "which",
    "yet",
}


def tex_hyphen_segments(token: str) -> list[str]:
    """Return indivisible segments around TeX's explicit hyphen breaks."""

    if "-" not in token:
        return [token] if token else []
    segments: list[str] = []
    start = 0
    for match in re.finditer("-", token):
        segment = token[start : match.end()]
        if segment:
            segments.append(segment)
        start = match.end()
    tail = token[start:]
    if tail:
        segments.append(tail)
    return segments


def proportional_text_width_units(text: str) -> int:
    """Return calibrated 20-point Latin Modern Sans width units.

    One unit is the measured width of the ordinary ``a``/``x`` class on the
    accessible 16:9 Beamer canvas. Class ceilings are calibrated at the last
    clean one-column repetitions: 22 ``W``, 30 generic uppercase/``w``, and 26
    ``m`` glyphs. The next repetition is rejected by preflight, before TeX can
    produce an overfull box. Full-width Unicode remains conservatively wider.
    """

    width = 0.0
    for character in text:
        if character.isspace():
            width += _PROPORTIONAL_SPACE_WIDTH_UNITS
        elif unicodedata.east_asian_width(character) in {"F", "W"}:
            width += 2.0
        elif character in _EXTRA_WIDE_PROPORTIONAL_GLYPHS:
            width += 1.95
        elif character in _WIDE_PROPORTIONAL_GLYPHS:
            width += 1.65
        elif character in _MEDIUM_WIDE_PROPORTIONAL_GLYPHS:
            width += 1.43
        elif character in _NARROW_PROPORTIONAL_GLYPHS:
            width += 0.55
        elif character.isupper():
            width += 1.43
        elif character.isdigit():
            width += 0.9
        elif character in "()[]{}-/\\":
            width += 0.7
        else:
            width += 1.0
    return max(1, math.ceil(width)) if text else 0


def tex_math_width_units(source: str) -> int:
    """Return a conservative visible-width bound for inline TeX math.

    Control-word spelling is not itself visible, so known operators use
    calibrated Latin Modern Math glyph ceilings. Unknown commands fail closed
    by retaining a bounded spelling-derived debit instead of collapsing every
    command to one generic ``x``. Braces, scripts, and font selectors contribute
    no glyph on their own; their visible operands remain in the scan.
    """

    width = 0.0
    index = 0
    while index < len(source):
        character = source[index]
        if character == "\\":
            command_match = re.match(r"[A-Za-z]+", source[index + 1 :])
            if command_match is not None:
                command = command_match.group(0)
                if command in {"begin", "end"}:
                    environment_match = re.match(
                        r"\{([A-Za-z*]+)\}",
                        source[index + len(command) + 1 :],
                    )
                    if environment_match is not None and environment_match.group(1) in _TEX_MATH_SUPPORTED_ENVIRONMENTS:
                        index += len(command) + len(environment_match.group(0)) + 1
                        continue
                width += _TEX_MATH_COMMAND_WIDTH_UNITS.get(command, min(6.0, max(1.5, len(command) * 0.8)))
                index += len(command) + 1
                continue
            if index + 1 < len(source):
                escaped = source[index + 1]
                width += 0.5 if escaped in ",;! " else proportional_text_width_units(escaped)
                index += 2
                continue
        if character not in "{}_^" and not character.isspace():
            width += proportional_text_width_units(character)
        index += 1
    return max(1, math.ceil(width)) if source else 0


def unsupported_tex_math_commands(source: str) -> tuple[str, ...]:
    """Return TeX control words without an explicit geometry contract."""

    commands: set[str] = set()
    if re.search(r"\\\\\s*\[[^\]]*\]", source):
        # TeX permits a physical vertical skip after an aligned row separator,
        # for example ``\\[10cm]``. The accessible profile does not model
        # author-selected physical spacing, so it must fail before rendering.
        commands.add("row-spacing")
    index = 0
    while index < len(source):
        if source[index] != "\\":
            index += 1
            continue
        if index + 1 < len(source) and source[index + 1] == "\\":
            # An aligned/substack row separator is one TeX control symbol.
            # The character following the second slash begins ordinary math;
            # it must never be re-read as a control word (``\\\\x`` is a row
            # break followed by ``x``, not the unsupported command ``\\x``).
            index += 2
            continue
        command_match = re.match(r"[A-Za-z]+", source[index + 1 :])
        if command_match is None:
            index += 2
            continue
        command = command_match.group(0)
        commands.add(command)
        index += len(command) + 1
    environment_controls = [
        (match.group(1), match.group(2)) for match in re.finditer(r"\\(begin|end)\{([A-Za-z*]+)\}", source)
    ]
    environment_stack: list[str] = []
    environments_valid = True
    for action, name in environment_controls:
        if name not in _TEX_MATH_SUPPORTED_ENVIRONMENTS:
            environments_valid = False
            continue
        if action == "begin":
            environment_stack.append(name)
        elif not environment_stack or environment_stack.pop() != name:
            environments_valid = False
    environments_valid = environments_valid and not environment_stack
    unsupported: set[str] = set()
    for command in commands:
        if command in {"begin", "end"}:
            if not environments_valid or not environment_controls:
                unsupported.add(command)
            continue
        if command not in _TEX_MATH_COMMAND_WIDTH_UNITS:
            unsupported.add(command)
    return tuple(sorted(unsupported))


def tex_math_vertical_line_demand(source: str) -> int:
    """Return conservative projection-line demand for supported TeX math.

    The accessible 16:9/20-point boundary is empirically clean through sixteen
    nested fraction controls and overflows at seventeen. Two nested fraction
    levels therefore consume one of the profile's eight body-line units. The
    count deliberately overprices sequential fractions. ``aligned`` is clean
    through six rows and overflows at seven, so its environment contributes two
    fixed lines beyond its authored row count. A substack is typeset more
    compactly: fourteen rows are clean and fifteen overflow, represented as two
    authored rows per body line plus one fixed line. Horizontal composition is
    priced independently.
    """

    fraction_count = len(re.findall(r"\\(?:dfrac|frac|tfrac)\b", source))
    demands = [max(1, math.ceil(fraction_count / 2))]
    for match in re.finditer(
        r"\\begin\{aligned\}(.*?)\\end\{aligned\}",
        source,
        flags=re.DOTALL,
    ):
        demands.append(_tex_math_row_count(match.group(1)) + 2)
    for argument in _tex_braced_command_arguments(source, "substack"):
        demands.append(math.ceil(_tex_math_row_count(argument) / 2) + 1)
    return max(demands)


def _tex_math_row_count(source: str) -> int:
    """Count authored TeX rows without re-reading the second row-break slash."""

    row_breaks = 0
    index = 0
    while index < len(source) - 1:
        if source[index : index + 2] == "\\\\":
            row_breaks += 1
            index += 2
            continue
        index += 1
    return row_breaks + 1


def _tex_braced_command_arguments(source: str, command: str) -> tuple[str, ...]:
    """Return balanced braced arguments for one supported TeX command."""

    arguments: list[str] = []
    pattern = re.compile(rf"\\{re.escape(command)}\s*\{{")
    for match in pattern.finditer(source):
        opening = match.end() - 1
        depth = 1
        index = opening + 1
        while index < len(source) and depth:
            character = source[index]
            if character == "\\" and index + 1 < len(source):
                index += 2
                continue
            if character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
            index += 1
        if depth == 0:
            arguments.append(source[opening + 1 : index - 1])
    return tuple(arguments)


@dataclass(frozen=True)
class AccessibleSlidePolicy:
    """Fail-closed density and typography policy for presentation derivatives."""

    max_prose_words: int = 80
    max_table_rows: int = 8
    min_figure_area_percent: int = 70
    title_font_pt: int = 28
    body_font_pt: int = 20
    figure_label_font_pt: int = 16
    reader_href: str = "../web/index.html"


@dataclass(frozen=True)
class AccessibleSlideComposition:
    """One deterministic AST composition result and its review counts."""

    document: dict[str, Any]
    frame_count: int
    section_divider_count: int
    excerpted_table_count: int
    figure_frame_count: int


@dataclass(frozen=True)
class _Frame:
    """One internal semantic frame before Pandoc block serialization."""

    title: dict[str, Any]
    blocks: tuple[dict[str, Any], ...]
    kind: str
    continuation: int


def density_error(
    code: str,
    message: str,
    *,
    source: str,
    heading: str,
    **context: object,
) -> RenderingError:
    """Return one actionable, stable accessible-slide density diagnostic."""

    return RenderingError(
        f"[{code}] {message}",
        context={"source": source, "heading": heading, "diagnostic_code": code, **context},
        suggestions=[
            "Add a semantic subheading or split the indivisible source block.",
            "Keep the complete material in the canonical HTML manuscript and present a bounded excerpt.",
        ],
    )


__all__ = ["AccessibleSlideComposition", "AccessibleSlidePolicy"]
