"""Tests for infrastructure.rendering.pipeline._render_individual_files.

RenderManager subclasses record successes and failures — no mocks.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.core.exceptions import RenderingError, TemplateError
from infrastructure.core.logging.diagnostic import DiagnosticReporter
from infrastructure.rendering import RenderManager
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.pipeline import _render_individual_files


# ---------------------------------------------------------------------------
# _render_individual_files (RenderManager subclasses — no mocks)
# ---------------------------------------------------------------------------


class _EmptyRenderManager(RenderManager):
    """RenderManager that reports no outputs for every source file."""

    def render_all(self, source_file: Path) -> list[Path]:
        return []


class _ErrorRenderManager(RenderManager):
    """RenderManager that raises RenderingError for every source file."""

    def render_all(self, source_file: Path) -> list[Path]:
        raise RenderingError(
            f"render failed for {source_file.name}",
            context={"source": str(source_file)},
        )


class _TemplateErrorRenderManager(RenderManager):
    """RenderManager that raises a non-rendering template-domain error."""

    def render_all(self, source_file: Path) -> list[Path]:
        raise TemplateError(
            f"template failed for {source_file.name}",
            context={"source": str(source_file)},
        )


class _SuccessRenderManager(RenderManager):
    """RenderManager that writes a tiny marker file per source."""

    def __init__(self, config: RenderingConfig, output_dir: Path) -> None:
        super().__init__(config)
        self._output_dir = output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def render_all(self, source_file: Path) -> list[Path]:
        out = self._output_dir / f"{source_file.stem}.out"
        out.write_text("ok", encoding="utf-8")
        return [out]


def test_render_individual_files_empty_outputs(tmp_path: Path) -> None:
    reporter = DiagnosticReporter(project_name="t", output_dir=tmp_path / "reports", load_existing=False)
    md = tmp_path / "01_intro.md"
    md.write_text("# Intro", encoding="utf-8")
    manager = _EmptyRenderManager(RenderingConfig(output_dir=str(tmp_path)))

    rendered_count, failed_files = _render_individual_files(manager, [md], reporter)

    assert rendered_count == 0
    assert failed_files == []
    assert reporter.events == []


def test_render_individual_files_rendering_error(tmp_path: Path) -> None:
    reporter = DiagnosticReporter(project_name="t", output_dir=tmp_path / "reports", load_existing=False)
    md = tmp_path / "02_methods.md"
    md.write_text("# Methods", encoding="utf-8")
    manager = _ErrorRenderManager(RenderingConfig(output_dir=str(tmp_path)))

    rendered_count, failed_files = _render_individual_files(manager, [md], reporter)

    assert rendered_count == 0
    assert failed_files == ["02_methods.md"]
    assert len(reporter.events) == 1
    assert reporter.events[0].category == "RenderingError"


def test_render_individual_files_template_error_is_a_recorded_failure(tmp_path: Path) -> None:
    reporter = DiagnosticReporter(project_name="t", output_dir=tmp_path / "reports", load_existing=False)
    md = tmp_path / "02b_template.md"
    md.write_text("# Template", encoding="utf-8")
    manager = _TemplateErrorRenderManager(RenderingConfig(output_dir=str(tmp_path)))

    rendered_count, failed_files = _render_individual_files(manager, [md], reporter)

    assert rendered_count == 0
    assert failed_files == ["02b_template.md"]
    assert len(reporter.events) == 1
    assert reporter.events[0].category == "TemplateError"


def test_render_individual_files_success(tmp_path: Path) -> None:
    reporter = DiagnosticReporter(project_name="t", output_dir=tmp_path / "reports", load_existing=False)
    md = tmp_path / "03_results.md"
    md.write_text("# Results", encoding="utf-8")
    out_dir = tmp_path / "outputs"
    manager = _SuccessRenderManager(RenderingConfig(output_dir=str(tmp_path)), out_dir)

    rendered_count, failed_files = _render_individual_files(manager, [md], reporter)

    assert rendered_count == 1
    assert failed_files == []
    assert (out_dir / "03_results.out").is_file()


@pytest.mark.parametrize(("enable_pdf", "expected_failures"), [(True, []), (False, ["23_limitations.md"])])
def test_render_individual_files_defers_only_pre_aux_accessible_beamer_overflow(
    tmp_path: Path,
    enable_pdf: bool,
    expected_failures: list[str],
) -> None:
    """Only a pipeline-owned post-AUX refresh can supersede first-pass overflow."""

    source = tmp_path / "23_limitations.md"
    source.write_text("# Limitations\n\nSee the discussion section.\n", encoding="utf-8")

    class OverflowingSlidesRenderer:
        def render_accessible_pair(self, _source_file: Path, **_kwargs: object) -> tuple[Path, Path]:
            raise RenderingError(
                "[slides.density.beamer-overflow] preliminary fallback prose exceeds the frame",
                context={"diagnostic_code": "slides.density.beamer-overflow"},
            )

    class WritingWebRenderer:
        def render(self, source_file: Path) -> Path:
            output = tmp_path / f"{source_file.stem}.html"
            output.write_text("<!doctype html><title>Current section</title>", encoding="utf-8")
            return output

    manager = RenderManager(
        RenderingConfig(
            enable_pdf=enable_pdf,
            enable_html=True,
            enable_slides=True,
            slides_profile="accessible",
            output_dir=str(tmp_path / "output"),
            pdf_dir=str(tmp_path / "output/pdf"),
            slides_dir=str(tmp_path / "output/slides"),
            web_dir=str(tmp_path / "output/web"),
        ),
        slides_renderer=OverflowingSlidesRenderer(),
        web_renderer=WritingWebRenderer(),
    )
    reporter = DiagnosticReporter(project_name="t", output_dir=tmp_path / "reports", load_existing=False)

    _rendered_count, failed_files = _render_individual_files(manager, [source], reporter)

    assert failed_files == expected_failures
    assert len(reporter.events) == len(expected_failures)
    if reporter.events:
        assert reporter.events[0].context["format_failures"] == [
            {
                "format": "accessible slide pair",
                "diagnostic_code": "slides.density.beamer-overflow",
            }
        ]


def test_render_individual_files_cleans_stale_web_artifacts(tmp_path: Path) -> None:
    """Render-only reruns remove obsolete generated HTML before writing current pages.

    Cleanup targets only pages this renderer produces (the combined
    ``index.html`` and ``{parent}__{stem}.html`` per-section pages) — an
    unrelated project HTML artifact sitting in the same ``output/web/`` dir
    (e.g. a project's own ``dashboard.html``) must survive.
    """
    reporter = DiagnosticReporter(project_name="t", output_dir=tmp_path / "reports", load_existing=False)
    md = tmp_path / "04_discussion.md"
    md.write_text("# Discussion", encoding="utf-8")
    web_dir = tmp_path / "output" / "web"
    web_dir.mkdir(parents=True)
    stale_html = web_dir / "manuscript__old_section_name.html"
    stale_index = web_dir / "index.html"
    stale_combined = web_dir / "_combined_manuscript.md"
    preserved_asset = web_dir / "style.css"
    preserved_dashboard = web_dir / "dashboard.html"
    stale_html.write_text("<html>stale</html>", encoding="utf-8")
    stale_index.write_text("<html>stale index</html>", encoding="utf-8")
    stale_combined.write_text("# stale combined", encoding="utf-8")
    preserved_asset.write_text("body { color: black; }", encoding="utf-8")
    preserved_dashboard.write_text("<html>dashboard</html>", encoding="utf-8")
    manager = _SuccessRenderManager(
        RenderingConfig(output_dir=str(tmp_path / "output"), web_dir=str(web_dir), enable_html=True),
        tmp_path / "outputs",
    )

    rendered_count, failed_files = _render_individual_files(manager, [md], reporter)

    assert rendered_count == 1
    assert failed_files == []
    assert not stale_html.exists()
    assert not stale_index.exists()
    assert not stale_combined.exists()
    assert preserved_asset.is_file()
    assert preserved_dashboard.is_file()
