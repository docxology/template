"""Tests for the execute_render_pipeline entrypoint and current format outputs.

Focused orchestration tests use RenderPipelineDependencies with deterministic
collaborators from _pipeline_helpers.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
import venv
from dataclasses import replace
from pathlib import Path

import pytest

from infrastructure.rendering._combined_exports import render_combined_outputs
from infrastructure.rendering._manuscript_source import render_individual_files
from infrastructure.rendering.manuscript_composition import COMPOSITION_RELATIVE_PATH, read_manuscript_composition
from infrastructure.rendering.pipeline import (
    RenderPipelineDependencies,
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


def test_render_stage_resolves_project_beside_entrypoint_with_independent_sdk(tmp_path: Path) -> None:
    """A separately located SDK must render the actual script's project tree."""
    source = Path(__file__).resolve().parents[3]
    repo = tmp_path / "current-source"
    stage = repo / "scripts/pipeline/stage_03_render.py"
    stage.parent.mkdir(parents=True)
    shutil.copy2(source / "scripts/pipeline/stage_03_render.py", stage)
    shutil.copy2(source / "scripts/__init__.py", repo / "scripts/__init__.py")
    project = repo / "projects/templates/template_test"
    _write_minimal_project_tree(project)
    marker = project / "selected-project.txt"
    (project / "scripts/z_generate_manuscript_variables.py").write_text(
        "from pathlib import Path\nPath('selected-project.txt').write_text(str(Path.cwd()))\nraise SystemExit(42)\n",
        encoding="utf-8",
    )
    venv.EnvBuilder(with_pip=False, symlinks=True).create(project / ".venv")
    code = f"""
import runpy, sys
from pathlib import Path
sys.path.insert(0, {str(source)!r})
import infrastructure.rendering.pipeline
assert not Path(infrastructure.rendering.pipeline.__file__).is_relative_to({str(repo)!r})
sys.argv = [{str(stage)!r}, '--project', 'templates/template_test']
runpy.run_path({str(stage)!r}, run_name='__main__')
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", code], cwd=tmp_path, capture_output=True, text=True, timeout=60, check=False
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert marker.read_text() == str(project)
    receipt = json.loads(next((project / "output/.pipeline/analysis").glob("*/*.json")).read_text())
    assert receipt["outcome"]["child_exit_code"] == 42
    assert receipt["worker"]["request"]["cwd"] == str(project)


def test_execute_render_pipeline_verify_pdf_false_returns_one(
    tmp_path: Path,
) -> None:
    """When the render orchestration returns 0 but output verification returns False, exit code is 1."""
    project = tmp_path / "verify_fail_proj"
    _make_project_with_manuscript(project, n_md=1)

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
        render_individual=render_individual_files,
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
    composition = read_manuscript_composition(project / COMPOSITION_RELATIVE_PATH)
    assert composition.combined_sha256 == hashlib.sha256(shared.read_bytes()).hexdigest()
    assert [row.path for row in composition.ordered_inputs] == ["manuscript/01_section.md"]
    for row in composition.ordered_inputs:
        assert row.sha256 == hashlib.sha256((project / row.path).read_bytes()).hexdigest()


def test_execute_render_pipeline_outer_exception_returns_one(
    tmp_path: Path,
) -> None:
    """An unexpected exception inside execute_render_pipeline is caught and returns 1."""

    def _raise(_repo_root: Path, _project_name: str) -> Path:
        raise RuntimeError("catastrophic unexpected error")

    dependencies = replace(RenderPipelineDependencies(), resolve_project=_raise)
    rc = execute_render_pipeline("any_project", repo_root=tmp_path, dependencies=dependencies)

    assert rc == 1
