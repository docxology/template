"""Tests for the execute_render_pipeline entrypoint and override short-circuit.

Focused orchestration tests use RenderPipelineDependencies with deterministic
collaborators from _pipeline_helpers.
"""

from __future__ import annotations

import shutil
import zipfile
from dataclasses import replace
from pathlib import Path

import pytest

from infrastructure.rendering._combined_exports import render_combined_outputs
from infrastructure.rendering.pipeline import (
    RenderPipelineDependencies,
    _render_individual_files,
    _render_pipeline_impl,
    execute_render_pipeline,
    verify_render_outputs,
)
from ._pipeline_helpers import (
    _dependencies_for,
    _make_project_with_manuscript,
    _write_minimal_project_tree,
)


def test_execute_render_pipeline_missing_project_returns_one(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing project root is a fast failure path that does not require LaTeX."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "projects").mkdir()
    rc = execute_render_pipeline("does_not_exist")
    assert rc == 1


# ---------------------------------------------------------------------------
# execute_render_pipeline override short-circuit
# ---------------------------------------------------------------------------


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
