"""Tests for infrastructure.rendering._combined_exports — branch coverage.

Covers fixture-driven branches for:
- combined_source_files: existing/missing path, transmission-bookend classification
- resolve_combined_markdown: manuscript/output dir layout, pdf/tex candidates, empty/missing
- resolve_bibliography: deterministic union, path deduplication, and conflicts
- render_combined_docx: no combined-md early return; bibliography/crossref/metadata paths
- render_combined_epub: no combined-md early return; bibliography present vs absent
- render_combined_outputs: enable_* toggles; RenderingError and OSError paths
"""

from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path
from typing import Literal

import pytest

from infrastructure.core.exceptions import CompilationError, RenderingError, TemplateError
from infrastructure.publishing.transmission_bookends import BEGIN_FILENAME
from infrastructure.rendering._combined_exports import (
    render_combined_outputs,
)
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.core import RenderManager
from ._combined_exports_helpers import _make_reporter


# ---------------------------------------------------------------------------
# render_combined_outputs — config toggle branches
# ---------------------------------------------------------------------------


class _FailingRenderManager(RenderManager):
    """RenderManager subclass that raises on render calls to exercise error paths."""

    def __init__(self, cfg: RenderingConfig, *, raise_with: Exception) -> None:
        super().__init__(config=cfg)
        self._raise_with = raise_with

    def render_combined_pdf(
        self, source_files: list[Path], manuscript_dir: Path, project_name: str = "project"
    ) -> Path:
        """Always raises the configured exception."""
        raise self._raise_with

    def render_combined_web(
        self, source_files: list[Path], manuscript_dir: Path, project_name: str = "project"
    ) -> Path:
        """Always raises the configured exception."""
        raise self._raise_with


class _AuxRefreshManager(RenderManager):
    """Test manager that produces a real AUX map before exercising the slide resolver."""

    def __init__(
        self,
        tmp_path: Path,
        *,
        aux_text: str | None,
        slide_error: type[TemplateError] | None = None,
        slides_profile: Literal["archive", "accessible"] = "archive",
    ) -> None:
        cfg = RenderingConfig(
            enable_pdf=True,
            enable_html=False,
            enable_slides=True,
            enable_docx=False,
            enable_epub=False,
            pdf_dir=str(tmp_path / "output/pdf"),
            slides_dir=str(tmp_path / "output/slides"),
            figures_dir=str(tmp_path / "output/figures"),
            web_dir=str(tmp_path / "output/web"),
            slides_profile=slides_profile,
        )
        super().__init__(config=cfg)
        self.aux_text = aux_text
        self.slide_error = slide_error
        self.events: list[str] = []
        self.strict_refresh_flags: list[bool] = []

    def render_combined_pdf(
        self,
        source_files: list[Path],
        manuscript_dir: Path,
        project_name: str = "project",
    ) -> Path:
        self.events.append("combined")
        aux_path = Path(self.config.pdf_dir) / "_combined_manuscript.aux"
        assert not aux_path.exists(), "the orchestration boundary must remove stale AUX state"
        aux_path.parent.mkdir(parents=True, exist_ok=True)
        if self.aux_text is not None:
            aux_path.write_text(self.aux_text, encoding="utf-8")
        output = Path(self.config.pdf_dir) / "project_combined.pdf"
        output.write_bytes(b"%PDF-1.7\n")
        return output

    def render_slides(
        self,
        source_file: Path,
        output_format: str = "beamer",
        *,
        strict_cross_deck_refs: bool = False,
    ) -> Path:
        self.events.append(f"slides:{source_file.stem}")
        self.strict_refresh_flags.append(strict_cross_deck_refs)
        output = Path(self.config.slides_dir) / f"{source_file.stem}_slides.pdf"
        output.parent.mkdir(parents=True, exist_ok=True)
        if self.slide_error is not None and source_file.stem == "01_intro":
            output.write_bytes(b"partial refreshed deck")
            raise self.slide_error("forced Beamer refresh failure")
        post_pandoc_tex = (
            r"See Equation \eqref{eq:foreign}."
            if source_file.stem == "01_intro"
            else r"\begin{equation}\label{eq:foreign}x=1\end{equation}"
        )
        resolved = self.slides_renderer._resolve_cross_deck_refs(
            post_pandoc_tex,
            strict_cross_deck_refs=strict_cross_deck_refs,
        )
        output.write_text(resolved, encoding="utf-8")
        return output

    def render_accessible_slide_pair(
        self,
        source_file: Path,
        *,
        strict_cross_deck_refs: bool = False,
    ) -> tuple[Path, Path]:
        self.events.append(f"pair:{source_file.stem}")
        self.strict_refresh_flags.append(strict_cross_deck_refs)
        pdf_output = Path(self.config.slides_dir) / f"{source_file.stem}_slides.pdf"
        html_output = pdf_output.with_suffix(".html")
        pdf_output.parent.mkdir(parents=True, exist_ok=True)
        if self.slide_error is not None and source_file.stem == "01_intro":
            pdf_output.write_bytes(b"partial refreshed deck")
            html_output.write_text("partial refreshed deck", encoding="utf-8")
            raise self.slide_error("forced accessible-pair refresh failure")
        post_pandoc_tex = (
            r"See Equation \eqref{eq:foreign}."
            if source_file.stem == "01_intro"
            else r"\begin{equation}\label{eq:foreign}x=1\end{equation}"
        )
        resolved = self.slides_renderer._resolve_cross_deck_refs(
            post_pandoc_tex,
            strict_cross_deck_refs=strict_cross_deck_refs,
        )
        pdf_output.write_text(resolved, encoding="utf-8")
        html_output.write_text(resolved, encoding="utf-8")
        return pdf_output, html_output


def _write_foreign_ref_sources(manuscript_dir: Path) -> tuple[Path, Path]:
    """Write two decks with one canonical Pandoc cross-deck equation reference."""
    source = manuscript_dir / "01_intro.md"
    source.write_text("# Intro\n\nSee [@eq:foreign].\n", encoding="utf-8")
    definition = manuscript_dir / "03_results.md"
    definition.write_text("# Results\n\n$$x = 1$$ {#eq:foreign}\n", encoding="utf-8")
    return source, definition


def test_render_combined_outputs_pdf_disabled_skips(tmp_path: Path) -> None:
    """When enable_pdf is False, the PDF render path is skipped without error."""
    cfg = RenderingConfig(enable_pdf=False, enable_html=False, enable_docx=False, enable_epub=False)
    manager = RenderManager(config=cfg)
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    reporter = _make_reporter(tmp_path)

    # No exception expected
    render_combined_outputs(manager, [], manuscript_dir, "proj", reporter, rendered_count=0)


def test_render_combined_outputs_html_disabled_skips(tmp_path: Path) -> None:
    """When enable_html is False, the HTML render path is skipped without error."""
    cfg = RenderingConfig(enable_pdf=False, enable_html=False, enable_docx=False, enable_epub=False)
    manager = RenderManager(config=cfg)
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    reporter = _make_reporter(tmp_path)

    render_combined_outputs(manager, [], manuscript_dir, "proj", reporter, rendered_count=0)


def test_render_combined_outputs_refreshes_slides_after_current_aux_exists(tmp_path: Path) -> None:
    """The current combined AUX exists before the real slide resolver runs."""
    manager = _AuxRefreshManager(
        tmp_path,
        aux_text="\\relax\n\\newlabel{eq:foreign}{{7}{2}{Foreign equation}{equation.7}{}}\n",
    )
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    source, definition = _write_foreign_ref_sources(manuscript_dir)
    bookend = manuscript_dir / BEGIN_FILENAME
    bookend.write_text("# Generated transmission boundary\n", encoding="utf-8")
    skipped = manuscript_dir / "02_appendix.md"
    skipped.write_text("<!-- render:skip-beamer -->\n# Appendix\n", encoding="utf-8")
    aux_path = Path(manager.config.pdf_dir) / "_combined_manuscript.aux"
    aux_path.parent.mkdir(parents=True)
    aux_path.write_text("\\relax\n\\newlabel{eq:foreign}{{99}{1}}\n", encoding="utf-8")

    render_combined_outputs(
        manager,
        [bookend, source, skipped, definition],
        manuscript_dir,
        "templates/project",
        _make_reporter(tmp_path),
        rendered_count=1,
    )

    assert manager.events == ["combined", "slides:01_intro", "slides:03_results"]
    assert manager.strict_refresh_flags == [True, True]
    refreshed = Path(manager.config.slides_dir) / "01_intro_slides.pdf"
    assert "See Equation (7)." in refreshed.read_text(encoding="utf-8")


def test_render_combined_outputs_refreshes_accessible_pair_against_current_aux(tmp_path: Path) -> None:
    """Accessible Reveal and Beamer receive the same strict current-AUX refresh."""

    manager = _AuxRefreshManager(
        tmp_path,
        aux_text="\\relax\n\\newlabel{eq:foreign}{{7}{2}{Foreign equation}{equation.7}{}}\n",
        slides_profile="accessible",
    )
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    source, definition = _write_foreign_ref_sources(manuscript_dir)

    render_combined_outputs(
        manager,
        [source, definition],
        manuscript_dir,
        "templates/project",
        _make_reporter(tmp_path),
        rendered_count=1,
    )

    assert manager.events == ["combined", "pair:01_intro", "pair:03_results"]
    assert manager.strict_refresh_flags == [True, True]
    refreshed_pdf = Path(manager.config.slides_dir) / "01_intro_slides.pdf"
    refreshed_html = refreshed_pdf.with_suffix(".html")
    assert "See Equation (7)." in refreshed_pdf.read_text(encoding="utf-8")
    assert refreshed_html.read_text(encoding="utf-8") == refreshed_pdf.read_text(encoding="utf-8")


def test_render_combined_outputs_pdf_disabled_does_not_refresh_slides(tmp_path: Path) -> None:
    """A slides-enabled run cannot refresh from AUX when combined PDF is disabled."""

    class _NoRefreshManager(RenderManager):
        def __init__(self) -> None:
            super().__init__(
                config=RenderingConfig(
                    enable_pdf=False,
                    enable_html=False,
                    enable_slides=True,
                    enable_docx=False,
                    enable_epub=False,
                    figures_dir=str(tmp_path / "output/figures"),
                    slides_dir=str(tmp_path / "output/slides"),
                    web_dir=str(tmp_path / "output/web"),
                )
            )
            self.slide_calls = 0

        def render_slides(
            self,
            source_file: Path,
            output_format: str = "beamer",
            *,
            strict_cross_deck_refs: bool = False,
        ) -> Path:
            self.slide_calls += 1
            raise AssertionError("disabled combined PDF must not trigger a refresh")

    manager = _NoRefreshManager()
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    source = manuscript_dir / "01_intro.md"
    source.write_text("# Intro\n", encoding="utf-8")

    render_combined_outputs(
        manager,
        [source],
        manuscript_dir,
        "templates/project",
        _make_reporter(tmp_path),
        rendered_count=1,
    )

    assert manager.slide_calls == 0


def test_render_combined_outputs_pdf_failure_does_not_refresh_slides(tmp_path: Path) -> None:
    """A failed combined PDF never dispatches the dependent Beamer refresh."""

    class _NoRefreshManager(_FailingRenderManager):
        def __init__(self) -> None:
            cfg = RenderingConfig(
                enable_pdf=True,
                enable_html=False,
                enable_slides=True,
                enable_docx=False,
                enable_epub=False,
                pdf_dir=str(tmp_path / "output/pdf"),
                figures_dir=str(tmp_path / "output/figures"),
                slides_dir=str(tmp_path / "output/slides"),
                web_dir=str(tmp_path / "output/web"),
            )
            super().__init__(cfg, raise_with=RenderingError("forced combined failure"))
            self.slide_calls = 0

        def render_slides(
            self,
            source_file: Path,
            output_format: str = "beamer",
            *,
            strict_cross_deck_refs: bool = False,
        ) -> Path:
            self.slide_calls += 1
            raise AssertionError("failed combined PDF must not trigger a refresh")

    manager = _NoRefreshManager()
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    source = manuscript_dir / "01_intro.md"
    source.write_text("# Intro\n", encoding="utf-8")
    aux_path = Path(manager.config.pdf_dir) / "_combined_manuscript.aux"
    aux_path.parent.mkdir(parents=True)
    aux_path.write_text("stale aux\n", encoding="utf-8")

    render_combined_outputs(
        manager,
        [source],
        manuscript_dir,
        "templates/project",
        _make_reporter(tmp_path),
        rendered_count=1,
    )

    assert manager.slide_calls == 0
    assert not aux_path.exists()


def test_accessible_combined_pdf_failure_removes_first_pass_pair(tmp_path: Path) -> None:
    """Accessible fallback derivatives cannot survive a failed numbering source."""

    cfg = RenderingConfig(
        enable_pdf=True,
        enable_html=False,
        enable_slides=True,
        enable_docx=False,
        enable_epub=False,
        slides_profile="accessible",
        pdf_dir=str(tmp_path / "output/pdf"),
        figures_dir=str(tmp_path / "output/figures"),
        slides_dir=str(tmp_path / "output/slides"),
        web_dir=str(tmp_path / "output/web"),
    )
    manager = _FailingRenderManager(cfg, raise_with=RenderingError("forced combined failure"))
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    source = manuscript_dir / "01_intro.md"
    source.write_text("# Intro\n", encoding="utf-8")
    slides_dir = Path(cfg.slides_dir)
    slides_dir.mkdir(parents=True)
    first_pass_pdf = slides_dir / "01_intro_slides.pdf"
    first_pass_html = slides_dir / "01_intro_slides.html"
    first_pass_pdf.write_bytes(b"fallback beamer")
    first_pass_html.write_text("fallback reveal", encoding="utf-8")

    render_combined_outputs(
        manager,
        [source],
        manuscript_dir,
        "templates/project",
        _make_reporter(tmp_path),
        rendered_count=1,
    )

    assert not first_pass_pdf.exists()
    assert not first_pass_html.exists()


@pytest.mark.parametrize(
    ("aux_text", "message"),
    [
        (None, "without producing the AUX"),
        ("not a LaTeX AUX\n", "no parseable LaTeX structure"),
        ("\\relax\n\\newlabel{broken}{{1}{2}\n", "no parseable LaTeX structure"),
    ],
)
def test_render_combined_outputs_rejects_unusable_current_aux_and_removes_first_pass_decks(
    tmp_path: Path,
    aux_text: str | None,
    message: str,
) -> None:
    """Missing, malformed, or incomplete current AUX state cannot leave first-pass decks."""
    manager = _AuxRefreshManager(tmp_path, aux_text=aux_text)
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    sources = _write_foreign_ref_sources(manuscript_dir)
    slides_dir = Path(manager.config.slides_dir)
    slides_dir.mkdir(parents=True)
    for source in sources:
        (slides_dir / f"{source.stem}_slides.pdf").write_bytes(b"unresolved first pass")

    with pytest.raises(RenderingError, match=message):
        render_combined_outputs(
            manager,
            list(sources),
            manuscript_dir,
            "templates/project",
            _make_reporter(tmp_path),
            rendered_count=2,
        )

    assert manager.events == ["combined"]
    assert not list(slides_dir.glob("*_slides.pdf"))


def test_render_combined_outputs_strict_post_pandoc_refs_remove_unresolved_deck(tmp_path: Path) -> None:
    """A valid AUX without the canonical foreign label fails after Pandoc and cleans the deck."""
    manager = _AuxRefreshManager(tmp_path, aux_text=r"\relax" + "\n")
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    sources = _write_foreign_ref_sources(manuscript_dir)
    failed_output = Path(manager.config.slides_dir) / "01_intro_slides.pdf"
    failed_output.parent.mkdir(parents=True)
    failed_output.write_bytes(b"unresolved first pass")

    with pytest.raises(RenderingError, match="refusing to publish stale standalone decks"):
        render_combined_outputs(
            manager,
            list(sources),
            manuscript_dir,
            "templates/project",
            _make_reporter(tmp_path),
            rendered_count=2,
        )

    assert manager.strict_refresh_flags == [True, True]
    assert not failed_output.exists()


@pytest.mark.parametrize("error_type", [CompilationError, TemplateError])
def test_render_combined_outputs_removes_failed_refresh_deck(
    tmp_path: Path,
    error_type: type[TemplateError],
) -> None:
    """Compiler and renderer-domain failures cannot preserve the unresolved first pass."""
    manager = _AuxRefreshManager(
        tmp_path,
        aux_text="\\relax\n\\newlabel{eq:foreign}{{7}{2}}\n",
        slide_error=error_type,
    )
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    sources = _write_foreign_ref_sources(manuscript_dir)
    failed_output = Path(manager.config.slides_dir) / "01_intro_slides.pdf"
    failed_output.parent.mkdir(parents=True)
    failed_output.write_bytes(b"unresolved first pass")

    with pytest.raises(RenderingError, match="refusing to publish stale standalone decks"):
        render_combined_outputs(
            manager,
            list(sources),
            manuscript_dir,
            "templates/project",
            _make_reporter(tmp_path),
            rendered_count=2,
        )

    assert not failed_output.exists()
    assert (Path(manager.config.slides_dir) / "03_results_slides.pdf").is_file()


def test_accessible_final_aux_refresh_overflow_remains_fail_closed(tmp_path: Path) -> None:
    """A persistent overflow in the authoritative refresh deletes the pair and fails."""

    class FinalOverflowManager(_AuxRefreshManager):
        def render_accessible_slide_pair(
            self,
            source_file: Path,
            *,
            strict_cross_deck_refs: bool = False,
        ) -> tuple[Path, Path]:
            self.events.append(f"pair:{source_file.stem}")
            self.strict_refresh_flags.append(strict_cross_deck_refs)
            pdf_output = Path(self.config.slides_dir) / f"{source_file.stem}_slides.pdf"
            html_output = pdf_output.with_suffix(".html")
            pdf_output.parent.mkdir(parents=True, exist_ok=True)
            pdf_output.write_bytes(b"partial final beamer")
            html_output.write_text("partial final reveal", encoding="utf-8")
            raise RenderingError(
                "[slides.density.beamer-overflow] strict refresh still exceeds the frame",
                context={"diagnostic_code": "slides.density.beamer-overflow"},
            )

    manager = FinalOverflowManager(
        tmp_path,
        aux_text="\\relax\n\\newlabel{eq:foreign}{{7}{2}}\n",
        slides_profile="accessible",
    )
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    source, _definition = _write_foreign_ref_sources(manuscript_dir)

    with pytest.raises(RenderingError, match="slides.density.beamer-overflow"):
        render_combined_outputs(
            manager,
            [source],
            manuscript_dir,
            "templates/project",
            _make_reporter(tmp_path),
            rendered_count=0,
        )

    assert manager.strict_refresh_flags == [True]
    assert not (Path(manager.config.slides_dir) / "01_intro_slides.pdf").exists()
    assert not (Path(manager.config.slides_dir) / "01_intro_slides.html").exists()


def test_render_combined_outputs_aux_refresh_is_idempotent(tmp_path: Path) -> None:
    """Repeated current-AUX refreshes replace decks with identical resolved content."""
    manager = _AuxRefreshManager(
        tmp_path,
        aux_text="\\relax\n\\newlabel{eq:foreign}{{7}{2}}\n",
    )
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    sources = _write_foreign_ref_sources(manuscript_dir)
    reporter = _make_reporter(tmp_path)

    render_combined_outputs(
        manager,
        list(sources),
        manuscript_dir,
        "templates/project",
        reporter,
        rendered_count=2,
    )
    slides_dir = Path(manager.config.slides_dir)
    first_bytes = {path.name: path.read_bytes() for path in sorted(slides_dir.glob("*_slides.pdf"))}

    render_combined_outputs(
        manager,
        list(sources),
        manuscript_dir,
        "templates/project",
        reporter,
        rendered_count=2,
    )
    second_bytes = {path.name: path.read_bytes() for path in sorted(slides_dir.glob("*_slides.pdf"))}

    assert first_bytes == second_bytes
    assert manager.events.count("combined") == 2
    assert manager.events.count("slides:01_intro") == 2
    assert manager.events.count("slides:03_results") == 2


def test_render_combined_outputs_pdf_rendering_error_with_rendered_count(tmp_path: Path) -> None:
    """A RenderingError during PDF with rendered_count>0 logs the individual-PDF note."""
    cfg = RenderingConfig(
        enable_pdf=True,
        enable_html=False,
        enable_docx=False,
        enable_epub=False,
        pdf_dir=str(tmp_path / "output/pdf"),
        figures_dir=str(tmp_path / "output/figures"),
        web_dir=str(tmp_path / "output/web"),
    )
    err = RenderingError("simulated combined-PDF failure")
    manager = _FailingRenderManager(cfg, raise_with=err)
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    reporter = _make_reporter(tmp_path)

    # Must not propagate — caught and logged
    render_combined_outputs(manager, [], manuscript_dir, "proj", reporter, rendered_count=3)

    # The diagnostic event should be recorded
    assert len(reporter.events) >= 1


def test_render_combined_outputs_pdf_rendering_error_zero_rendered(tmp_path: Path) -> None:
    """A RenderingError during PDF with rendered_count=0 does NOT log the individual note."""
    cfg = RenderingConfig(
        enable_pdf=True,
        enable_html=False,
        enable_docx=False,
        enable_epub=False,
        pdf_dir=str(tmp_path / "output/pdf"),
        figures_dir=str(tmp_path / "output/figures"),
        web_dir=str(tmp_path / "output/web"),
    )
    err = RenderingError("combined-PDF failure")
    manager = _FailingRenderManager(cfg, raise_with=err)
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    reporter = _make_reporter(tmp_path)

    render_combined_outputs(manager, [], manuscript_dir, "proj", reporter, rendered_count=0)

    # Error still recorded despite rendered_count=0
    assert len(reporter.events) >= 1


def test_render_combined_outputs_pdf_oserror_with_existing_combined_md(tmp_path: Path) -> None:
    """An OSError during PDF render logs stderr/stdout attrs and stats the combined-md if present."""
    cfg = RenderingConfig(
        enable_pdf=True,
        enable_html=False,
        enable_docx=False,
        enable_epub=False,
        pdf_dir=str(tmp_path / "output/pdf"),
        figures_dir=str(tmp_path / "output/figures"),
        web_dir=str(tmp_path / "output/web"),
    )

    class _OSErrWithAttrs(OSError):
        stderr = "err output"
        stdout = "std output"

    err = _OSErrWithAttrs("disk full")
    manager = _FailingRenderManager(cfg, raise_with=err)
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()

    # Create the combined markdown so the stat-log branch is exercised
    tex_dir = tmp_path / "output" / "tex"
    tex_dir.mkdir(parents=True)
    (tex_dir / "_combined_manuscript.md").write_text("content\n")

    reporter = _make_reporter(tmp_path)

    render_combined_outputs(manager, [], manuscript_dir, "proj", reporter, rendered_count=0)


def test_render_combined_outputs_html_rendering_error_recorded(tmp_path: Path) -> None:
    """A RenderingError during HTML render is caught and recorded on the reporter."""
    cfg = RenderingConfig(
        enable_pdf=False,
        enable_html=True,
        enable_docx=False,
        enable_epub=False,
        figures_dir=str(tmp_path / "output/figures"),
        web_dir=str(tmp_path / "output/web"),
    )
    err = RenderingError("html render failed")
    manager = _FailingRenderManager(cfg, raise_with=err)
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    reporter = _make_reporter(tmp_path)

    render_combined_outputs(manager, [], manuscript_dir, "proj", reporter, rendered_count=0)

    assert len(reporter.events) >= 1


@pytest.mark.skipif(shutil.which("pandoc") is None, reason="pandoc is required for real DOCX rendering")
def test_render_combined_outputs_docx_is_independent_of_pdf(tmp_path: Path) -> None:
    """DOCX uses a fresh current combined source when PDF is disabled."""
    cfg = RenderingConfig(
        enable_pdf=False,
        enable_html=False,
        enable_docx=True,
        enable_epub=False,
        docx_dir=str(tmp_path / "output/docx"),
        figures_dir=str(tmp_path / "output/figures"),
        web_dir=str(tmp_path / "output/web"),
    )
    manager = RenderManager(config=cfg)
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    source = manuscript_dir / "01_intro.md"
    source.write_text("# Current DOCX source\n\nCurrent content.\n", encoding="utf-8")
    stale_pdf_md = tmp_path / "output" / "pdf" / "_combined_manuscript.md"
    stale_pdf_md.parent.mkdir(parents=True)
    stale_pdf_md.write_text("# STALE PDF SOURCE\n", encoding="utf-8")
    reporter = _make_reporter(tmp_path)

    render_combined_outputs(manager, [source], manuscript_dir, "templates/proj", reporter, rendered_count=0)

    output = tmp_path / "output" / "docx" / "proj_combined.docx"
    assert zipfile.is_zipfile(output)
    shared = tmp_path / "output" / "web" / "_combined_manuscript.md"
    assert "Current DOCX source" in shared.read_text(encoding="utf-8")
    assert "STALE PDF SOURCE" not in shared.read_text(encoding="utf-8")
    receipt = json.loads((tmp_path / "output" / "reports" / "manuscript_composition.json").read_text())
    assert receipt["algorithm"] == "shared-combined-markdown-v1"


@pytest.mark.skipif(shutil.which("pandoc") is None, reason="pandoc is required for real EPUB rendering")
def test_render_combined_outputs_epub_is_independent_of_pdf(tmp_path: Path) -> None:
    """EPUB uses a fresh current combined source when PDF is disabled."""
    cfg = RenderingConfig(
        enable_pdf=False,
        enable_html=False,
        enable_docx=False,
        enable_epub=True,
        epub_dir=str(tmp_path / "output/epub"),
        figures_dir=str(tmp_path / "output/figures"),
        web_dir=str(tmp_path / "output/web"),
    )
    manager = RenderManager(config=cfg)
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    source = manuscript_dir / "01_intro.md"
    source.write_text("# Current EPUB source\n\nCurrent content.\n", encoding="utf-8")
    stale_pdf_md = tmp_path / "output" / "pdf" / "_combined_manuscript.md"
    stale_pdf_md.parent.mkdir(parents=True)
    stale_pdf_md.write_text("# STALE PDF SOURCE\n", encoding="utf-8")
    reporter = _make_reporter(tmp_path)

    render_combined_outputs(manager, [source], manuscript_dir, "templates/proj", reporter, rendered_count=0)

    output = tmp_path / "output" / "epub" / "proj_combined.epub"
    assert zipfile.is_zipfile(output)
    shared = tmp_path / "output" / "web" / "_combined_manuscript.md"
    assert "Current EPUB source" in shared.read_text(encoding="utf-8")
    assert "STALE PDF SOURCE" not in shared.read_text(encoding="utf-8")
    receipt = json.loads((tmp_path / "output" / "reports" / "manuscript_composition.json").read_text())
    assert receipt["algorithm"] == "shared-combined-markdown-v1"
