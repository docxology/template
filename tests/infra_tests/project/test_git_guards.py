#!/usr/bin/env python3
"""Tests for infrastructure.project.git_guards."""

from __future__ import annotations

import subprocess
from pathlib import Path

from infrastructure.project.git_guards import offending_tracked_projects, tracked_generated_artifacts


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


def test_tracked_generated_artifacts_detects_output_tree(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    artifact = tmp_path / "projects" / "templates" / "template_code_project" / "output" / "data" / "x.csv"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("a,b\n")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "artifact"], cwd=tmp_path, check=True)

    tracked = tracked_generated_artifacts(tmp_path)
    assert "projects/templates/template_code_project/output/data/x.csv" in tracked


def test_tracked_generated_artifacts_detects_codegraph_index(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    artifact = tmp_path / ".codegraph" / "codegraph.db"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("local index\n")
    project_artifact = tmp_path / "projects" / "templates" / "template_code_project" / ".codegraph" / "codegraph.db"
    project_artifact.parent.mkdir(parents=True)
    project_artifact.write_text("project index\n")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "artifact"], cwd=tmp_path, check=True)

    tracked = tracked_generated_artifacts(tmp_path)
    assert ".codegraph/codegraph.db" in tracked
    assert "projects/templates/template_code_project/.codegraph/codegraph.db" in tracked
