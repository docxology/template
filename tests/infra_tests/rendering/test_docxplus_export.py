"""Tests for the optional docxplus export and stage orchestration without mocks."""

from __future__ import annotations

from pathlib import Path

from infrastructure.rendering.docxplus_export import (
    ExportResult,
    _cover_paragraphs,
    export_project,
    is_available,
)
from infrastructure.rendering.docxplus_stage import (
    _manuscript_identity,
    run_docxplus_export,
)


def test_export_result_dataclass_and_serialization():
    result = ExportResult(
        available=True,
        written=[Path("/tmp/test.docx"), Path("/tmp/test.docxplus")],
        carried_files=42,
        signed=True,
        skipped_reason="",
    )
    d = result.to_dict()
    assert d["available"] is True
    assert len(d["written"]) == 2
    assert d["carried_files"] == 42
    assert d["signed"] is True
    assert d["skipped_reason"] == ""


def test_cover_paragraphs_formatting():
    paras = _cover_paragraphs("sample_project", "Sample Title", "Dr. Author")
    assert paras[0] == "Sample Title"
    assert paras[1] == "Dr. Author"
    assert "conforming OOXML" in paras[2]
    assert "excludes build products" in paras[3]

    paras_fallback = _cover_paragraphs("sample_project", None, None)
    assert paras_fallback[0] == "sample_project"
    assert len(paras_fallback) == 3


def test_export_project_when_extra_is_absent(tmp_path: Path):
    """When the optional docxplus extra is not installed, export_project returns a clean skip."""
    # Under default test environment without docxplus installed
    if not is_available():
        project_dir = tmp_path / "my_project"
        project_dir.mkdir()
        out_dir = tmp_path / "output"

        res = export_project(project_dir, out_dir, project="my_project")
        assert res.available is False
        assert not res.written
        assert "docxplus is not installed" in res.skipped_reason


def test_export_project_when_project_root_missing(tmp_path: Path):
    missing_dir = tmp_path / "non_existent_project"
    out_dir = tmp_path / "output"

    res = export_project(missing_dir, out_dir, project="non_existent_project")
    if is_available():
        assert res.available is True
        assert not res.written
        assert "project root does not exist" in res.skipped_reason
    else:
        assert res.available is False
        assert "docxplus is not installed" in res.skipped_reason


def test_manuscript_identity_discovery(tmp_path: Path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    assert _manuscript_identity(project_root) == (None, None)

    manuscript_dir = project_root / "manuscript"
    manuscript_dir.mkdir()
    (manuscript_dir / "config.yaml").write_text(
        "paper:\n  title: 'Paper Title'\nauthors:\n  - name: 'Jane Doe'\n",
        encoding="utf-8",
    )
    title, author = _manuscript_identity(project_root)
    assert title == "Paper Title"
    assert author == "Jane Doe"


def test_run_docxplus_export_stage(tmp_path: Path):
    repo_root = tmp_path / "repo"
    project_root = repo_root / "projects" / "templates" / "template_test"
    project_root.mkdir(parents=True)
    (project_root / "README.md").write_text("content", encoding="utf-8")

    # Stage returns 0 (soft-skip if extra absent, or 0 on completion)
    exit_code = run_docxplus_export(repo_root, "templates/template_test")
    assert exit_code == 0
