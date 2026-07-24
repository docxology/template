"""Tests for cross-deck reference resolution in slide decks.

Per-section slide decks are standalone Beamer builds, so raw-LaTeX
``\\ref``/``\\eqref`` commands whose ``\\label`` lives in another
section's deck used to render as "??". ``_slides_crossref`` resolves
them from the combined manuscript build's retained ``.aux`` file so
slides print the *same* numbers as the combined PDF.

Covers the two pure passes (aux parsing, substitution) plus the
``SlidesRenderer._resolve_cross_deck_refs`` hook. No Pandoc/LaTeX
toolchain needed — everything here is string/file transformation on
real aux-format lines (samples mirror an actual
``_combined_manuscript.aux`` from a working project).
"""

from __future__ import annotations

from infrastructure.rendering._slides_crossref import (
    COMBINED_AUX_BASENAME,
    parse_aux_label_numbers,
    resolve_cross_deck_references,
)
from infrastructure.rendering.slides_renderer import SlidesRenderer

# Real hyperref five-group aux lines, including a caption field with heavy
# nested braces and inline macros (verbatim shape from a live project aux).
_REAL_AUX = "\n".join(
    [
        r"\relax",
        r"\providecommand\hyper@newdestlabel[2]{}",
        r"\newlabel{sec:abstract}{{1}{4}{Abstract}{section.1}{}}",
        r"\newlabel{fig:system-overview}{{2}{7}{System overview. \textbf {Recovery ribbon:} the"
        r" \protect \breaktt {robust\_aggregate} heuristic (see {nested {deeply}} braces)}{figure.caption.3}{}}",
        r"\newlabel{sec:intro-visual-map}{{2.3.1}{7}{How to read the visual architecture}{subsubsection.2.3.1}{}}",
        r"\newlabel{def:generalized-bayes}{{1}{11}{Generalized-(Gibbs)-Bayes posterior}{theorem.1}{}}",
        r"\newlabel{thm:belief-sharing-recovery}{{5}{13}{Standard belief sharing is the FedGVI"
        r" KL/NLL/\(\beta =0\) corner}{theorem.5}{}}",
        r"\newlabel{eq:gen-bayes}{{1}{11}}",  # plain two-group (no hyperref) form
        r"\newlabel{sec:appendix-proofs}{{A.2}{41}{Proofs}{appendix.A.2}{}}",
    ]
)


class TestParseAuxLabelNumbers:
    """``parse_aux_label_numbers`` — aux file to {label -> printed number}."""

    def test_parses_real_aux_lines(self, tmp_path):
        aux = tmp_path / COMBINED_AUX_BASENAME
        aux.write_text(_REAL_AUX, encoding="utf-8")

        labels = parse_aux_label_numbers(aux)

        assert labels["sec:abstract"] == "1"
        assert labels["def:generalized-bayes"] == "1"
        assert labels["thm:belief-sharing-recovery"] == "5"
        assert labels["eq:gen-bayes"] == "1"

    def test_multi_brace_caption_and_dotted_numbers(self, tmp_path):
        """Nested braces in later groups must not corrupt the number group."""
        aux = tmp_path / COMBINED_AUX_BASENAME
        aux.write_text(_REAL_AUX, encoding="utf-8")

        labels = parse_aux_label_numbers(aux)

        assert labels["fig:system-overview"] == "2"
        assert labels["sec:intro-visual-map"] == "2.3.1"
        assert labels["sec:appendix-proofs"] == "A.2"

    def test_skips_cref_bookkeeping_and_macro_numbers(self, tmp_path):
        aux = tmp_path / COMBINED_AUX_BASENAME
        aux.write_text(
            "\n".join(
                [
                    r"\newlabel{thm:main}{{3}{9}{Main}{theorem.3}{}}",
                    r"\newlabel{thm:main@cref}{{[theorem][3][]3}{[1][9][]9}}",
                    r"\newlabel{sec:odd}{{\M@TitleReference {4}{Odd}}{10}{Odd}{section.4}{}}",
                    r"\newlabel{sec:relaxed}{{\relax 3.2}{10}{Relaxed}{subsection.3.2}{}}",
                ]
            ),
            encoding="utf-8",
        )

        labels = parse_aux_label_numbers(aux)

        assert labels["thm:main"] == "3"
        assert "thm:main@cref" not in labels
        assert "sec:odd" not in labels  # macro-wrapped number: never inject TeX
        assert labels["sec:relaxed"] == "3.2"  # \relax wrapper stripped

    def test_truncated_entry_skipped_not_fatal(self, tmp_path):
        """A truncated final aux entry (crashed run) parses fail-open."""
        aux = tmp_path / COMBINED_AUX_BASENAME
        aux.write_text(
            "\\newlabel{sec:ok}{{1}{4}{Fine}{section.1}{}}\n\\newlabel{sec:cut}{{2}{5",
            encoding="utf-8",
        )

        labels = parse_aux_label_numbers(aux)

        assert labels == {"sec:ok": "1"}

    def test_missing_aux_returns_empty(self, tmp_path):
        assert parse_aux_label_numbers(tmp_path / "nope.aux") == {}


class TestResolveCrossDeckReferences:
    """``resolve_cross_deck_references`` — the substitution pass."""

    LABEL_MAP = {
        "def:generalized-bayes": "1",
        "thm:belief-sharing-recovery": "5",
        "eq:gen-bayes": "1",
        "sec:intro-visual-map": "2.3.1",
    }

    def test_cross_deck_ref_replaced_with_combined_number(self):
        tex = r"Definitions \ref{def:generalized-bayes} and Theorem \ref{thm:belief-sharing-recovery} apply."

        updated, replaced, unresolved = resolve_cross_deck_references(tex, self.LABEL_MAP)

        assert updated == "Definitions 1 and Theorem 5 apply."
        assert replaced == 2
        assert unresolved == []

    def test_eqref_gets_parentheses(self):
        tex = r"as shown in \eqref{eq:gen-bayes}."

        updated, replaced, _ = resolve_cross_deck_references(tex, self.LABEL_MAP)

        assert updated == "as shown in (1)."
        assert replaced == 1

    def test_within_deck_ref_preserved_for_native_numbering(self):
        tex = "\n".join(
            [
                r"\begin{theorem}\label{thm:belief-sharing-recovery}Body.\end{theorem}",
                r"See Theorem \ref{thm:belief-sharing-recovery} and Definition \ref{def:generalized-bayes}.",
            ]
        )

        updated, replaced, unresolved = resolve_cross_deck_references(tex, self.LABEL_MAP)

        # The locally-defined label keeps its \ref; only the foreign one resolves.
        assert r"\ref{thm:belief-sharing-recovery}" in updated
        assert r"Definition 1." in updated
        assert replaced == 1
        assert unresolved == []

    def test_unknown_label_left_untouched_and_reported(self):
        tex = r"Lemma \ref{lem:not-in-aux} and Theorem \ref{thm:belief-sharing-recovery}."

        updated, replaced, unresolved = resolve_cross_deck_references(tex, self.LABEL_MAP)

        assert r"\ref{lem:not-in-aux}" in updated
        assert "Theorem 5." in updated
        assert replaced == 1
        assert unresolved == ["lem:not-in-aux"]

    def test_other_ref_commands_untouched(self):
        tex = r"\pageref{sec:intro-visual-map} \autoref{sec:intro-visual-map} \cref{sec:intro-visual-map}"

        updated, replaced, _ = resolve_cross_deck_references(tex, self.LABEL_MAP)

        assert updated == tex
        assert replaced == 0


class TestSlidesRendererHook:
    """``SlidesRenderer._resolve_cross_deck_refs`` — the renderer wiring."""

    def test_resolves_from_retained_combined_aux(self, test_config, tmp_path):
        aux_dir = tmp_path / "output" / "pdf"
        aux_dir.mkdir(parents=True, exist_ok=True)
        (aux_dir / COMBINED_AUX_BASENAME).write_text(_REAL_AUX, encoding="utf-8")

        renderer = SlidesRenderer(test_config)
        tex = r"Theorem \ref{thm:belief-sharing-recovery} and \eqref{eq:gen-bayes}, but \ref{lem:missing}."

        updated = renderer._resolve_cross_deck_refs(tex)

        assert updated == r"Theorem 5 and (1), but \ref{lem:missing}."

    def test_missing_aux_is_a_noop(self, test_config):
        renderer = SlidesRenderer(test_config)
        tex = r"Theorem \ref{thm:belief-sharing-recovery} stands."

        assert renderer._resolve_cross_deck_refs(tex) == tex
