#!/usr/bin/env python3
"""Tests for infrastructure.core.pipeline.definition."""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.core.pipeline.definition import (
    PipelinePurpose,
    PipelineSourceOrigin,
    PipelineSourceResolutionError,
    resolve_pipeline_source,
)


def _write_yaml(path: Path, label: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"stages:\n  - name: {label}\n    method: noop\n", encoding="utf-8")
    return path


def test_resolve_pipeline_source_prefers_explicit_relative_path(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    project_root = repo_root / "projects" / "demo"
    explicit_path = _write_yaml(repo_root / "custom" / "pipeline.yaml", "explicit")
    _write_yaml(project_root / "methods_pipeline.yaml", "methods")
    _write_yaml(project_root / "pipeline.yaml", "project")
    _write_yaml(repo_root / "infrastructure" / "core" / "pipeline" / "pipeline.yaml", "repo")

    source = resolve_pipeline_source(
        repo_root=repo_root,
        project_root=project_root,
        explicit_path=Path("custom/pipeline.yaml"),
        purpose=PipelinePurpose.METHODS,
    )

    assert source.path == explicit_path
    assert source.origin is PipelineSourceOrigin.EXPLICIT
    assert source.purpose is PipelinePurpose.METHODS


def test_resolve_pipeline_source_prefers_explicit_absolute_path(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    explicit_path = _write_yaml(tmp_path / "external" / "pipeline.yaml", "explicit")
    _write_yaml(repo_root / "infrastructure" / "core" / "pipeline" / "pipeline.yaml", "repo")

    source = resolve_pipeline_source(repo_root=repo_root, explicit_path=explicit_path)

    assert source.path == explicit_path
    assert source.origin is PipelineSourceOrigin.EXPLICIT
    assert source.purpose is PipelinePurpose.EXECUTION


def test_resolve_pipeline_source_errors_for_missing_explicit_path(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    missing = Path("missing/pipeline.yaml")

    with pytest.raises(PipelineSourceResolutionError, match="Explicit pipeline path does not exist"):
        resolve_pipeline_source(repo_root=repo_root, explicit_path=missing)


def test_resolve_pipeline_source_errors_for_explicit_directory(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    explicit_dir = repo_root / "custom"
    explicit_dir.mkdir(parents=True)

    with pytest.raises(PipelineSourceResolutionError, match="explicit pipeline candidate is not a file"):
        resolve_pipeline_source(repo_root=repo_root, explicit_path=Path("custom"))


def test_resolve_pipeline_source_prefers_project_methods_pipeline(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    project_root = repo_root / "projects" / "demo"
    methods_path = _write_yaml(project_root / "methods_pipeline.yaml", "methods")
    _write_yaml(project_root / "pipeline.yaml", "project")
    _write_yaml(repo_root / "infrastructure" / "core" / "pipeline" / "pipeline.yaml", "repo")

    source = resolve_pipeline_source(
        repo_root=repo_root,
        project_root=project_root,
        purpose=PipelinePurpose.METHODS,
    )

    assert source.path == methods_path
    assert source.origin is PipelineSourceOrigin.PROJECT_METHODS


def test_resolve_pipeline_source_uses_project_pipeline_for_execution(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    project_root = repo_root / "projects" / "demo"
    _write_yaml(project_root / "methods_pipeline.yaml", "methods")
    project_pipeline = _write_yaml(project_root / "pipeline.yaml", "project")
    _write_yaml(repo_root / "infrastructure" / "core" / "pipeline" / "pipeline.yaml", "repo")

    source = resolve_pipeline_source(
        repo_root=repo_root,
        project_root=project_root,
        purpose=PipelinePurpose.EXECUTION,
    )

    assert source.path == project_pipeline
    assert source.origin is PipelineSourceOrigin.PROJECT_PIPELINE


def test_resolve_pipeline_source_falls_back_to_project_pipeline_when_methods_missing(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    project_root = repo_root / "projects" / "demo"
    project_pipeline = _write_yaml(project_root / "pipeline.yaml", "project")
    _write_yaml(repo_root / "infrastructure" / "core" / "pipeline" / "pipeline.yaml", "repo")

    source = resolve_pipeline_source(
        repo_root=repo_root,
        project_root=project_root,
        purpose=PipelinePurpose.METHODS,
    )

    assert source.path == project_pipeline
    assert source.origin is PipelineSourceOrigin.PROJECT_PIPELINE


def test_resolve_pipeline_source_falls_back_to_repository_pipeline(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_pipeline = _write_yaml(repo_root / "infrastructure" / "core" / "pipeline" / "pipeline.yaml", "repo")

    source = resolve_pipeline_source(repo_root=repo_root)

    assert source.path == repo_pipeline
    assert source.origin is PipelineSourceOrigin.REPOSITORY_PIPELINE


def test_resolve_pipeline_source_falls_back_to_real_package_data(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"

    source = resolve_pipeline_source(repo_root=repo_root)

    assert source.origin is PipelineSourceOrigin.PACKAGE_DATA
    assert source.path.is_file()
    assert source.path.name == "pipeline.yaml"
