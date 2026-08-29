"""Tests for infrastructure.rendering.pipeline.

Covers manuscript resolution, LaTeX preflight helpers, override delegation,
config loading, per-file rendering, and the public execute entrypoint.
No mocking framework — real files, subprocesses, and RenderManager subclasses.
"""

from __future__ import annotations

import os
import shutil
import venv
import zipfile
from dataclasses import replace
from pathlib import Path

import pytest

from infrastructure.core.exceptions import RenderingError, TemplateError
from infrastructure.core.logging.diagnostic import DiagnosticReporter
from infrastructure.rendering import RenderManager
from infrastructure.rendering._combined_exports import render_combined_outputs
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.latex_validation import ValidationReport
from infrastructure.rendering.pipeline import (
    _has_generated_manuscript_ordering,
    _load_project_config_yaml,
    _log_manuscript_composition,
    _render_individual_files,
    _render_pipeline_impl,
    _resolve_manuscript_dir,
    _run_manuscript_variable_script,
    _run_override_script,
    _validate_latex_packages,
    execute_render_pipeline,
    RenderPipelineDependencies,
    verify_render_outputs,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_report(
    *,
    all_required: bool = True,
    missing_req: list[str] | None = None,
    missing_opt: list[str] | None = None,
) -> ValidationReport:
    """Build a real ValidationReport dataclass for testing _validate_latex_packages."""
    return ValidationReport(
        required_packages=[],
        optional_packages=[],
        missing_required=missing_req or [],
        missing_optional=missing_opt or [],
        all_required_available=all_required,
    )


# ---------------------------------------------------------------------------
# _resolve_manuscript_dir
# ---------------------------------------------------------------------------


def test_resolve_manuscript_dir_uses_injected_when_present(tmp_path: Path) -> None:
    """Prefers output/manuscript/ when it exists and contains .md files."""
    injected = tmp_path / "output" / "manuscript"
    injected.mkdir(parents=True)
    (injected / "01_intro.md").write_text("# Intro")

    result = _resolve_manuscript_dir(tmp_path)

    assert result == injected


def test_resolve_manuscript_dir_refreshes_injected_auxiliary_files(tmp_path: Path) -> None:
    """Refreshes source config, preamble, and bibliography with injected Markdown."""
    source = tmp_path / "manuscript"
    injected = tmp_path / "output" / "manuscript"
    source.mkdir()
    injected.mkdir(parents=True)
    (injected / "01_intro.md").write_text("# Intro")
    (source / "config.yaml").write_text("book:\n  title: Fresh\n", encoding="utf-8")
    (injected / "config.yaml").write_text("book:\n  title: Stale\n", encoding="utf-8")
    (source / "preamble.md").write_text("```latex\n% Fresh preamble\n```\n", encoding="utf-8")
    (injected / "preamble.md").write_text("```latex\n% Stale preamble\n```\n", encoding="utf-8")
    (source / "references.bib").write_text("@book{fresh,title={Fresh}}\n", encoding="utf-8")
    (injected / "references.bib").write_text("@book{stale,title={Stale}}\n", encoding="utf-8")

    result = _resolve_manuscript_dir(tmp_path)

    assert result == injected
    assert "Fresh" in (injected / "config.yaml").read_text(encoding="utf-8")
    assert "Fresh preamble" in (injected / "preamble.md").read_text(encoding="utf-8")
    assert "Stale preamble" not in (injected / "preamble.md").read_text(encoding="utf-8")
    assert "fresh" in (injected / "references.bib").read_text(encoding="utf-8")


def test_resolve_manuscript_dir_falls_back_to_source(tmp_path: Path) -> None:
    """Falls back to manuscript/ when injected dir is absent."""
    result = _resolve_manuscript_dir(tmp_path)

    assert result == tmp_path / "manuscript"


def test_resolve_manuscript_dir_falls_back_to_docs_source(tmp_path: Path) -> None:
    """Uses docs/manuscript directly when it is the populated source tree."""
    source = tmp_path / "docs" / "manuscript"
    source.mkdir(parents=True)
    (source / "01_intro.md").write_text("# Intro\n", encoding="utf-8")

    result = _resolve_manuscript_dir(tmp_path)

    assert result == source


def test_resolve_manuscript_dir_refreshes_injected_config_from_docs_source(tmp_path: Path) -> None:
    """Injected Markdown retains the canonical docs/manuscript configuration."""
    source = tmp_path / "docs" / "manuscript"
    injected = tmp_path / "output" / "manuscript"
    source.mkdir(parents=True)
    injected.mkdir(parents=True)
    (source / "01_intro.md").write_text("# Source\n", encoding="utf-8")
    (source / "config.yaml").write_text("paper:\n  title: Fresh docs config\n", encoding="utf-8")
    (source / "references.bib").write_text("@article{fresh,title={Fresh}}\n", encoding="utf-8")
    (injected / "01_intro.md").write_text("# Injected\n", encoding="utf-8")
    (injected / "config.yaml").write_text("paper:\n  title: Stale\n", encoding="utf-8")

    result = _resolve_manuscript_dir(tmp_path)

    assert result == injected
    assert "Fresh docs config" in (injected / "config.yaml").read_text(encoding="utf-8")
    assert "fresh" in (injected / "references.bib").read_text(encoding="utf-8")


def test_resolve_manuscript_dir_returns_manuscript_path_when_absent(tmp_path: Path) -> None:
    """Returns manuscript/ even when neither injected nor source trees exist."""
    project_root = tmp_path / "project"
    project_root.mkdir()

    result = _resolve_manuscript_dir(project_root)

    assert result == project_root / "manuscript"


def test_resolve_manuscript_dir_preserves_generated_config_ordering(tmp_path: Path) -> None:
    """Keeps injected config.yaml when it carries generated ordering marker."""
    source = tmp_path / "manuscript"
    injected = tmp_path / "output" / "manuscript"
    source.mkdir()
    injected.mkdir(parents=True)
    (injected / "01_intro.md").write_text("# Intro")
    (source / "config.yaml").write_text("book:\n  title: Source\n", encoding="utf-8")
    (injected / "config.yaml").write_text(
        "# Generated manuscript ordering\nbook:\n  title: Generated\n",
        encoding="utf-8",
    )

    result = _resolve_manuscript_dir(tmp_path)

    assert result == injected
    assert "Generated" in (injected / "config.yaml").read_text(encoding="utf-8")
    assert "Source" not in (injected / "config.yaml").read_text(encoding="utf-8")


def test_resolve_manuscript_dir_falls_back_when_injected_empty(tmp_path: Path) -> None:
    """Falls back to source when injected dir exists but has no .md files."""
    injected = tmp_path / "output" / "manuscript"
    injected.mkdir(parents=True)
    # directory exists but no .md files

    result = _resolve_manuscript_dir(tmp_path)

    assert result == tmp_path / "manuscript"


def test_resolve_manuscript_dir_ignores_non_md_files_in_injected(tmp_path: Path) -> None:
    """Falls back to source when injected dir has only non-.md files."""
    injected = tmp_path / "output" / "manuscript"
    injected.mkdir(parents=True)
    (injected / "notes.txt").write_text("just a note")

    result = _resolve_manuscript_dir(tmp_path)

    assert result == tmp_path / "manuscript"


# ---------------------------------------------------------------------------
# _log_manuscript_composition
# ---------------------------------------------------------------------------


def test_log_manuscript_composition_mixed_files(tmp_path: Path) -> None:
    """Logs without error for a mix of .md and .tex files."""
    md1 = tmp_path / "01_intro.md"
    md1.write_text("# Intro section")
    md2 = tmp_path / "02_methods.md"
    md2.write_text("# Methods section")
    tex = tmp_path / "preamble.tex"
    tex.write_text(r"\documentclass{article}")

    # Should not raise
    _log_manuscript_composition([md1, md2, tex])


def test_log_manuscript_composition_only_md(tmp_path: Path) -> None:
    """Handles markdown-only file list without error."""
    md = tmp_path / "01_abstract.md"
    md.write_text("Abstract content")

    _log_manuscript_composition([md])


def test_log_manuscript_composition_empty(tmp_path: Path) -> None:
    """Handles empty source file list without error."""
    _log_manuscript_composition([])


# ---------------------------------------------------------------------------
# _run_override_script  (real subprocess — no mocking)
# ---------------------------------------------------------------------------


def test_run_override_script_success(tmp_path: Path) -> None:
    """Returns 0 when a real override script exits successfully."""
    override = tmp_path / "scripts" / "_render_pdf_override.py"
    override.parent.mkdir(parents=True)
    override.write_text("import sys\nsys.exit(0)\n")

    result = _run_override_script(tmp_path, override)

    assert result == 0


def test_run_override_script_failure(tmp_path: Path) -> None:
    """Returns non-zero when a real override script exits with error."""
    override = tmp_path / "scripts" / "_render_pdf_override.py"
    override.parent.mkdir(parents=True)
    override.write_text("import sys\nsys.exit(1)\n")

    result = _run_override_script(tmp_path, override)

    assert result == 1


def test_run_override_script_non_zero_exit_code(tmp_path: Path) -> None:
    """Returns the specific non-zero exit code from the override script."""
    override = tmp_path / "scripts" / "_render_pdf_override.py"
    override.parent.mkdir(parents=True)
    override.write_text("import sys\nsys.exit(42)\n")

    result = _run_override_script(tmp_path, override)

    assert result == 42


def test_run_override_script_subprocess_error(tmp_path: Path) -> None:
    """Returns a non-zero code when the interpreter rejects malformed source."""
    override = tmp_path / "scripts" / "_render_pdf_override.py"
    override.parent.mkdir(parents=True)
    # A syntax error is portable across Python versions; arbitrary invalid
    # bytes were accepted as an empty script by one supported interpreter.
    override.write_text("def broken(:\n", encoding="utf-8")

    result = _run_override_script(tmp_path, override)

    # Malformed source run through Python must fail (exit non-zero or raise).
    assert result != 0


def test_run_override_script_missing_file(tmp_path: Path) -> None:
    """Returns non-zero when the override script path does not exist."""
    missing = tmp_path / "scripts" / "nonexistent.py"

    result = _run_override_script(tmp_path, missing)

    assert result != 0


@pytest.mark.skipif(os.name == "nt", reason="POSIX symlink semantics")
def test_run_manuscript_variable_script_uses_project_venv_python(tmp_path: Path) -> None:
    project = tmp_path / "project"
    script = project / "scripts" / "z_generate_manuscript_variables.py"
    script.parent.mkdir(parents=True)
    script.write_text(
        "\n".join(
            [
                "import os",
                "import sys",
                "from pathlib import Path",
                'Path("hydration_result.txt").write_text(',
                '    sys.executable + "\\n" + os.environ.get("TEMPLATE_REPO_ROOT", ""),',
                '    encoding="utf-8",',
                ")",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    venv_python = project / ".venv" / "bin" / "python"
    # Build a real virtual environment. A bare symlink to the host interpreter
    # is not a virtual environment and, on Python 3.14, correctly reports the
    # resolved host binary as ``sys.executable`` even when invoked via that
    # symlink. The production contract is specifically the project venv.
    venv.EnvBuilder(with_pip=False).create(project / ".venv")
    template_root = tmp_path / "template"
    template_root.mkdir()

    result = _run_manuscript_variable_script(project, template_repo_root=template_root)

    assert result == 0
    executable, injected_template_root = (project / "hydration_result.txt").read_text(encoding="utf-8").splitlines()
    assert executable == str(venv_python)
    assert injected_template_root == str(template_root)


# ---------------------------------------------------------------------------
# _validate_latex_packages  (real ValidationReport instances — no mocking)
# ---------------------------------------------------------------------------


def test_validate_latex_packages_all_available() -> None:
    """Returns 0 when all required packages are available."""
    result = _validate_latex_packages(report=_make_report(all_required=True))

    assert result == 0


def test_validate_latex_packages_missing_required() -> None:
    """Returns 1 when required packages are missing."""
    result = _validate_latex_packages(report=_make_report(all_required=False, missing_req=["multirow", "cleveref"]))

    assert result == 1


def test_validate_latex_packages_optional_missing_still_passes() -> None:
    """Returns 0 even when optional packages are absent."""
    result = _validate_latex_packages(report=_make_report(all_required=True, missing_opt=["minted"]))

    assert result == 0


def test_validate_latex_packages_empty_report() -> None:
    """Returns 0 for an all-clean report with no packages at all."""
    result = _validate_latex_packages(report=_make_report())

    assert result == 0


def test_validate_latex_packages_multiple_missing_required() -> None:
    """Returns 1 with multiple missing required packages."""
    result = _validate_latex_packages(
        report=_make_report(
            all_required=False,
            missing_req=["multirow", "cleveref", "doi", "newunicodechar"],
        )
    )

    assert result == 1


def test_validate_latex_packages_os_error_is_non_fatal() -> None:
    """Returns 0 (proceed anyway) when report=None and validator raises OSError.

    This test calls _validate_latex_packages() with no report so it runs the
    live validate_preamble_packages path.  On systems without kpsewhich the
    OSError handler returns 0 (non-fatal).  On systems with LaTeX installed
    the function also returns 0 (all packages available) or 1 (missing).
    Either way the function must not raise.
    """
    result = _validate_latex_packages()

    assert result in (0, 1)


def test_execute_render_pipeline_missing_project_returns_one(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing project root is a fast failure path that does not require LaTeX."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "projects").mkdir()
    rc = execute_render_pipeline("does_not_exist")
    assert rc == 1


# ---------------------------------------------------------------------------
# _has_generated_manuscript_ordering / _load_project_config_yaml
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("config_text", "expected"),
    [
        ("# Generated manuscript ordering\nbook:\n  title: X\n", True),
        ("book:\n  title: Plain\n", False),
    ],
)
def test_has_generated_manuscript_ordering(tmp_path: Path, config_text: str, expected: bool) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(config_text, encoding="utf-8")

    assert _has_generated_manuscript_ordering(cfg) is expected


def test_has_generated_manuscript_ordering_missing_file(tmp_path: Path) -> None:
    assert _has_generated_manuscript_ordering(tmp_path / "missing.yaml") is False


def test_load_project_config_yaml_missing_file(tmp_path: Path) -> None:
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()

    assert _load_project_config_yaml(manuscript_dir) is None


def test_load_project_config_yaml_valid_dict(tmp_path: Path) -> None:
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    (manuscript_dir / "config.yaml").write_text(
        "render:\n  formats:\n    pdf: true\n    html: false\n",
        encoding="utf-8",
    )

    loaded = _load_project_config_yaml(manuscript_dir)

    assert loaded is not None
    assert loaded["render"]["formats"]["pdf"] is True


def test_load_project_config_yaml_invalid_yaml(tmp_path: Path) -> None:
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    (manuscript_dir / "config.yaml").write_text("paper:\n  title: [\n  broken\n", encoding="utf-8")

    assert _load_project_config_yaml(manuscript_dir) is None


def test_load_project_config_yaml_non_mapping_root(tmp_path: Path) -> None:
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    (manuscript_dir / "config.yaml").write_text("- just\n- a list\n", encoding="utf-8")

    assert _load_project_config_yaml(manuscript_dir) is None


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


# ---------------------------------------------------------------------------
# execute_render_pipeline override short-circuit
# ---------------------------------------------------------------------------


def _write_minimal_project_tree(project_root: Path) -> None:
    for sub in ("src", "tests", "scripts", "manuscript"):
        (project_root / sub).mkdir(parents=True, exist_ok=True)
    (project_root / "src" / "__init__.py").write_text("", encoding="utf-8")
    (project_root / "tests" / "__init__.py").write_text("", encoding="utf-8")
    (project_root / "manuscript" / "01_intro.md").write_text("# Intro", encoding="utf-8")


def _dependencies_for(project_root: Path, **overrides: object) -> RenderPipelineDependencies:
    """Return deterministic collaborators for focused orchestration tests."""
    dependencies = RenderPipelineDependencies(
        resolve_project=lambda _repo_root, _name: project_root,
        hydrate_manuscript=lambda _project_root, template_repo_root=None: 0,
        write_bookends=lambda _project_root, _project_name, repo_root: None,
        validate_latex=lambda report=None: 0,
        render_individual=lambda _manager, _source_files, _reporter: (0, []),
        render_combined=lambda *_args, **_kwargs: None,
        generate_summary=lambda project_name, repo_root=None: {
            "project": project_name,
            "combined_pdf": None,
            "combined_html": None,
            "individual_pdfs": [],
            "web_outputs": [],
            "slides": [],
            "total_size_kb": 0,
        },
        log_summary=lambda _summary: None,
        verify_outputs=lambda _project_name, repo_root=None: True,
    )
    return replace(dependencies, **overrides)


def test_render_pipeline_impl_short_circuits_on_override_script(
    tmp_path: Path,
) -> None:
    """When _render_pdf_override.py exists, the pipeline delegates and skips LaTeX."""
    project = tmp_path / "override_proj"
    _write_minimal_project_tree(project)
    override = project / "scripts" / "_render_pdf_override.py"
    override.write_text("import sys\nsys.exit(42)\n", encoding="utf-8")

    rc = _render_pipeline_impl("override_proj", repo_root=tmp_path, dependencies=_dependencies_for(project))

    assert rc == 42


def test_execute_render_pipeline_override_success_with_pdf(
    tmp_path: Path,
) -> None:
    """Override script may finish the stage by writing a real combined PDF."""
    project = tmp_path / "override_ok"
    _write_minimal_project_tree(project)
    override = project / "scripts" / "_render_pdf_override.py"
    override.write_text(
        "\n".join(
            [
                "from pathlib import Path",
                "from reportlab.pdfgen import canvas",
                'out = Path("output/pdf")',
                "out.mkdir(parents=True, exist_ok=True)",
                'pdf = out / "override_ok_combined.pdf"',
                "c = canvas.Canvas(str(pdf))",
                "for page in range(30):",
                '    c.drawString(72, 720, "override ok " * 80)',
                "    c.showPage()",
                "c.save()",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    rc = execute_render_pipeline(
        "override_ok",
        repo_root=tmp_path,
        dependencies=_dependencies_for(project),
    )

    assert rc == 0
    assert (project / "output" / "pdf" / "override_ok_combined.pdf").is_file()


# ---------------------------------------------------------------------------
# Additional branch coverage: missing manuscript dir, skip_manuscript_hydration,
# manuscript_variable_script failure, RenderManager init error, failed_files,
# reporter.events path, figure truncation log, no-figures warning,
# transmission bookend except, verify_pdf_outputs False, outer except in execute.
# ---------------------------------------------------------------------------


def _make_project_with_manuscript(project_root: Path, *, n_md: int = 1, n_figures: int = 0) -> None:
    """Populate a minimal project tree with real manuscript files."""
    for sub in ("src", "tests", "scripts", "manuscript", "output/figures"):
        (project_root / sub).mkdir(parents=True, exist_ok=True)
    (project_root / "src" / "__init__.py").write_text("", encoding="utf-8")
    (project_root / "tests" / "__init__.py").write_text("", encoding="utf-8")
    for i in range(1, n_md + 1):
        (project_root / "manuscript" / f"0{i}_section.md").write_text(f"# Section {i}\n\nContent.\n", encoding="utf-8")
    for j in range(n_figures):
        fig = project_root / "output" / "figures" / f"fig_{j:02d}.png"
        fig.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)


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


def test_execute_render_pipeline_verify_pdf_false_returns_one(
    tmp_path: Path,
) -> None:
    """When _render_pipeline_impl returns 0 but verify_pdf_outputs returns False, exit code is 1."""
    project = tmp_path / "verify_fail_proj"
    _make_project_with_manuscript(project, n_md=1)

    # Make impl succeed immediately via override script exit(0)
    override = project / "scripts" / "_render_pdf_override.py"
    override.write_text("import sys\nsys.exit(0)\n", encoding="utf-8")
    dependencies = _dependencies_for(project, verify_outputs=lambda project_name, repo_root=None: False)
    rc = execute_render_pipeline("verify_fail_proj", repo_root=tmp_path, dependencies=dependencies)

    assert rc == 1


@pytest.mark.parametrize("with_stale_pdf", [False, True])
def test_execute_render_pipeline_html_only_needs_no_pdf_and_removes_stale_pdf(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    with_stale_pdf: bool,
) -> None:
    """An HTML-only run verifies HTML and never accepts or retains an old PDF."""

    for env_name in ("ENABLE_PDF", "ENABLE_HTML", "ENABLE_SLIDES", "ENABLE_DOCX", "ENABLE_EPUB"):
        monkeypatch.delenv(env_name, raising=False)
    project = tmp_path / "projects" / "templates" / "html_only_proj"
    _make_project_with_manuscript(project, n_md=1)
    (project / "manuscript" / "config.yaml").write_text(
        "render:\n  formats:\n    pdf: false\n    html: true\n    slides: false\n    docx: false\n    epub: false\n",
        encoding="utf-8",
    )
    stale_pdf = project / "output" / "pdf" / "html_only_proj_combined.pdf"
    if with_stale_pdf:
        stale_pdf.parent.mkdir(parents=True)
        stale_pdf.write_bytes(b"stale PDF from an earlier run")

    def _write_current_html(manager, *_args, **_kwargs) -> None:
        web_dir = Path(manager.config.web_dir)
        web_dir.mkdir(parents=True, exist_ok=True)
        (web_dir / "index.html").write_text(
            "<!doctype html><html><body>current run</body></html>",
            encoding="utf-8",
        )

    dependencies = _dependencies_for(
        project,
        render_combined=_write_current_html,
        verify_outputs=verify_render_outputs,
    )

    rc = execute_render_pipeline("html_only_proj", repo_root=tmp_path, dependencies=dependencies)

    assert rc == 0
    assert not stale_pdf.exists()
    assert (project / "output" / "web" / "index.html").is_file()


def test_execute_render_pipeline_pdf_enabled_rejects_stale_prior_pdf(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pre-run cleanup prevents an old combined PDF from satisfying strict verification."""

    for env_name in ("ENABLE_PDF", "ENABLE_HTML", "ENABLE_SLIDES", "ENABLE_DOCX", "ENABLE_EPUB"):
        monkeypatch.delenv(env_name, raising=False)
    project = tmp_path / "projects" / "templates" / "strict_pdf_proj"
    _make_project_with_manuscript(project, n_md=1)
    (project / "manuscript" / "config.yaml").write_text(
        "render:\n  formats:\n    pdf: true\n    html: false\n    slides: false\n    docx: false\n    epub: false\n",
        encoding="utf-8",
    )
    stale_pdf = project / "output" / "pdf" / "strict_pdf_proj_combined.pdf"
    stale_pdf.parent.mkdir(parents=True)
    stale_pdf.write_bytes(b"%PDF-1.7\n" + b"stale" * 4096 + b"\nstartxref\n0\n%%EOF\n")

    dependencies = _dependencies_for(project, verify_outputs=verify_render_outputs)
    rc = execute_render_pipeline("strict_pdf_proj", repo_root=tmp_path, dependencies=dependencies)

    assert rc == 1
    assert not stale_pdf.exists()


@pytest.mark.skipif(shutil.which("pandoc") is None, reason="pandoc is required for combined package rendering")
@pytest.mark.parametrize(("format_name", "extension"), [("docx", "docx"), ("epub", "epub")])
def test_execute_render_pipeline_combined_packages_do_not_require_pdf(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    format_name: str,
    extension: str,
) -> None:
    """DOCX-only and EPUB-only runs create and verify current real packages."""

    for env_name in ("ENABLE_PDF", "ENABLE_HTML", "ENABLE_SLIDES", "ENABLE_DOCX", "ENABLE_EPUB"):
        monkeypatch.delenv(env_name, raising=False)
    project_name = f"{format_name}_only_proj"
    project = tmp_path / "projects" / "templates" / project_name
    _make_project_with_manuscript(project, n_md=1)
    (project / "manuscript" / "config.yaml").write_text(
        "render:\n"
        "  formats:\n"
        "    pdf: false\n"
        "    html: false\n"
        "    slides: false\n"
        f"    docx: {str(format_name == 'docx').lower()}\n"
        f"    epub: {str(format_name == 'epub').lower()}\n",
        encoding="utf-8",
    )
    stale_pdf = project / "output" / "pdf" / f"{project_name}_combined.pdf"
    stale_combined = project / "output" / "pdf" / "_combined_manuscript.md"
    stale_pdf.parent.mkdir(parents=True)
    stale_pdf.write_bytes(b"stale PDF")
    stale_combined.write_text("# stale combined source\n", encoding="utf-8")

    dependencies = _dependencies_for(
        project,
        render_individual=_render_individual_files,
        render_combined=render_combined_outputs,
        verify_outputs=verify_render_outputs,
    )
    rc = execute_render_pipeline(project_name, repo_root=tmp_path, dependencies=dependencies)

    output = project / "output" / format_name / f"{project_name}_combined.{extension}"
    assert rc == 0
    assert zipfile.is_zipfile(output)
    assert not stale_pdf.exists()
    assert not stale_combined.exists()
    shared = project / "output" / "web" / "_combined_manuscript.md"
    assert "Section 1" in shared.read_text(encoding="utf-8")
    assert (project / "output" / "reports" / "manuscript_composition.json").is_file()


def test_execute_render_pipeline_outer_exception_returns_one(
    tmp_path: Path,
) -> None:
    """An unexpected exception inside execute_render_pipeline is caught and returns 1."""

    def _raise(_repo_root: Path, _project_name: str) -> Path:
        raise RuntimeError("catastrophic unexpected error")

    dependencies = replace(RenderPipelineDependencies(), resolve_project=_raise)
    rc = execute_render_pipeline("any_project", repo_root=tmp_path, dependencies=dependencies)

    assert rc == 1
