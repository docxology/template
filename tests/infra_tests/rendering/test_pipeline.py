"""Tests for infrastructure.rendering.pipeline.

Covers manuscript resolution, LaTeX preflight helpers, override delegation,
config loading, per-file rendering, and the public execute entrypoint.
No mocking framework — real files, subprocesses, and RenderManager subclasses.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.core.exceptions import RenderingError
from infrastructure.core.logging.diagnostic import DiagnosticReporter
from infrastructure.rendering import RenderManager
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.latex_validation import ValidationReport
from infrastructure.rendering.pipeline import (
    _has_generated_manuscript_ordering,
    _load_project_config_yaml,
    _log_manuscript_composition,
    _render_individual_files,
    _render_pipeline_impl,
    _resolve_manuscript_dir,
    _run_override_script,
    _validate_latex_packages,
    execute_render_pipeline,
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
    """Refreshes source config and bibliography when using injected markdown."""
    source = tmp_path / "manuscript"
    injected = tmp_path / "output" / "manuscript"
    source.mkdir()
    injected.mkdir(parents=True)
    (injected / "01_intro.md").write_text("# Intro")
    (source / "config.yaml").write_text("book:\n  title: Fresh\n", encoding="utf-8")
    (injected / "config.yaml").write_text("book:\n  title: Stale\n", encoding="utf-8")
    (source / "references.bib").write_text("@book{fresh,title={Fresh}}\n", encoding="utf-8")
    (injected / "references.bib").write_text("@book{stale,title={Stale}}\n", encoding="utf-8")

    result = _resolve_manuscript_dir(tmp_path)

    assert result == injected
    assert "Fresh" in (injected / "config.yaml").read_text(encoding="utf-8")
    assert "fresh" in (injected / "references.bib").read_text(encoding="utf-8")


def test_resolve_manuscript_dir_falls_back_to_source(tmp_path: Path) -> None:
    """Falls back to manuscript/ when injected dir is absent."""
    result = _resolve_manuscript_dir(tmp_path)

    assert result == tmp_path / "manuscript"


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
    """Returns 1 when the script cannot be executed (non-Python binary content)."""
    override = tmp_path / "scripts" / "_render_pdf_override.py"
    override.parent.mkdir(parents=True)
    # Write a script that immediately raises a SyntaxError so the interpreter
    # exits non-zero — this exercises the failure path without needing OSError.
    override.write_bytes(b"\x00\x01\x02\x03\xff\xfe")  # Invalid UTF-8 / binary

    result = _run_override_script(tmp_path, override)

    # A binary file run through Python will fail (exit non-zero or raise)
    assert result != 0


def test_run_override_script_missing_file(tmp_path: Path) -> None:
    """Returns non-zero when the override script path does not exist."""
    missing = tmp_path / "scripts" / "nonexistent.py"

    result = _run_override_script(tmp_path, missing)

    assert result != 0


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


# ---------------------------------------------------------------------------
# execute_render_pipeline override short-circuit
# ---------------------------------------------------------------------------


def _write_minimal_project_tree(project_root: Path) -> None:
    for sub in ("src", "tests", "scripts", "manuscript"):
        (project_root / sub).mkdir(parents=True, exist_ok=True)
    (project_root / "src" / "__init__.py").write_text("", encoding="utf-8")
    (project_root / "tests" / "__init__.py").write_text("", encoding="utf-8")
    (project_root / "manuscript" / "01_intro.md").write_text("# Intro", encoding="utf-8")


def test_render_pipeline_impl_short_circuits_on_override_script(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When _render_pdf_override.py exists, the pipeline delegates and skips LaTeX."""
    project = tmp_path / "override_proj"
    _write_minimal_project_tree(project)
    override = project / "scripts" / "_render_pdf_override.py"
    override.write_text("import sys\nsys.exit(42)\n", encoding="utf-8")

    monkeypatch.setattr(
        "infrastructure.rendering.pipeline.resolve_project_root",
        lambda _repo_root, name: project,
    )

    rc = _render_pipeline_impl("override_proj")

    assert rc == 42


def test_execute_render_pipeline_override_success_with_pdf(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
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

    monkeypatch.setattr(
        "infrastructure.rendering.pipeline.resolve_project_root",
        lambda _repo_root, name: project,
    )
    monkeypatch.setattr(
        "infrastructure.rendering._pipeline_summary.resolve_project_root",
        lambda _repo_root, name: project,
    )

    rc = execute_render_pipeline("override_ok")

    assert rc == 0
    assert (project / "output" / "pdf" / "override_ok_combined.pdf").is_file()
