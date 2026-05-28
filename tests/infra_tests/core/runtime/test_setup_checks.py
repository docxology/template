#!/usr/bin/env python3
"""Tests for infrastructure.core.runtime.setup_checks."""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.runtime.setup_checks import validate_project_discovery
from tests._support.projects import make_project


def _scaffold_project(root: Path, name: str) -> Path:
    return make_project(root, name, with_manuscript=True, with_scripts=True)


def test_validate_project_discovery_passes_for_scaffold(tmp_path: Path) -> None:
    name = "demo_project"
    _scaffold_project(tmp_path, name)
    assert validate_project_discovery(tmp_path, name) is True


def test_validate_project_discovery_fails_for_missing_structure(tmp_path: Path) -> None:
    name = "broken_project"
    (tmp_path / "projects" / name / "src").mkdir(parents=True)
    assert validate_project_discovery(tmp_path, name) is False


def test_validate_project_discovery_fails_when_no_projects(tmp_path: Path) -> None:
    (tmp_path / "projects").mkdir()
    assert validate_project_discovery(tmp_path, "anything") is False
