"""Cross-deck LaTeX reference resolution for per-section slide decks.

Each section deck is a standalone Pandoc/Beamer build, so raw-LaTeX
``\\ref{...}`` / ``\\eqref{...}`` commands whose ``\\label`` lives in a
*different* section's deck compile to "??" — xelatex never sees the
defining label. The combined manuscript PDF *does* resolve every label,
and its retained ``.aux`` file (``output/pdf/_combined_manuscript.aux``)
carries the ground-truth ``\\newlabel{label}{{number}{page}...}`` map.

This module provides the parsing and substitution pass used by
:class:`infrastructure.rendering.slides_renderer.SlidesRenderer`:

* :func:`parse_aux_label_numbers` parses the combined build's ``.aux``
  into ``{label -> printed number}``. Missing/unreadable aux, truncated
  entries, and ``@cref`` bookkeeping labels are all skipped silently —
  parsing never raises.
* :func:`resolve_cross_deck_references` rewrites ``\\ref{L}`` to the
  literal printed number (and ``\\eqref{L}`` to ``(N)``) for every label
  ``L`` that is **not** defined inside the deck's own ``.tex`` source.
  Within-deck references are left alone so Beamer numbers them natively;
  labels absent from the aux map are left untouched and reported back to
  the caller. Direct standalone renders remain fail-open, while the canonical
  post-combined refresh rejects unresolved non-section labels in strict mode.

The numbers substituted here match the combined PDF exactly because they
come *from* the combined PDF's own auxiliary file. Direct standalone slide
renders remain fail-open when no AUX is available. The canonical rendering
pipeline instead clears any stale combined AUX before the combined build,
validates the newly produced label map, and then refreshes each Beamer deck;
it therefore does not require a second pipeline invocation to resolve
cross-deck references.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

#: Basename of the combined manuscript's LaTeX auxiliary file, relative to
#: the configured ``pdf_dir`` (see ``_pdf_latex_pipeline`` /
#: ``pdf_renderer`` which compile ``_combined_manuscript.tex`` in place).
COMBINED_AUX_BASENAME = "_combined_manuscript.aux"

# \newlabel{<label>}{  — the label itself never contains braces.
_NEWLABEL_RE = re.compile(r"\\newlabel\{([^{}]+)\}\{")

# ``Section~\ref{L}`` reaches post-Pandoc Beamer as
# ``Section\textasciitilde{}\ref{L}``.  Capture that escaped nonbreaking
# join with the reference so successful numeric substitution can restore a
# real TeX nonbreaking space rather than project a visible tilde.  The leading
# reference backslash still keeps \pageref / \autoref / \nameref / \cref
# tails from matching ("...ref" without their own backslash).
_REF_RE = re.compile(
    r"(?P<escaped_join>\\textasciitilde\{\})?"
    r"(?P<authored_open>\()?"
    r"\\(?P<command>eqref|ref)\{(?P<label>[^{}]+)\}"
)

# \label{L} occurrences inside the deck's own generated .tex source.
_LABEL_RE = re.compile(r"\\label\{([^{}]+)\}")

#: Printed numbers we trust for literal substitution: plain section /
#: theorem / equation counters like ``5``, ``2.3.1``, ``A.2``. Anything
#: containing macros (e.g. hyperref's ``\M@TitleReference`` wrapping) is
#: skipped so we never inject unexpanded TeX into a slide deck.
_SAFE_NUMBER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.\-]*$")

_LITERAL_ENVIRONMENT_START_RE = re.compile(r"\\begin\{(?P<environment>verbatim\*?|Verbatim|lstlisting|minted)\}")
_INLINE_VERB_START_RE = re.compile(r"\\verb\*?(?P<delimiter>[^A-Za-z0-9\s])")


def _is_escaped_character(text: str, index: int) -> bool:
    """Return whether ``text[index]`` follows an odd backslash run."""

    backslashes = 0
    cursor = index - 1
    while cursor >= 0 and text[cursor] == "\\":
        backslashes += 1
        cursor -= 1
    return backslashes % 2 == 1


def _tex_literal_ranges(tex_content: str) -> tuple[tuple[int, int], ...]:
    """Locate comments and verbatim-like TeX regions in source order.

    Cross-reference rewriting is a prose transformation.  Literal examples
    inside comments, ``\\verb``, or code-listing environments must remain
    byte-identical and must not become strict-render findings.
    """

    ranges: list[tuple[int, int]] = []
    cursor = 0
    length = len(tex_content)
    while cursor < length:
        character = tex_content[cursor]
        if character == "%" and not _is_escaped_character(tex_content, cursor):
            end = tex_content.find("\n", cursor)
            end = length if end < 0 else end
            ranges.append((cursor, end))
            cursor = end
            continue

        if character == "\\" and not _is_escaped_character(tex_content, cursor):
            environment = _LITERAL_ENVIRONMENT_START_RE.match(tex_content, cursor)
            if environment is not None:
                end_token = rf"\end{{{environment.group('environment')}}}"
                end_start = tex_content.find(end_token, environment.end())
                end = length if end_start < 0 else end_start + len(end_token)
                ranges.append((cursor, end))
                cursor = end
                continue

            inline_verb = _INLINE_VERB_START_RE.match(tex_content, cursor)
            if inline_verb is not None:
                delimiter = inline_verb.group("delimiter")
                line_end = tex_content.find("\n", inline_verb.end())
                search_end = length if line_end < 0 else line_end
                delimiter_end = tex_content.find(delimiter, inline_verb.end(), search_end)
                end = search_end if delimiter_end < 0 else delimiter_end + 1
                ranges.append((cursor, end))
                cursor = end
                continue
        cursor += 1
    return tuple(ranges)


def transform_tex_prose(tex_content: str, transform: Callable[[str], str]) -> str:
    """Apply ``transform`` only outside TeX comments and literal code.

    The helper is shared by the generic resolver and the section-reference
    fallback in :mod:`slides_renderer`, ensuring that both passes preserve
    authored teaching examples and comments exactly.
    """

    pieces: list[str] = []
    cursor = 0
    for start, end in _tex_literal_ranges(tex_content):
        pieces.append(transform(tex_content[cursor:start]))
        pieces.append(tex_content[start:end])
        cursor = end
    pieces.append(transform(tex_content[cursor:]))
    return "".join(pieces)


def tex_prose_content(tex_content: str) -> str:
    """Return only transformable TeX prose, excluding literal regions."""

    pieces: list[str] = []
    cursor = 0
    for start, end in _tex_literal_ranges(tex_content):
        pieces.append(tex_content[cursor:start])
        cursor = end
    pieces.append(tex_content[cursor:])
    return "".join(pieces)


def _read_brace_group(text: str, start: int) -> tuple[str, int] | None:
    """Read one balanced ``{...}`` group beginning at ``text[start]``.

    Returns ``(content, index_past_closing_brace)`` or ``None`` when
    ``start`` is not an opening brace or the group never balances (e.g.
    a truncated aux entry).
    """
    if start >= len(text) or text[start] != "{":
        return None
    depth = 0
    for idx in range(start, len(text)):
        char = text[idx]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1 : idx], idx + 1
    return None


def parse_aux_label_numbers(aux_path: Path) -> dict[str, str]:
    """Parse ``\\newlabel`` entries from a LaTeX ``.aux`` file.

    Returns ``{label -> printed number}`` where the printed number is the
    first brace group of the ``\\newlabel`` value — exactly what
    ``\\ref{label}`` typesets in the combined PDF. Handles the plain
    two-group form ``{{1}{5}}`` and hyperref's five-group form
    ``{{5}{13}{Title...}{theorem.5}{}}`` including nested braces inside
    caption/title fields. Fail-open by design: a missing or unreadable
    file returns ``{}``; malformed or truncated entries, ``@cref``
    bookkeeping labels, and macro-wrapped numbers are skipped.
    """
    try:
        aux_text = aux_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return {}

    label_numbers: dict[str, str] = {}
    for match in _NEWLABEL_RE.finditer(aux_text):
        label = match.group(1)
        if label.endswith("@cref"):
            continue  # cleveref bookkeeping twin of the real entry
        # match.end() sits just past the value group's opening brace. Require
        # the *outer* value group to balance first — a truncated final entry
        # (crashed run) can leave a complete-looking number group inside an
        # unterminated value, and we only trust fully-written entries (cf.
        # ``repair_truncated_aux`` in ``_pdf_latex_validation``).
        outer = _read_brace_group(aux_text, match.end() - 1)
        if outer is None:
            continue  # truncated/malformed entry — skip, never raise
        # The first inner group of the value is the printed number.
        group = _read_brace_group(outer[0], 0)
        if group is None:
            continue
        number = group[0].replace("\\relax", "").strip()
        if not _SAFE_NUMBER_RE.match(number):
            logger.debug("Skipping aux label %r: non-literal number %r", label, group[0])
            continue
        label_numbers[label] = number
    return label_numbers


def resolve_cross_deck_references(
    tex_content: str,
    label_numbers: dict[str, str],
    *,
    resolve_local: bool = False,
) -> tuple[str, int, list[str]]:
    """Substitute cross-deck ``\\ref``/``\\eqref`` with combined-PDF numbers.

    A reference is *cross-deck* when its label is not defined by any
    ``\\label{...}`` in ``tex_content`` itself. Cross-deck refs found in
    ``label_numbers`` become the literal printed number (``\\eqref``
    additionally parenthesized, matching amsmath's rendering). Within-deck
    refs are preserved for Beamer's native numbering by default. The
    canonical accessible refresh sets ``resolve_local`` so local and foreign
    references both use the combined manuscript's exact numbering; this keeps
    Beamer and Reveal derivatives in parity. Any reference selected for
    resolution but missing from the map is left untouched and returned for
    logging.

    Returns ``(updated_tex, replaced_count, sorted_unresolved_labels)``.
    """
    local_labels = set(_LABEL_RE.findall(tex_prose_content(tex_content)))
    replaced = 0
    unresolved: set[str] = set()

    def _resolve_segment(segment: str) -> str:
        def _substitute(match: re.Match[str]) -> str:
            nonlocal replaced
            command, label = match.group("command"), match.group("label")
            if label in local_labels and not resolve_local:
                return match.group(0)  # within-deck: Beamer numbers it natively
            number = label_numbers.get(label)
            if number is None:
                unresolved.add(label)
                return match.group(0)  # fail open: leave the ref untouched
            replaced += 1
            join = "~" if match.group("escaped_join") else ""
            authored_open = match.group("authored_open") or ""
            authored_pair = bool(authored_open and segment[match.end() :].startswith(")"))
            resolved_number = number if command == "ref" or authored_pair else f"({number})"
            return join + authored_open + resolved_number

        return _REF_RE.sub(_substitute, segment)

    updated = transform_tex_prose(tex_content, _resolve_segment)
    return updated, replaced, sorted(unresolved)
