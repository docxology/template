"""Slides math-header injection tests.

The Beamer renderer writes ``_slides_math_header.tex`` when ``preamble.md``
loads unicode-math, and passes it to Pandoc via ``-H``. When unicode-math is
absent, the header still carries natbib/cleveref fallbacks so slides
compiled for the combined PDF survive natbib commands.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from pypdf import PdfWriter

from infrastructure.rendering import slides_renderer
from infrastructure.rendering._slides_accessibility import AccessibleSlidePolicy
from infrastructure.rendering._slides_math_header import write_slides_math_header
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.slides_renderer import SlidesRenderer


class TestSlidesMathHeaderInjection:
    """The Beamer renderer writes _slides_math_header.tex when preamble.md
    loads unicode-math, and passes it to Pandoc via -H. When unicode-math
    is absent, no header is written and no -H flag is added.
    """

    def _make_renderer(self, tmp_path):
        config = RenderingConfig(output_dir=tmp_path, slides_dir=tmp_path / "slides")
        (tmp_path / "slides").mkdir(exist_ok=True)
        return SlidesRenderer(config)

    def test_helper_writes_header_when_unicode_math_loaded(self, tmp_path):
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "preamble.md").write_text(
            "```latex\n\\usepackage{unicode-math}\n```\n",
            encoding="utf-8",
        )
        self._make_renderer(tmp_path)
        output_dir = tmp_path / "slides"
        header = write_slides_math_header(manuscript, output_dir)
        assert header is not None
        assert header.name == "_slides_math_header.tex"
        content = header.read_text(encoding="utf-8")
        assert "\\usepackage{unicode-math}" in content
        assert "\\setmathfont{latinmodern-math.otf}" in content

    def test_helper_returns_header_with_citation_fallbacks_when_no_preamble(self, tmp_path):
        """Even when ``preamble.md`` is missing, the helper writes a
        header that defines ``\\providecommand{\\citep}{...}`` fallbacks
        so slides survive natbib commands emitted for the combined PDF.
        """
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        self._make_renderer(tmp_path)
        header = write_slides_math_header(manuscript, tmp_path / "slides")
        assert header is not None
        assert header.name == "_slides_math_header.tex"
        content = header.read_text(encoding="utf-8")
        assert "\\providecommand{\\citep}" in content
        assert "\\providecommand{\\citet}" in content
        assert "\\providecommand{\\cref}" in content
        assert "\\providecommand{\\Cref}" in content
        # No math snippet expected (no preamble).
        assert "unicode-math" not in content

    def test_header_includes_manuscript_macros_with_unsafe_packages_filtered(self, tmp_path):
        r"""Manuscript macros land in the slide header rewritten as
        \providecommand; unsafe layout packages (geometry) are dropped while
        Beamer-safe ones (amsmath) survive."""
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "preamble.md").write_text(
            "```latex\n\\usepackage{geometry}\n\\usepackage{amsmath}\n\\newcommand{\\calD}{\\mathcal{D}}\n```\n",
            encoding="utf-8",
        )
        self._make_renderer(tmp_path)
        header = write_slides_math_header(manuscript, tmp_path / "slides")
        assert header is not None
        content = header.read_text(encoding="utf-8")
        # Macro rewritten to providecommand and present.
        assert "\\providecommand{\\calD}" in content
        assert "\\newcommand{\\calD}" not in content
        # Safe package kept, layout machinery dropped.
        assert "\\usepackage{amsmath}" in content
        assert "geometry" not in content

    def test_helper_returns_header_with_citation_fallbacks_when_no_unicode_math(self, tmp_path):
        """When ``preamble.md`` exists but doesn't load unicode-math,
        the helper still writes a header for the natbib fallbacks.
        """
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "preamble.md").write_text("```latex\n\\usepackage{geometry}\n```\n", encoding="utf-8")
        self._make_renderer(tmp_path)
        header = write_slides_math_header(manuscript, tmp_path / "slides")
        assert header is not None
        content = header.read_text(encoding="utf-8")
        assert "\\providecommand{\\citep}" in content
        assert "unicode-math" not in content

    def test_helper_defines_proposition_and_hypothesis_environments(self, tmp_path):
        """Beamer's document class already defines \\theorem/\\lemma/\\corollary/
        \\definition natively; redeclaring them via \\newtheorem fails with
        "Command ... already defined" (regression: template_formal's
        auto-numbered-formalism manuscript hit exactly this on \\usepackage-free
        beamer compilation). Only the two environments beamer does not ship —
        proposition and hypothesis — should be declared here, and neither
        declaration should attempt to chain onto beamer's own theorem counter.
        """
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        self._make_renderer(tmp_path)
        header = write_slides_math_header(manuscript, tmp_path / "slides")
        assert header is not None
        content = header.read_text(encoding="utf-8")
        assert "\\newtheorem{proposition}{Proposition}" in content
        assert "\\newtheorem{hypothesis}{Hypothesis}" in content
        assert "\\newtheorem{theorem}" not in content
        assert "\\newtheorem{lemma}" not in content
        assert "\\newtheorem{corollary}" not in content
        assert "\\newtheorem{definition}" not in content

    def test_helper_declares_every_environment_the_extractor_skips(self, tmp_path):
        """The skip-set and the unconditional block must agree.

        ``write_slides_math_header`` drops a manuscript's ``\\newtheorem``
        declarations for environments it believes are "already declared or
        declared below/above". ``axiom`` and ``property`` sat in that set while
        being declared in neither place, so a manuscript using
        ``\\begin{property}`` had the declaration dropped on the way in and
        never restored -- beamer then failed with "Environment property
        undefined", and the render stage discarded the slide deck it had
        already written. Six of Part 1's decks were lost this way.

        This asserts the invariant rather than the two names: every environment
        the extractor refuses to carry over must be one beamer ships natively
        or one this header declares itself.
        """
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "preamble.md").write_text(
            "```latex\n\\newtheorem{property}{Property}[section]\n\\newtheorem{axiom}{Axiom}[section]\n```\n",
            encoding="utf-8",
        )
        self._make_renderer(tmp_path)
        header = write_slides_math_header(manuscript, tmp_path / "slides")
        assert header is not None
        content = header.read_text(encoding="utf-8")

        beamer_native = {"theorem", "lemma", "corollary", "definition", "example", "fact"}
        skipped = beamer_native | {"proposition", "hypothesis", "remark", "axiom", "property"}
        undeclared = [env for env in sorted(skipped - beamer_native) if f"\\newtheorem{{{env}}}" not in content]
        assert not undeclared, (
            "the extractor skips these environments as already handled, but the "
            f"header declares none of them: {undeclared}"
        )

    def test_helper_provides_cleveref_range_fallbacks(self, tmp_path):
        """``\\cref``'s fallback takes one argument and cannot cover
        ``\\crefrange``, which takes two. Without its own fallback beamer
        stopped at "Undefined control sequence" and Part 1's formal-framework
        deck failed to compile.
        """
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        self._make_renderer(tmp_path)
        header = write_slides_math_header(manuscript, tmp_path / "slides")
        assert header is not None
        content = header.read_text(encoding="utf-8")
        assert "\\providecommand{\\crefrange}[2]" in content
        assert "\\providecommand{\\Crefrange}[2]" in content

    def test_helper_supplies_a_non_floating_algorithm_environment(self, tmp_path):
        """`algorithm` must be replaced, not carried over.

        Loading it under beamer defines the environment but leaves its float
        machinery (\\@float@Hx, \\float@makebox) undefined, so a deck using it
        dies one step later than it would have without the package -- still
        dead, and harder to diagnose. 14 \\begin{algorithm} blocks in one
        manuscript cost a 51-page deck this way.
        """
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "preamble.md").write_text(
            "```latex\n\\usepackage{algorithm}\n\\usepackage{algpseudocode}\n```\n",
            encoding="utf-8",
        )
        self._make_renderer(tmp_path)
        header = write_slides_math_header(manuscript, tmp_path / "slides")
        assert header is not None
        content = header.read_text(encoding="utf-8")
        assert "\\usepackage{algpseudocode}" in content
        assert "\\usepackage{algorithm}" not in content, (
            "the float package was carried over; it has no beamer implementation"
        )
        assert "\\newenvironment{algorithm}" in content
        # \providecommand is a no-op for \caption -- the caption package has
        # already defined it, and then refuses it outside a float.
        assert "\\renewcommand{\\caption}" in content

        accessible_header = write_slides_math_header(
            manuscript,
            tmp_path / "accessible-slides",
            accessible_policy=AccessibleSlidePolicy(),
        )
        assert accessible_header is not None
        accessible_content = accessible_header.read_text(encoding="utf-8")
        algorithm_override = accessible_content.split("% Non-floating stand-in for the `algorithm` float.", 1)[1]
        assert r"\fontsize{20pt}{24pt}\selectfont" in algorithm_override
        assert r"\nobreak\small" not in algorithm_override

    def test_postprocessor_overrides_generated_codelisting_float(self):
        """The override lands after pandoc-crossref's preamble declaration."""
        tex = r"""\documentclass{beamer}
\newfloat{codelisting}{h}{lop}
\begin{document}
\begin{frame}
\begin{codelisting}
\caption[Short]{Long caption}
code
\end{codelisting}
\end{frame}
\end{document}
"""

        updated, changed = slides_renderer.make_codelisting_slide_safe(tex)

        assert changed == 1
        assert updated.index(r"\newfloat{codelisting}") < updated.index("Beamer-safe codelisting override")
        assert updated.index("Beamer-safe codelisting override") < updated.index(r"\begin{document}")
        assert r"\renewenvironment{codelisting}" in updated
        assert r"\renewcommand{\caption}[2][]" in updated
        assert r"\refstepcounter{codelisting}" in updated
        assert slides_renderer.make_codelisting_slide_safe(updated) == (updated, 0)

        accessible_updated, accessible_changed = slides_renderer.make_codelisting_slide_safe(
            tex,
            accessible_body_font_pt=20,
        )
        assert accessible_changed == 1
        override = accessible_updated.split("Beamer-safe codelisting override", 1)[1]
        assert r"\fontsize{20pt}{24pt}\selectfont" in override
        assert r"\footnotesize" not in override

    def test_beamer_renames_compiled_pdf_to_output_file(self, tmp_path):
        """When compile_latex writes {stem}_slides.pdf, normalize to output_file."""
        source = tmp_path / "slides.md"
        source.write_text("# Slide 1\n", encoding="utf-8")
        output_file = tmp_path / "slides.pdf"

        def fake_run(cmd, *args, **kwargs):
            tex_path = Path(cmd[cmd.index("-o") + 1])
            tex_path.write_text("\\documentclass{beamer}\\begin{document}foo\\end{document}\n")
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

        def fake_compile(tex, out_dir, **kwargs):
            compiled = out_dir / f"{tex.stem}.pdf"
            compiled.write_bytes(b"%PDF-1.4 fake\n")
            return compiled

        renderer = SlidesRenderer(
            RenderingConfig(output_dir=tmp_path),
            process_runner=fake_run,
            latex_compile=fake_compile,
        )

        result = renderer._render_beamer_with_paths(source, output_file, manuscript_dir=None, figures_dir=None)
        assert result == output_file
        assert output_file.exists()
        assert not (tmp_path / "slides_slides.pdf").exists()

    def test_beamer_pandoc_cmd_includes_h_flag_when_math_required(self, tmp_path):
        """End-to-end wiring: pandoc receives -H _slides_math_header.tex."""
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "preamble.md").write_text("```latex\n\\usepackage{unicode-math}\n```\n", encoding="utf-8")
        source = manuscript / "00_intro.md"
        source.write_text("# Slide 1\n\nHello.\n", encoding="utf-8")

        captured: dict[str, list[str]] = {}

        def fake_run(cmd, *args, **kwargs):
            captured["cmd"] = cmd
            tex_path = Path(cmd[cmd.index("-o") + 1])
            tex_path.write_text("\\documentclass{beamer}\\begin{document}foo\\end{document}\n")
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

        def fake_compile(tex, out_dir, **kwargs):
            compiled = out_dir / f"{tex.stem}.pdf"
            compiled.write_bytes(b"%PDF-1.4 fake\n")
            return compiled

        renderer = SlidesRenderer(
            RenderingConfig(output_dir=tmp_path),
            process_runner=fake_run,
            latex_compile=fake_compile,
        )

        output_file = tmp_path / "slides" / "00_intro_slides.pdf"
        result = renderer._render_beamer_with_paths(source, output_file, manuscript_dir=manuscript, figures_dir=None)
        assert result == output_file
        cmd = captured["cmd"]
        assert "-H" in cmd
        h_idx = cmd.index("-H")
        assert cmd[h_idx + 1].endswith("_slides_math_header.tex")
        assert Path(cmd[h_idx + 1]).exists()

    @pytest.mark.parametrize(
        ("slides_profile", "expected_aspect_ratio"),
        [
            ("archive", False),
            ("accessible", True),
        ],
    )
    def test_accessible_beamer_owns_widescreen_canvas_without_changing_archive(
        self,
        tmp_path,
        slides_profile,
        expected_aspect_ratio,
    ):
        """Only the opt-in projection profile requests Beamer's 16:9 canvas."""

        source = tmp_path / "00_intro.md"
        source.write_text(
            '{"blocks": [], "meta": {}}' if slides_profile == "accessible" else "# Slide 1\n\nHello.\n",
            encoding="utf-8",
        )
        (tmp_path / "slides").mkdir()
        captured: dict[str, list[str]] = {}

        def fake_run(cmd, *args, **kwargs):
            captured["cmd"] = cmd
            tex_path = Path(cmd[cmd.index("-o") + 1])
            tex_path.write_text("\\documentclass{beamer}\\begin{document}foo\\end{document}\n")
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

        def fake_compile(tex, out_dir, **kwargs):
            compiled = out_dir / f"{tex.stem}.pdf"
            writer = PdfWriter()
            writer.add_blank_page(width=453.543, height=255.12)
            with compiled.open("wb") as stream:
                writer.write(stream)
            return compiled

        renderer = SlidesRenderer(
            RenderingConfig(
                output_dir=tmp_path,
                slides_dir=tmp_path / "slides",
                slides_profile=slides_profile,
            ),
            process_runner=fake_run,
            latex_compile=fake_compile,
        )

        output_file = tmp_path / "slides" / "00_intro_slides.pdf"
        renderer._render_beamer_with_paths(source, output_file, manuscript_dir=None, figures_dir=None)

        aspect_ratio_arg = "--variable=aspectratio:169"
        assert (aspect_ratio_arg in captured["cmd"]) is expected_aspect_ratio

    def test_beamer_pandoc_cmd_includes_h_flag_for_citation_fallbacks(self, tmp_path):
        """The slides math header is now always written so natbib
        citation fallbacks are in scope, even when the preamble doesn't
        load unicode-math. Pandoc therefore always sees ``-H``.
        """
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "preamble.md").write_text("```latex\n\\usepackage{geometry}\n```\n", encoding="utf-8")
        source = manuscript / "00_intro.md"
        source.write_text("# Slide 1\n", encoding="utf-8")

        captured: dict[str, list[str]] = {}

        def fake_run(cmd, *args, **kwargs):
            captured["cmd"] = cmd
            tex_path = Path(cmd[cmd.index("-o") + 1])
            tex_path.write_text("\\documentclass{beamer}\\begin{document}foo\\end{document}\n")
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

        def fake_compile_return_path(tex, out_dir, **kw):
            compiled = out_dir / f"{tex.stem}.pdf"
            compiled.write_bytes(b"%PDF-1.4 fake\n")
            return compiled

        renderer = SlidesRenderer(
            RenderingConfig(output_dir=tmp_path),
            process_runner=fake_run,
            latex_compile=fake_compile_return_path,
        )

        output_file = tmp_path / "slides" / "00_intro_slides.pdf"
        renderer._render_beamer_with_paths(source, output_file, manuscript_dir=manuscript, figures_dir=None)
        assert "-H" in captured["cmd"]
        h_idx = captured["cmd"].index("-H")
        header_path = Path(captured["cmd"][h_idx + 1])
        assert header_path.name == "_slides_math_header.tex"
        content = header_path.read_text(encoding="utf-8")
        assert "\\providecommand{\\citep}" in content
