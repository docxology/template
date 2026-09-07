"""Tests for infrastructure/rendering/web_renderer.py split by area.

Tests web/HTML rendering functionality using real implementations.
Follows No Mocks Policy - all tests use real data and real execution.
"""

from infrastructure.rendering.web_renderer import WebRenderer

from ._web_renderer_test_helpers import _make_renderer


class TestTheoremBlocks:
    """Web-only rewrite of raw-LaTeX theorem environments into numbered Divs."""

    def test_theorem_block_becomes_numbered_div_with_name_and_body(self):
        src = (
            "\\begin{theorem}[Recovery corner]\n"
            "The robust aggregator at zero robustness equals the log-linear pool.\n"
            "\\end{theorem}"
        )
        out = WebRenderer._html_theorem_blocks(src)
        assert "::: {.theorem-box .theorem}" in out
        assert "**Theorem 1** (Recovery corner)." in out
        assert "equals the log-linear pool." in out  # body preserved
        assert "\\begin{theorem}" not in out  # raw LaTeX gone

    def test_theorem_block_with_same_line_label_is_rewritten_with_anchor(self):
        # The standard amsthm idiom puts \label on the \begin line:
        # \begin{proposition}[Name]\label{prop:x} — the rewriter must still fire
        # (a 2026-07-17 regression dropped every labeled environment from the
        # web surface) and should carry the label through as a Div anchor.
        src = (
            "\\begin{proposition}[EFE identity]\\label{prop:efe-decomposition}\n"
            "The cost and value decompositions agree.\n"
            "\\end{proposition}"
        )
        out = WebRenderer._html_theorem_blocks(src)
        assert "::: {.theorem-box .proposition #prop:efe-decomposition}" in out
        assert "**Proposition 1** (EFE identity)." in out
        assert "decompositions agree." in out
        assert "\\label{" not in out  # label consumed, not leaked into prose
        assert "\\begin{proposition}" not in out

    def test_shared_counter_across_environments(self):
        src = (
            "\\begin{definition}[Free energy]\nF is defined here.\n\\end{definition}\n\n"
            "\\begin{lemma}\nA lemma body.\n\\end{lemma}\n\n"
            "\\begin{theorem}[Main]\nThe theorem body.\n\\end{theorem}"
        )
        out = WebRenderer._html_theorem_blocks(src)
        # one running counter, mirroring \newtheorem[theorem] shared numbering
        assert "**Definition 1** (Free energy)." in out
        assert "**Lemma 2**." in out
        assert "**Theorem 3** (Main)." in out
        assert ".definition" in out and ".lemma" in out and ".theorem" in out

    def test_unnamed_block_has_no_parenthetical(self):
        out = WebRenderer._html_theorem_blocks("\\begin{proposition}\nNo name here.\n\\end{proposition}")
        assert "**Proposition 1**." in out
        assert "(" not in out.split("No name")[0].split("Proposition 1")[1]

    def test_non_theorem_content_is_untouched(self):
        src = "Just prose with $x = 1$ and a [@fig:a] reference.\n"
        assert WebRenderer._html_theorem_blocks(src) == src

    def test_texttt_in_body_becomes_code_span_with_unescaped_underscores(self):
        # Pandoc's HTML writer drops \texttt{...} as raw inline LaTeX, which
        # made module names vanish from the web theorem boxes ("the categorical
        # generative model of , the cost"). The body cleaner must surface the
        # filename as a markdown code span instead.
        src = (
            "\\begin{definition}[EFE module]\n"
            "The categorical generative model of \\texttt{expected\\_free\\_energy.py}, the cost.\n"
            "\\end{definition}"
        )
        out = WebRenderer._html_theorem_blocks(src)
        assert "`expected_free_energy.py`" in out
        assert "\\texttt" not in out

    def test_inline_and_display_math_delimiters_become_dollar_math(self):
        # \(...\) degraded to "(G())" on the web because pandoc's markdown
        # reader doesn't enable tex_math_single_backslash; the body cleaner
        # converts to $...$ / $$...$$ so HTML+MathJax renders them.
        src = (
            "\\begin{theorem}[EFE]\n"
            "The expected free energy \\(G(\\pi)\\) satisfies\n"
            "\\[G(\\pi) = \\mathbb{E}[F]\\]\n"
            "for every policy.\n"
            "\\end{theorem}"
        )
        out = WebRenderer._html_theorem_blocks(src)
        assert "$G(\\pi)$" in out
        assert "$$G(\\pi) = \\mathbb{E}[F]$$" in out
        assert "\\(" not in out and "\\[" not in out

    def test_theorem_name_preserves_math_and_texttt(self):
        """Optional theorem names use the same safe path as theorem bodies."""
        src = "\\begin{theorem}[KL/NLL/\\(\\beta=0\\), \\texttt{log_linear_pool}]\nThe identity holds.\n\\end{theorem}"
        out = WebRenderer._html_theorem_blocks(src)
        assert "KL/NLL/$\\beta=0$" in out
        assert "`log_linear_pool`" in out
        assert "\\(" not in out
        assert "\\texttt" not in out

    def test_texttt_and_math_outside_theorem_bodies_are_untouched(self):
        # The cleaner is theorem-body-scoped: surrounding prose keeps its raw
        # LaTeX for the existing global passes to handle.
        src = (
            "Prose with \\texttt{keep\\_raw.py} and \\(x\\) here.\n\n\\begin{lemma}\nBody with \\(y\\).\n\\end{lemma}\n"
        )
        out = WebRenderer._html_theorem_blocks(src)
        assert "\\texttt{keep\\_raw.py}" in out
        assert "Prose with \\texttt" in out and "\\(x\\)" in out
        assert "$y$" in out

    def test_theorems_survive_full_html_safe_pass(self, tmp_path):
        renderer = _make_renderer(tmp_path)
        src = (
            "Intro.\n\n\\begin{theorem}[Descent]\n"
            "Block-coordinate descent never increases $F$.\n"
            "\\end{theorem}\n\nOutro."
        )
        result = renderer._html_safe_markdown(src)
        assert "theorem-box" in result
        assert "Block-coordinate descent never increases" in result  # not dropped
        assert "\\begin{theorem}" not in result
