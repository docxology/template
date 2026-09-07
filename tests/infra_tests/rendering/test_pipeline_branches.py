"""Additional branch coverage for _render_pipeline_impl.

Missing manuscript dir, skip_manuscript_hydration, manuscript_variable_script
failure, RenderManager init error, failed_files, reporter.events path, figure
truncation log, no-figures warning, transmission bookend except, and the
unresolved-config-token guard.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.rendering import RenderManager
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.pipeline import _render_pipeline_impl
from ._pipeline_helpers import (
    _dependencies_for,
    _make_project_with_manuscript,
    _write_minimal_project_tree,
)


# ---------------------------------------------------------------------------
# Additional branch coverage: missing manuscript dir, skip_manuscript_hydration,
# manuscript_variable_script failure, RenderManager init error, failed_files,
# reporter.events path, figure truncation log, no-figures warning,
# transmission bookend except, verify_pdf_outputs False, outer except in execute.
# ---------------------------------------------------------------------------


def test_render_pipeline_impl_missing_manuscript_dir_returns_one(
    tmp_path: Path,
) -> None:
    """No current manuscript inputs must not validate stale prior outputs."""
    project = tmp_path / "empty_ms_proj"
    _make_project_with_manuscript(project, n_md=0)

    # manuscript dir exists but has no .md files
    rc = _render_pipeline_impl("empty_ms_proj", repo_root=tmp_path, dependencies=_dependencies_for(project))

    assert rc == 1


def test_render_pipeline_impl_skip_manuscript_hydration_branch(
    tmp_path: Path,
) -> None:
    """skip_manuscript_hydration=True logs the skip message and does not call the variable script."""
    project = tmp_path / "skip_hydration_proj"
    _make_project_with_manuscript(project, n_md=1)

    called = []

    def _fail_if_called(project_root: Path, template_repo_root: object = None) -> int:
        called.append(True)
        return 0

    dependencies = _dependencies_for(project, hydrate_manuscript=_fail_if_called)
    rc = _render_pipeline_impl(
        "skip_hydration_proj",
        skip_manuscript_hydration=True,
        repo_root=tmp_path,
        dependencies=dependencies,
    )

    # Variable script must not have been called
    assert called == []
    # Pipeline proceeds (may return 0 or 1 depending on downstream tools, but not 1 from the script)
    assert rc in (0, 1)


def test_render_pipeline_propagates_accessible_slide_policy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Source-owned slide policy reaches the path-bound renderer config."""

    for env_name in (
        "SLIDES_PROFILE",
        "SLIDES_MAX_PROSE_WORDS",
        "SLIDES_MAX_TABLE_ROWS",
        "SLIDES_MIN_FIGURE_AREA_PERCENT",
        "SLIDES_TITLE_FONT_PT",
        "SLIDES_BODY_FONT_PT",
        "SLIDES_FIGURE_LABEL_FONT_PT",
        "SLIDES_READER_HREF",
    ):
        monkeypatch.delenv(env_name, raising=False)
    project = tmp_path / "accessible_slides_proj"
    _make_project_with_manuscript(project, n_md=1)
    (project / "manuscript" / "config.yaml").write_text(
        "render:\n"
        "  slides:\n"
        "    profile: accessible\n"
        "    max_prose_words: 72\n"
        "    max_table_rows: 7\n"
        "    min_figure_area_percent: 72\n"
        "    title_font_pt: 30\n"
        "    body_font_pt: 22\n"
        "    figure_label_font_pt: 17\n"
        "    reader_href: reader/index.html\n",
        encoding="utf-8",
    )
    captured: list[RenderingConfig] = []

    def _capture_manager(
        config: RenderingConfig,
        *,
        manuscript_dir: Path,
        figures_dir: Path,
    ) -> RenderManager:
        captured.append(config)
        return RenderManager(config, manuscript_dir=manuscript_dir, figures_dir=figures_dir)

    dependencies = _dependencies_for(project, manager_factory=_capture_manager)

    rc = _render_pipeline_impl(
        "accessible_slides_proj",
        skip_manuscript_hydration=True,
        repo_root=tmp_path,
        dependencies=dependencies,
    )

    assert rc == 0
    assert len(captured) == 1
    config = captured[0]
    assert config.slides_profile == "accessible"
    assert config.slides_max_prose_words == 72
    assert config.slides_max_table_rows == 7
    assert config.slides_min_figure_area_percent == 72
    assert config.slides_title_font_pt == 30
    assert config.slides_body_font_pt == 22
    assert config.slides_figure_label_font_pt == 17
    assert config.slides_reader_href == "reader/index.html"


def test_render_pipeline_impl_manuscript_variable_script_nonzero_exits_one(
    tmp_path: Path,
) -> None:
    """A non-zero return from _run_manuscript_variable_script causes _render_pipeline_impl to return 1."""
    project = tmp_path / "var_fail_proj"
    _make_project_with_manuscript(project, n_md=1)

    dependencies = _dependencies_for(project, hydrate_manuscript=lambda project_root, template_repo_root=None: 1)
    rc = _render_pipeline_impl("var_fail_proj", repo_root=tmp_path, dependencies=dependencies)

    assert rc == 1


def test_render_pipeline_impl_render_manager_init_raises_exits_one(
    tmp_path: Path,
) -> None:
    """An OSError/ValueError/TypeError during RenderManager construction returns 1."""
    project = tmp_path / "rm_init_fail_proj"
    _make_project_with_manuscript(project, n_md=1)

    original_render_manager = __import__("infrastructure.rendering", fromlist=["RenderManager"]).RenderManager

    class _FailingRenderManager(original_render_manager):
        def __init__(self, *args, **kwargs):
            raise OSError("Simulated init failure from real OSError")

    dependencies = _dependencies_for(project, manager_factory=_FailingRenderManager)
    rc = _render_pipeline_impl("rm_init_fail_proj", repo_root=tmp_path, dependencies=dependencies)

    assert rc == 1


@pytest.mark.slow
def test_render_pipeline_impl_failed_files_exits_one(
    tmp_path: Path,
) -> None:
    """When _render_individual_files returns non-empty failed_files, pipeline returns 1."""
    project = tmp_path / "fail_files_proj"
    _make_project_with_manuscript(project, n_md=1)

    def _always_fail(manager, source_files, reporter):
        for sf in source_files:
            if sf.suffix == ".md":
                from infrastructure.core.logging.diagnostic import DiagnosticEvent, DiagnosticSeverity

                reporter.events.append(
                    DiagnosticEvent(
                        category="RenderingError",
                        severity=DiagnosticSeverity.ERROR,
                        message=f"forced failure: {sf.name}",
                    )
                )
        return 0, [sf.name for sf in source_files if sf.suffix == ".md"]

    dependencies = _dependencies_for(project, render_individual=_always_fail)
    rc = _render_pipeline_impl("fail_files_proj", repo_root=tmp_path, dependencies=dependencies)

    assert rc == 1


def test_render_pipeline_impl_reporter_events_triggers_print_save(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """When reporter.events is non-empty both print_report and save_report are called."""
    project = tmp_path / "reporter_events_proj"
    _make_project_with_manuscript(project, n_md=1)

    print_called = []
    save_called = []

    def _inject_event_and_succeed(manager, source_files, reporter):
        from infrastructure.core.logging.diagnostic import DiagnosticEvent, DiagnosticSeverity

        reporter.events.append(
            DiagnosticEvent(
                category="Warning",
                severity=DiagnosticSeverity.WARNING,
                message="synthetic warning event",
            )
        )
        # Capture print_report / save_report calls
        original_print = reporter.print_report
        original_save = reporter.save_report

        def _track_print():
            print_called.append(True)
            original_print()

        def _track_save():
            save_called.append(True)
            original_save()

        reporter.print_report = _track_print
        reporter.save_report = _track_save
        return 0, []

    dependencies = _dependencies_for(project, render_individual=_inject_event_and_succeed)
    _render_pipeline_impl("reporter_events_proj", repo_root=tmp_path, dependencies=dependencies)

    assert print_called, "reporter.print_report() was not called when events were present"
    assert save_called, "reporter.save_report() was not called when events were present"


def test_render_pipeline_impl_figure_truncation_log(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """When more than 3 figures are found, the truncation log line fires."""
    import logging

    project = tmp_path / "fig_truncate_proj"
    _make_project_with_manuscript(project, n_md=1, n_figures=5)

    dependencies = _dependencies_for(project)

    with caplog.at_level(logging.INFO, logger="infrastructure.rendering.pipeline"):
        rc = _render_pipeline_impl("fig_truncate_proj", repo_root=tmp_path, dependencies=dependencies)

    truncation_logged = any("... and" in record.message and "more" in record.message for record in caplog.records)
    assert truncation_logged, "Expected truncation log '... and N more' when figures > 3"
    assert rc == 0


def test_render_pipeline_impl_no_figures_warning(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """When no figures are found a warning about missing figures is emitted."""
    import logging

    project = tmp_path / "no_fig_proj"
    _make_project_with_manuscript(project, n_md=1, n_figures=0)
    # Remove figures dir so verify_figures_exist returns empty found_figures
    import shutil

    shutil.rmtree(project / "output" / "figures", ignore_errors=True)

    dependencies = _dependencies_for(project, discover_manuscript=lambda manuscript_dir: [])

    with caplog.at_level(logging.WARNING, logger="infrastructure.rendering.pipeline"):
        _render_pipeline_impl("no_fig_proj", repo_root=tmp_path, dependencies=dependencies)

    no_fig_warned = any("No figures found" in record.message for record in caplog.records)
    assert no_fig_warned, "Expected warning about no figures found"


def test_render_pipeline_impl_transmission_bookend_exception_logged(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """When write_transmission_bookends raises, a warning is logged and pipeline continues."""
    import logging

    project = tmp_path / "bookend_exc_proj"
    _make_project_with_manuscript(project, n_md=1)

    def _raise(*args, **kwargs):
        raise RuntimeError("simulated bookend failure")

    dependencies = _dependencies_for(
        project,
        write_bookends=_raise,
    )

    with caplog.at_level(logging.WARNING, logger="infrastructure.rendering.pipeline"):
        rc = _render_pipeline_impl("bookend_exc_proj", repo_root=tmp_path, dependencies=dependencies)

    bookend_warned = any(
        "Transmission bookend" in record.message or "bookend" in record.message.lower() for record in caplog.records
    )
    assert bookend_warned, "Expected warning about skipped transmission bookends"
    assert rc == 0


def test_render_pipeline_impl_fails_on_unresolved_config_token(tmp_path: Path) -> None:
    """An unresolved config token exits non-zero instead of printing on the title page."""
    project = tmp_path / "token_proj"
    _write_minimal_project_tree(project)
    (project / "manuscript" / "config.yaml").write_text(
        'paper:\n  title: "{{PAPER_TITLE}}"\n',
        encoding="utf-8",
    )

    rc = _render_pipeline_impl("token_proj", repo_root=tmp_path, dependencies=_dependencies_for(project))

    assert rc == 1
