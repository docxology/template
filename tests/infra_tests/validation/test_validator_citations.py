#!/usr/bin/env python3
"""Citation-key extraction must follow Pandoc's internal-punctuation rule.

Pandoc's manual is explicit that a citation key "may contain alphanumerics and
internal punctuation characters": punctuation is part of the key only when
something follows it. A sentence-final in-text citation therefore ends at the
last word character, and the period belongs to the sentence.

The extraction pattern originally ran its punctuation class to the end of the
match, so ``... given textbook treatment by @parr2022active. That is ...``
yielded the key ``parr2022active.``. No such key can ever exist in a ``.bib``
file, so every sentence-final in-text citation became a pre-render ERROR blocker
and the combined PDF was abandoned before Pandoc ran — while the individual
per-section PDFs, which do not go through this validator, rendered fine. That
asymmetry is what made the defect easy to misread as a manuscript error.

These tests are written against real files on disk (no mocks, per the repo's
no-mocks policy) plus direct pattern assertions for the punctuation rule.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._pandoc_filters import (
    CROSS_REFERENCE_PREFIXES,
    FORMALISM_KINDS,
    FormalismKind,
)
from infrastructure.validation.content.prerender import prevalidate_for_render
from infrastructure.validation.content.validator_citations import (
    CITE_KEY_PATTERN,
    validate_citations,
)

BIB = """\
@book{parr2022active,
  author = {Parr, Thomas and Pezzulo, Giovanni and Friston, Karl},
  title  = {Active Inference},
  year   = {2022}
}

@article{viterbi1967error,
  author  = {Viterbi, Andrew},
  title   = {Error bounds for convolutional codes},
  journal = {IEEE Transactions on Information Theory},
  year    = {1967}
}

@article{smith-jones2020,
  author  = {Smith-Jones, Ada},
  title   = {Hyphenated keys are legal},
  journal = {Journal of Keys},
  year    = {2020}
}
"""


def _write_case(tmp_path: Path, body: str) -> tuple[list[str], Path, Path]:
    """Write a one-section manuscript plus a bib and return validator arguments."""
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    md = manuscript / "10_related_work.md"
    md.write_text(body, encoding="utf-8")
    bib = manuscript / "references.bib"
    bib.write_text(BIB, encoding="utf-8")
    return [str(md)], tmp_path, bib


# ── the punctuation rule itself ───────────────────────────────────────────────


def test_trailing_period_is_not_part_of_the_key() -> None:
    """The defect that blocked the combined PDF."""
    assert CITE_KEY_PATTERN.findall("treatment by @parr2022active. That is") == ["parr2022active"]


def test_trailing_period_at_end_of_input() -> None:
    """No following character to lean on — the period must still be excluded."""
    assert CITE_KEY_PATTERN.findall("of @coecke2010mathematical.") == ["coecke2010mathematical"]


def test_internal_punctuation_is_kept() -> None:
    """The narrowing must not amputate legal internal punctuation.

    Without this, excluding trailing punctuation could have been implemented by
    dropping the punctuation class altogether, which would break every
    hyphenated key and every ``@sec:``/``@fig:`` cross-reference.
    """
    assert CITE_KEY_PATTERN.findall("as @smith-jones2020 shows") == ["smith-jones2020"]
    assert CITE_KEY_PATTERN.findall("see @fig:g2p_accuracy and") == ["fig:g2p_accuracy"]
    assert CITE_KEY_PATTERN.findall("in @a.b.c2020 we") == ["a.b.c2020"]


def test_bracketed_and_multi_key_citations_still_parse() -> None:
    assert CITE_KEY_PATTERN.findall("see [@a2020x; @b2021y].") == ["a2020x", "b2021y"]


def test_single_letter_key_is_still_matched() -> None:
    """The optional tail group must not require a second character."""
    assert CITE_KEY_PATTERN.findall("@a and @b") == ["a", "b"]


def test_email_addresses_are_not_citations() -> None:
    """NEGATIVE CONTROL — the lookbehind must keep doing its job."""
    assert CITE_KEY_PATTERN.findall("mail me at ada@example.com") == []


# ── end-to-end through the validator ─────────────────────────────────────────


def test_sentence_final_in_text_citation_is_accepted(tmp_path: Path) -> None:
    """The regression: three real sentence-final citations, all in the bib."""
    md_paths, root, bib = _write_case(
        tmp_path,
        "# Related work\n\n"
        "Given textbook treatment by @parr2022active. That is the frame here.\n\n"
        "The classical algorithm is @viterbi1967error. The oracle implements it.\n\n"
        "Hyphenated keys work too, as in @smith-jones2020.\n",
    )
    problems = validate_citations(md_paths, root, bib)
    assert problems == [], f"keys present in references.bib were reported undefined: {[p.message for p in problems]}"


def test_a_genuinely_missing_key_is_still_reported(tmp_path: Path) -> None:
    """POSITIVE CONTROL — without this the fix could have disabled the check.

    A validator that accepts everything would pass the test above just as well,
    so the suite must prove a real undefined key is still caught, including one
    that sits at the end of a sentence.
    """
    md_paths, root, bib = _write_case(
        tmp_path,
        "# Related work\n\nAs argued by @nosuchkey2099. And also @alsomissing1999.\n",
    )
    problems = validate_citations(md_paths, root, bib)
    reported = sorted(p.message for p in problems)
    assert len(reported) == 2, reported
    assert "'@nosuchkey2099'" in reported[1], reported
    assert "'@alsomissing1999'" in reported[0], reported
    # The period must not have been folded into the reported key either, or the
    # fix_suggestion would tell an author to add an unusable bib entry.
    assert all("." not in m.split("'")[1] for m in reported), reported


# ── formalism cross-references are not bibliography keys ─────────────────────
#
# formalism.lua numbers every kind in the shared registry and consumes
# ``[@<prefix>:label]`` before natbib or citeproc sees it. The validator used to
# accept only ``def:``, ``prop:`` and ``thm:`` of those prefixes, so a manuscript
# that cited ``[@rem:x]`` was blocked here with "Undefined citation key" and the
# combined PDF never reached Pandoc (hit on 2026-11-24 rendering a remark-heavy
# paper, worked around by relabelling remarks as propositions).


def _kind_id(kind: FormalismKind) -> str:
    return kind.css_class


@pytest.mark.parametrize("kind", FORMALISM_KINDS, ids=_kind_id)
def test_every_formalism_reference_passes_the_prerender_gate(tmp_path: Path, kind: FormalismKind) -> None:
    """The regression, through the gate that raised: one block of every kind, cited."""
    label = f"{kind.label_prefix}:central"
    md_paths, _root, _bib = _write_case(
        tmp_path,
        "# Results\n\n"
        f"::: {{.{kind.css_class} #{label}}}\nThe central statement.\n:::\n\n"
        f"By [@{label}] and the frame of @parr2022active, the result follows.\n",
    )
    # bib_file=None mirrors the combined-PDF renderer, which lets the gate find
    # references.bib beside the sections. The bib does not contain the label.
    prevalidate_for_render(md_paths, bib_file=None)


@pytest.mark.parametrize("prefix", CROSS_REFERENCE_PREFIXES)
def test_validator_accepts_every_registered_cross_reference_prefix(tmp_path: Path, prefix: str) -> None:
    """The validator reads the shared registry rather than a list of its own."""
    md_paths, root, bib = _write_case(tmp_path, f"# Results\n\nSee @{prefix}:anything and [@{prefix}:other].\n")
    problems = validate_citations(md_paths, root, bib)
    assert problems == [], [p.message for p in problems]


def test_a_plain_missing_key_still_fails_beside_formalism_references(tmp_path: Path) -> None:
    """NEGATIVE CONTROL — accepting ``rem:`` must not accept every key in the file.

    A validator that skipped the whole file once it saw a formalism reference,
    or that accepted everything, would pass the two tests above. A genuine
    undefined bibliography key in the same section must still block the render.
    """
    md_paths, root, bib = _write_case(
        tmp_path,
        "# Results\n\n"
        "::: {.remark #rem:central}\nA remark.\n:::\n\n"
        "By [@rem:central] and as argued by @nosuchkey2099, the result follows.\n",
    )
    problems = validate_citations(md_paths, root, bib)
    assert [p.message for p in problems] == ["Undefined citation key '@nosuchkey2099' (not in references.bib)"]

    with pytest.raises(RenderingError) as raised:
        prevalidate_for_render(md_paths, bib_file=None)
    assert "@nosuchkey2099" in str(raised.value)
    assert "rem:central" not in str(raised.value)


@pytest.mark.parametrize("prefix", CROSS_REFERENCE_PREFIXES)
def test_the_prefix_colon_is_load_bearing(tmp_path: Path, prefix: str) -> None:
    """NEGATIVE CONTROL — a key that merely starts with a prefix's letters is a citation.

    ``@remington1990``, ``@axelrod1984`` and ``@exner2000`` are ordinary
    author-year keys. Matching on the bare prefix instead of ``prefix:`` would
    wave every one of them through as a cross-reference.
    """
    key = f"{prefix}author1999"
    md_paths, root, bib = _write_case(tmp_path, f"# Related work\n\nAs shown by @{key}, it holds.\n")
    problems = validate_citations(md_paths, root, bib)
    assert [p.message for p in problems] == [f"Undefined citation key '@{key}' (not in references.bib)"]
