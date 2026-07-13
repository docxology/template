#!/usr/bin/env python3
"""Tests for infrastructure.project.git_guards."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from infrastructure.project import git_guards
from infrastructure.project.git_guards import (
    is_generated_artifact_path,
    is_public_template_output_path,
    offending_tracked_projects,
    tracked_generated_artifacts,
)


def _init_git_repo(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True)


def test_offending_tracked_projects_flags_non_exemplar(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    secret = tmp_path / "projects" / "secret_project" / "src"
    secret.mkdir(parents=True)
    (secret / "module.py").write_text("x = 1\n")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, check=True)

    offenders = offending_tracked_projects(tmp_path)
    assert "projects/secret_project/src/module.py" in offenders


def test_offending_tracked_projects_allows_exemplars(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    for name in ("template_code_project", "template_prose_project", "template_autoresearch_project"):
        src = tmp_path / "projects" / "templates" / name / "src"
        src.mkdir(parents=True)
        (src / "x.py").write_text("pass\n")
    (tmp_path / "projects" / "README.md").write_text("# projects\n")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "exemplars"], cwd=tmp_path, check=True)

    assert offending_tracked_projects(tmp_path) == []


def test_offending_tracked_projects_allows_known_nav_docs(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    for doc in ("README.md", "AGENTS.md", "PAI.md", "PROJECTS_PARADIGM.md"):
        (tmp_path / "projects" / doc).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / "projects" / doc).write_text(f"# {doc}\n")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "nav docs"], cwd=tmp_path, check=True)

    assert offending_tracked_projects(tmp_path) == []


def test_offending_tracked_projects_allows_templates_agents_doc(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    doc = tmp_path / "projects" / "templates" / "AGENTS.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("# template agents\n")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "templates agents"], cwd=tmp_path, check=True)

    assert offending_tracked_projects(tmp_path) == []


def test_offending_tracked_projects_allows_templates_design_doc(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    doc = tmp_path / "projects" / "templates" / "DESIGN.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("# template design\n")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "templates design"], cwd=tmp_path, check=True)

    assert offending_tracked_projects(tmp_path) == []


def test_offending_tracked_projects_flags_unknown_templates_toplevel_doc(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    doc = tmp_path / "projects" / "templates" / "NOTES.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("# notes\n")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "unknown templates doc"], cwd=tmp_path, check=True)

    assert "projects/templates/NOTES.md" in offending_tracked_projects(tmp_path)


def test_offending_tracked_projects_flags_unknown_toplevel_md(tmp_path: Path) -> None:
    """A non-allowlisted top-level projects/*.md must NOT slip past the guard.

    Regression for the wildcard ``projects/[^/]+\\.md`` rule that would have let
    any markdown file (e.g. a leaked private roster) be tracked under projects/.
    """
    _init_git_repo(tmp_path)
    (tmp_path / "projects").mkdir(parents=True)
    (tmp_path / "projects" / "secret_roster.md").write_text("# confidential\n")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "leak"], cwd=tmp_path, check=True)

    assert "projects/secret_roster.md" in offending_tracked_projects(tmp_path)


def test_tracked_generated_artifacts_allows_public_template_output_tree(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    project_artifact = tmp_path / "projects" / "templates" / "template_code_project" / "output" / "data" / "x.csv"
    copied_artifact = tmp_path / "output" / "templates" / "template_code_project" / "pdf" / "x.pdf"
    project_artifact.parent.mkdir(parents=True)
    copied_artifact.parent.mkdir(parents=True)
    project_artifact.write_text("a,b\n")
    copied_artifact.write_bytes(b"%PDF-1.7\n")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "artifact"], cwd=tmp_path, check=True)

    assert tracked_generated_artifacts(tmp_path) == []


def test_tracked_generated_artifacts_detects_private_output_tree(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    artifact = tmp_path / "projects" / "working" / "secret_project" / "output" / "data" / "x.csv"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("a,b\n")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "artifact"], cwd=tmp_path, check=True)

    assert "projects/working/secret_project/output/data/x.csv" in tracked_generated_artifacts(tmp_path)


def test_tracked_generated_artifacts_detects_oversized_public_template_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _init_git_repo(tmp_path)
    artifact = tmp_path / "output" / "templates" / "template_code_project" / "data" / "too-large.bin"
    artifact.parent.mkdir(parents=True)
    artifact.write_bytes(b"12345")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "artifact"], cwd=tmp_path, check=True)
    monkeypatch.setattr(git_guards, "PUBLIC_TEMPLATE_OUTPUT_MAX_BYTES", 4)

    assert "output/templates/template_code_project/data/too-large.bin" in tracked_generated_artifacts(tmp_path)


def test_tracked_generated_artifacts_detects_codegraph_index(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    artifact = tmp_path / ".codegraph" / "codegraph.db"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("local index\n")
    leann_index = tmp_path / ".leann" / "indexes" / "template-public" / "index.faiss"
    leann_index.parent.mkdir(parents=True)
    leann_index.write_text("local semantic index\n")
    local_agent_state = tmp_path / ".omo" / "ulw-loop" / "ledger.jsonl"
    local_agent_state.parent.mkdir(parents=True)
    local_agent_state.write_text("{}\n")
    project_artifact = tmp_path / "projects" / "templates" / "template_code_project" / ".codegraph" / "codegraph.db"
    project_artifact.parent.mkdir(parents=True)
    project_artifact.write_text("project index\n")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "artifact"], cwd=tmp_path, check=True)

    tracked = tracked_generated_artifacts(tmp_path)
    assert ".codegraph/codegraph.db" in tracked
    assert ".leann/indexes/template-public/index.faiss" in tracked
    assert ".omo/ulw-loop/ledger.jsonl" in tracked
    assert "projects/templates/template_code_project/.codegraph/codegraph.db" in tracked


def test_generated_artifact_matcher_detects_agent_state_roots() -> None:
    assert is_generated_artifact_path(".codegraph")
    assert is_generated_artifact_path("projects/templates/template_code_project/.codegraph")
    assert is_generated_artifact_path(".leann")
    assert is_generated_artifact_path("projects/templates/template_code_project/.leann/indexes/x")
    assert is_generated_artifact_path(".omo")
    assert is_generated_artifact_path(".omo/ulw-loop/ledger.jsonl")


def test_public_template_output_path_matcher_is_closed_to_private_outputs() -> None:
    assert is_public_template_output_path("projects/templates/template_code_project/output/data/results.json")
    assert is_public_template_output_path("output/templates/template_code_project/pdf/paper.pdf")
    assert not is_public_template_output_path("projects/working/private/output/data/results.json")
    assert not is_public_template_output_path("output/private_project/pdf/paper.pdf")
