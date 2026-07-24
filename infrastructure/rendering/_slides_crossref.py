"""Cross-deck LaTeX reference resolution for per-section slide decks.

Each section deck is a standalone Pandoc/Beamer build, so raw-LaTeX
``\\ref{...}`` / ``\\eqref{...}`` commands whose ``\\label`` lives in a
*different* section's deck compile to "??" — xelatex never sees the
defining label. The combined manuscript PDF *does* resolve every label,
and its retained ``.aux`` file (``output/pdf/_combined_manuscript.aux``)
carries the ground-truth ``\\newlabel{label}{{number}{page}...}`` map.

This module provides a fail-open pre-pass for
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
  the caller for the render log. The slide build never fails because of
  this pass.

The numbers substituted here match the combined PDF exactly because they
come *from* the combined PDF's own auxiliary file. Note the aux is a
retained artefact of the most recent combined build: on the very first
render of a project (no aux yet) every cross-deck ref stays as "??"
until the next render pass, consistent with fail-open behavior.
"""

from __future__ import annotations

import re
from pathlib import Path

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

#: Basename of the combined manuscript's LaTeX auxiliary file, relative to
#: the configured ``pdf_dir`` (see ``_pdf_latex_pipeline`` /
#: ``pdf_renderer`` which compile ``_combined_manuscript.tex`` in place).
COMBINED_AUX_BASENAME = "_combined_manuscript.aux"

# \newlabel{<label>}{  — the label itself never contains braces.
_NEWLABEL_RE = re.compile(r"\\newlabel\{([^{}]+)\}\{")

# \ref{L} / \eqref{L}. The leading backslash keeps \pageref / \autoref /
# \nameref / \cref tails from matching ("...ref" without its own backslash).
_REF_RE = re.compile(r"\\(eqref|ref)\{([^{}]+)\}")

# \label{L} occurrences inside the deck's own generated .tex source.
_LABEL_RE = re.compile(r"\\label\{([^{}]+)\}")

#: Printed numbers we trust for literal substitution: plain section /
#: theorem / equation counters like ``5``, ``2.3.1``, ``A.2``. Anything
#: containing macros (e.g. hyperref's ``\M@TitleReference`` wrapping) is
#: skipped so we never inject unexpanded TeX into a slide deck.
_SAFE_NUMBER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.\-]*$")


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
) -> tuple[str, int, list[str]]:
    """Substitute cross-deck ``\\ref``/``\\eqref`` with combined-PDF numbers.

    A reference is *cross-deck* when its label is not defined by any
    ``\\label{...}`` in ``tex_content`` itself. Cross-deck refs found in
    ``label_numbers`` become the literal printed number (``\\eqref``
    additionally parenthesized, matching amsmath's rendering); within-deck
    refs are preserved for Beamer's native numbering; cross-deck refs
    missing from the map are left untouched and returned for logging.

    Returns ``(updated_tex, replaced_count, sorted_unresolved_labels)``.
    """
    local_labels = set(_LABEL_RE.findall(tex_content))
    replaced = 0
    unresolved: set[str] = set()

    def _substitute(match: re.Match[str]) -> str:
        nonlocal replaced
        command, label = match.group(1), match.group(2)
        if label in local_labels:
            return match.group(0)  # within-deck: Beamer numbers it natively
        number = label_numbers.get(label)
        if number is None:
            unresolved.add(label)
            return match.group(0)  # fail open: leave the ref untouched
        replaced += 1
        return f"({number})" if command == "eqref" else number

    updated = _REF_RE.sub(_substitute, tex_content)
    return updated, replaced, sorted(unresolved)
