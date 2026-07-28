"""Real pandoc tests for formalism.lua — formalism auto-numbering.

Follows the No Mocks Policy: every test invokes the real pandoc binary against
the real Lua filter, and the LaTeX-compile test runs a real TeX engine.

The filter is resolved through ``formalism_filter_path()`` rather than by
rebuilding the path here, so these tests exercise the same resolver the
renderers use. A negative control accompanies each gate, because an assertion
that cannot fail certifies nothing.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from infrastructure.rendering._pandoc_filters import formalism_filter_path

PANDOC_FORMAT = "markdown+tex_math_dollars+raw_tex+header_attributes"


def _pandoc_path() -> str:
    pandoc = shutil.which("pandoc")
    if pandoc is None:
        pytest.skip("pandoc not available on PATH")
    return pandoc


def _run_pandoc(
    markdown: str,
    *,
    to: str = "markdown",
    with_filter: bool = True,
    extra: list[str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Convert *markdown* with pandoc, optionally applying the formalism filter.

    ``with_filter=False`` is the negative-control switch: the same input and the
    same assertions, minus the filter under test.
    """
    cmd = [_pandoc_path(), "--from", PANDOC_FORMAT, "-t", to]
    if with_filter:
        cmd.append(f"--lua-filter={formalism_filter_path()}")
    cmd.extend(extra or [])
    return subprocess.run(cmd, input=markdown, text=True, capture_output=True, check=True)


# ---------------------------------------------------------------------------
# Fixtures — authoring samples
# ---------------------------------------------------------------------------

TWO_KINDS = """\
::: {.definition #def:aspiration title="Aspiration"}
An aspiration is a six-tuple.
:::

::: {.proposition #prop:monotone title="Monotonicity"}
Dropping oversight never softens a verdict.
:::

::: {.definition #def:registry title="Registry"}
The registry is an ordered sequence.
:::

By [@def:aspiration] and [@prop:monotone], and see [@def:registry].
"""

RESET_DOC = """\
---
formalism_reset_level: 1
---

# Work One

::: {.definition #def:a}
First.
:::

::: {.definition #def:b}
Second.
:::

# Work Two

::: {.definition #def:c}
Restarts here.
:::

Refs: [@def:a] [@def:b] [@def:c].
"""


# ---------------------------------------------------------------------------
# Numbering
# ---------------------------------------------------------------------------


def test_counters_are_independent_per_kind() -> None:
    """Definitions and Propositions each run their own sequence."""
    out = _run_pandoc(TWO_KINDS).stdout

    assert "**Definition 1 (Aspiration).**" in out
    assert "**Definition 2 (Registry).**" in out
    # The Proposition sits between the two Definitions but starts at 1, so the
    # counters are per kind rather than one shared document counter.
    assert "**Proposition 1 (Monotonicity).**" in out


def test_numbering_follows_document_order() -> None:
    """A block inserted earlier in the source takes the earlier number."""
    reordered = TWO_KINDS.replace(
        '::: {.definition #def:aspiration title="Aspiration"}\nAn aspiration is a six-tuple.\n:::\n\n',
        "",
    )
    reordered = '::: {.definition #def:inserted title="Inserted"}\nInserted ahead of everything.\n:::\n\n' + reordered
    out = _run_pandoc(reordered).stdout

    assert "**Definition 1 (Inserted).**" in out
    # The block that used to be Definition 2 slides down to 2 automatically —
    # this is the drift a hand-written literal cannot survive.
    assert "**Definition 2 (Registry).**" in out


def test_title_attribute_is_rendered_in_parentheses() -> None:
    """An optional title attribute becomes a parenthetical name."""
    out = _run_pandoc('::: {.theorem #thm:x title="Pythagoras"}\nBody.\n:::\n').stdout
    assert "**Theorem 1 (Pythagoras).**" in out


def test_block_without_title_omits_the_parenthetical() -> None:
    """A block with no title renders the kind and number alone."""
    out = _run_pandoc("::: {.lemma #lem:x}\nBody.\n:::\n").stdout
    assert "**Lemma 1.**" in out
    assert "(" not in out.split("Body")[0]


def test_unnumbered_class_suppresses_the_counter() -> None:
    """An .unnumbered block gets a label but consumes no number."""
    out = _run_pandoc(
        "::: {.remark .unnumbered}\nNot a claim about importance.\n:::\n\n"
        "::: {.remark #rem:counted}\nCounted.\n:::\n\n"
        "See [@rem:counted].\n"
    ).stdout

    assert "**Remark.** Not a claim" in out
    # The numbered Remark that follows is still 1, so the unnumbered one did
    # not silently advance the counter.
    assert "**Remark 1.** Counted." in out


def test_reset_level_restarts_counters_at_each_level_one_header() -> None:
    """formalism_reset_level: 1 restarts numbering per top-level work."""
    out = _run_pandoc(RESET_DOC).stdout

    assert "**Definition 1.** First." in out
    assert "**Definition 2.** Second." in out
    assert "**Definition 1.** Restarts here." in out


def test_reset_level_is_off_by_default() -> None:
    """Without the metadata key, a level-1 header is just a section."""
    out = _run_pandoc(RESET_DOC.replace("formalism_reset_level: 1", "formalism_reset_level: 0")).stdout

    assert "**Definition 3.** Restarts here." in out


def test_marker_joins_the_first_paragraph_rather_than_standing_alone() -> None:
    """The bold marker leads the body text instead of forming its own block."""
    out = _run_pandoc("::: {.definition #def:x}\nAn aspiration.\n:::\n").stdout
    assert "**Definition 1.** An aspiration." in out


# ---------------------------------------------------------------------------
# Reference resolution
# ---------------------------------------------------------------------------


def test_reference_resolves_to_a_link_carrying_the_resolved_text() -> None:
    """[@label] becomes a hyperlink whose text is the current number."""
    out = _run_pandoc(TWO_KINDS).stdout

    assert "[Definition 1](#def:aspiration)" in out
    assert "[Proposition 1](#prop:monotone)" in out
    assert "[Definition 2](#def:registry)" in out


def test_reference_text_tracks_renumbering() -> None:
    """The reference is resolved from the label, never from a stale literal."""
    with_extra = '::: {.definition #def:new title="New"}\nInserted first.\n:::\n\n' + TWO_KINDS
    out = _run_pandoc(with_extra).stdout

    # def:aspiration moved from 1 to 2 and its reference moved with it.
    assert "[Definition 2](#def:aspiration)" in out


def test_reference_resolution_negative_control() -> None:
    """Without the filter, the reference stays an unresolved citation.

    Proves the assertion above binds to filter behaviour and not to something
    pandoc would have done anyway.
    """
    out = _run_pandoc(TWO_KINDS, with_filter=False).stdout

    assert "[Definition 1](#def:aspiration)" not in out
    assert "@def:aspiration" in out


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------


def test_duplicate_label_is_reported_on_stderr() -> None:
    """Two blocks claiming one label is a warning, not a silent overwrite."""
    result = _run_pandoc("::: {.definition #def:dup}\nFirst.\n:::\n\n::: {.definition #def:dup}\nSecond.\n:::\n")
    assert "duplicate label 'def:dup'" in result.stderr


def test_duplicate_label_negative_control() -> None:
    """Distinct labels produce no duplicate warning."""
    result = _run_pandoc("::: {.definition #def:one}\nFirst.\n:::\n\n::: {.definition #def:two}\nSecond.\n:::\n")
    assert "duplicate label" not in result.stderr


def test_undeclared_reference_is_reported_on_stderr() -> None:
    """A reference to a label nobody declared is named on stderr."""
    result = _run_pandoc("::: {.definition #def:real}\nBody.\n:::\n\nSee [@def:nowhere].\n")
    assert "reference to undeclared formalism 'def:nowhere'" in result.stderr


def test_undeclared_reference_survives_verbatim() -> None:
    """The broken reference stays visible instead of vanishing from the prose.

    Silently dropping it would convert a broken cross-reference into invisible
    prose, which is the failure the filter exists to prevent.
    """
    out = _run_pandoc("::: {.definition #def:real}\nBody.\n:::\n\nSee [@def:nowhere].\n").stdout

    assert "def:nowhere" in out
    assert "See" in out


def test_undeclared_reference_negative_control() -> None:
    """A declared reference triggers no undeclared warning."""
    result = _run_pandoc("::: {.definition #def:real}\nBody.\n:::\n\nSee [@def:real].\n")
    assert "undeclared formalism" not in result.stderr


def test_undeclared_prefix_learned_from_the_document() -> None:
    """A stale ref sharing a declared label's prefix is caught, not passed on.

    "thm" is not a prefix of "theorem", so a purely name-based heuristic would
    miss this. Once the document declares #thm:real, the prefix is known.
    """
    result = _run_pandoc("::: {.theorem #thm:real}\nBody.\n:::\n\nSee [@thm:typo].\n")
    assert "reference to undeclared formalism 'thm:typo'" in result.stderr


# ---------------------------------------------------------------------------
# THE CRITICAL PROPERTY — formalism refs must never reach the citation machinery
# ---------------------------------------------------------------------------


def test_natbib_output_contains_no_citep_for_a_formalism_label() -> None:
    """[@def:x] must never survive to natbib, which would ship "[?]"."""
    out = _run_pandoc(TWO_KINDS, to="latex", extra=["--natbib"]).stdout

    assert "citep" not in out
    assert r"\hyperref[def:aspiration]{Definition 1}" in out


def test_natbib_citep_negative_control() -> None:
    """Without the filter, natbib does emit \\citep for the same labels.

    This is the shipped failure the filter prevents; if this control ever stops
    failing, the test above has stopped proving anything.
    """
    out = _run_pandoc(TWO_KINDS, to="latex", with_filter=False, extra=["--natbib"]).stdout

    assert "citep{def:aspiration}" in out


def test_undeclared_reference_also_avoids_citep() -> None:
    """Even a broken reference is kept out of natbib.

    Verbatim text is visible to the author; \\citep{def:nowhere} would instead
    become an undefined citation and a "[?]" in the PDF.
    """
    out = _run_pandoc(
        "::: {.definition #def:real}\nBody.\n:::\n\nSee [@def:nowhere].\n",
        to="latex",
        extra=["--natbib"],
    ).stdout

    assert "citep" not in out
    assert "def:nowhere" in out


def test_mixed_citation_group_is_partitioned() -> None:
    """[@def:x; @bibkey] resolves the formalism half and keeps the bib half.

    Bailing out of the whole group because one member is a bibliography key
    would put def:x back into \\citep — the exact defect this partition fixes.
    """
    out = _run_pandoc(
        "::: {.definition #def:a}\nBody.\n:::\n\nMixed [@def:a; @smith2020].\n",
        to="latex",
        extra=["--natbib"],
    ).stdout

    assert r"\hyperref[def:a]{Definition 1}" in out
    assert "citep{smith2020}" in out
    assert "citep{def:a" not in out


def test_ordinary_bibliography_citations_are_left_alone() -> None:
    """A plain bib key is not a formalism label and must reach natbib intact."""
    out = _run_pandoc("Plain [@smith2020].\n", to="latex", extra=["--natbib"]).stdout
    assert "citep{smith2020}" in out


def test_citeproc_reports_no_unresolved_citation(tmp_path: Path) -> None:
    """The DOCX/EPUB/HTML path: citeproc never sees a formalism reference."""
    bib = tmp_path / "refs.bib"
    bib.write_text(
        "@article{smith2020, title={T}, author={Smith, J}, year={2020}, journal={J}}\n",
        encoding="utf-8",
    )
    result = _run_pandoc(
        TWO_KINDS,
        to="html",
        extra=["--citeproc", f"--bibliography={bib}"],
    )

    assert "not found" not in result.stderr
    assert 'href="#def:aspiration"' in result.stdout


def test_citeproc_unresolved_citation_negative_control(tmp_path: Path) -> None:
    """Without the filter, citeproc does warn about the same references."""
    bib = tmp_path / "refs.bib"
    bib.write_text(
        "@article{smith2020, title={T}, author={Smith, J}, year={2020}, journal={J}}\n",
        encoding="utf-8",
    )
    result = _run_pandoc(
        TWO_KINDS,
        to="html",
        with_filter=False,
        extra=["--citeproc", f"--bibliography={bib}"],
    )

    assert "citation def:aspiration not found" in result.stderr


# ---------------------------------------------------------------------------
# Interoperability with pandoc-crossref
# ---------------------------------------------------------------------------


def test_runs_alongside_pandoc_crossref_without_disturbing_it() -> None:
    """Formalism numbering and crossref equation numbering coexist."""
    crossref = shutil.which("pandoc-crossref")
    if crossref is None:
        pytest.skip("pandoc-crossref not available on PATH")

    out = _run_pandoc(
        "::: {.definition #def:a}\nBody.\n:::\n\n$$x = 1$$ {#eq:one}\n\nSee [@def:a] and [@eq:one].\n",
        extra=["--filter", crossref],
    ).stdout

    assert "**Definition 1.**" in out
    assert "[Definition 1](#def:a)" in out
    # crossref still owns equation numbering.
    assert "eq:one" in out


# ---------------------------------------------------------------------------
# Real LaTeX compile
# ---------------------------------------------------------------------------


@pytest.mark.requires_latex
@pytest.mark.slow
@pytest.mark.timeout(120)
def test_real_pdf_compile_has_zero_undefined_citations(tmp_path: Path) -> None:
    """Compile a real PDF and assert the LaTeX log carries no undefined citation."""
    engine = shutil.which("pdflatex") or shutil.which("xelatex")
    if engine is None:
        pytest.skip("no LaTeX engine available")

    tex = tmp_path / "doc.tex"
    tex.write_text(
        _run_pandoc(TWO_KINDS, to="latex", extra=["--natbib", "--standalone"]).stdout,
        encoding="utf-8",
    )

    # Two passes, matching the multi-pass behaviour of the real LaTeX pipeline:
    # \hyperref targets land in the .aux on pass one and only resolve on pass
    # two. Asserting on a single pass would report undefined references that the
    # shipped renderer never produces.
    for _ in range(2):
        result = subprocess.run(
            [engine, "-interaction=nonstopmode", "-halt-on-error", tex.name],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=90,
            check=False,
        )
        assert result.returncode == 0, result.stdout[-2000:]
    assert (tmp_path / "doc.pdf").is_file()

    log = (tmp_path / "doc.log").read_text(encoding="utf-8", errors="replace")
    assert "undefined" not in log.lower()

    # The rendered page carries resolved numbers, not natbib's "[?]" or LaTeX's "??".
    pdftotext = shutil.which("pdftotext")
    if pdftotext is not None:
        text = subprocess.run(
            [pdftotext, "doc.pdf", "-"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        ).stdout
        assert "By Definition 1 and Proposition 1, and see Definition 2." in text
        assert "[?]" not in text
        assert "??" not in text


# --------------------------------------------------------------------------
# Regressions found by adversarial verification of the first integration.
# Each of these shipped green once; the assertions below are what caught them.
# --------------------------------------------------------------------------


def test_theorem_box_divs_are_left_to_the_web_prepass() -> None:
    """``_html_theorem_blocks`` already numbered these; numbering again doubles them.

    ``WebRenderer._html_theorem_blocks`` rewrites raw-LaTeX ``\\begin{definition}``
    into ``::: {.theorem-box .definition}`` and numbers it on a shared counter
    before pandoc runs. That is the same Div shape this filter consumes, so the
    combined HTML edition of the tracked ``template_formal`` exemplar rendered
    ``**Definition 1.** **Definition 1**``.
    """
    result = _run_pandoc("::: {.theorem-box .definition}\n**Definition 1** Numbered by the web pre-pass.\n:::\n")
    assert result.returncode == 0, result.stderr
    assert result.stdout.count("Definition 1") == 1, result.stdout
    assert "Definition 1 (" not in result.stdout


def test_theorem_box_guard_negative_control() -> None:
    """Without the guard class the same Div *is* numbered, so the check can fail."""
    result = _run_pandoc("::: {.definition}\n**Definition 1** Authored as a fenced Div.\n:::\n")
    assert result.returncode == 0, result.stderr
    assert result.stdout.count("Definition 1") == 2, result.stdout


def test_bibliography_keys_that_resemble_a_kind_prefix_are_not_stolen() -> None:
    """An ``author:year`` citekey must stay a citation.

    An earlier rule claimed any prefix that spelled the start of a kind name,
    which matched 64 prefixes including the single letters a, c, d, e, l, p, r
    and t. ``[@ex:pandoc2020]`` stopped being a citation and shipped as literal
    markup, with pandoc still exiting 0.
    """
    body = "Refs: [@ex:pandoc2020] [@co:jones1999] [@d:smith2001] [@rem:brown2011].\n"
    result = _run_pandoc(body, to="latex", extra=["--natbib"])
    assert result.returncode == 0, result.stderr
    for key in ("ex:pandoc2020", "co:jones1999", "d:smith2001", "rem:brown2011"):
        assert f"citep{{{key}}}" in result.stdout, (key, result.stdout)
    assert "[@" not in result.stdout, result.stdout


def test_a_declared_prefix_still_claims_its_own_undeclared_labels() -> None:
    """The document-driven half of the rule survives the narrowing above."""
    body = '::: {.definition #def:real title="Real"}\nDeclared.\n:::\n\nA typo: [@def:typo].\n'
    result = _run_pandoc(body, to="latex", extra=["--natbib"])
    assert result.returncode == 0, result.stderr
    assert "citep{def:typo}" not in result.stdout, result.stdout
    assert "def:typo" in result.stdout, result.stdout
    assert "undeclared formalism 'def:typo'" in result.stderr


def test_citation_prefix_and_suffix_are_carried_across() -> None:
    """``[see @def:x, p. 3]`` must not silently lose "see" and ", p. 3"."""
    body = '::: {.definition #def:a title="A"}\nBody.\n:::\n\nRead [see @def:a, p. 3] closely.\n'
    result = _run_pandoc(body)
    assert result.returncode == 0, result.stderr
    # Pandoc renders "p. 3" with a non-breaking space, so compare on a form
    # that does not depend on which space character the writer chose.
    normalised = result.stdout.replace(" ", " ")
    assert "see" in normalised, result.stdout
    assert "p. 3" in normalised, result.stdout
    assert "Definition 1" in normalised, result.stdout


def test_citation_affix_negative_control() -> None:
    """The affix assertion fails when there is no affix to carry."""
    body = '::: {.definition #def:a title="A"}\nBody.\n:::\n\nRead [@def:a] closely.\n'
    result = _run_pandoc(body)
    assert result.returncode == 0, result.stderr
    assert "p. 3" not in result.stdout


def test_undeclared_reference_stays_visible_inside_a_mixed_group() -> None:
    """The solo path is not the only path a broken reference can take.

    An undeclared label alongside a declared one, or alongside a bibliography
    key, takes the partition branch rather than the verbatim branch. Replacing
    the fallback text with an empty string left the whole suite green, so a
    broken cross-reference could vanish into invisible prose — the exact
    failure the filter's own header says it exists to prevent.
    """
    declared_and_broken = _run_pandoc('::: {.definition #def:a title="A"}\nBody.\n:::\n\nSee [@def:a; @def:nowhere].\n')
    assert declared_and_broken.returncode == 0, declared_and_broken.stderr
    assert "def:nowhere" in declared_and_broken.stdout, declared_and_broken.stdout
    assert "Definition 1" in declared_and_broken.stdout

    broken_and_bibliography = _run_pandoc(
        '::: {.definition #def:a title="A"}\nBody.\n:::\n\nSee [@def:nowhere; @knuth1984].\n'
    )
    assert broken_and_bibliography.returncode == 0, broken_and_bibliography.stderr
    assert "def:nowhere" in broken_and_bibliography.stdout, broken_and_bibliography.stdout
    assert "knuth1984" in broken_and_bibliography.stdout
