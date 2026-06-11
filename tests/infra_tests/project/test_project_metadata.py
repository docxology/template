#!/usr/bin/env python3
"""Tests for infrastructure.project.metadata.get_project_metadata."""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.project.metadata import get_project_metadata


@pytest.fixture
def project_with_pyproject(tmp_path: Path) -> Path:
    """Create a project with pyproject.toml metadata."""
    project_dir = tmp_path / "pyproject_project"

    (project_dir / "src").mkdir(parents=True)
    (project_dir / "tests").mkdir()
    (project_dir / "src" / "__init__.py").write_text("")
    (project_dir / "tests" / "__init__.py").write_text("")

    pyproject_content = """\
[project]
name = "pyproject-project"
version = "2.1.0"
description = "A project with pyproject.toml metadata"
authors = [
    {name = "Alice Author", email = "alice@example.com"},
    {name = "Bob Builder", email = "bob@example.com"}
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
"""
    (project_dir / "pyproject.toml").write_text(pyproject_content)

    return project_dir


@pytest.fixture
def project_with_manuscript_config(tmp_path: Path) -> Path:
    """Create a project with manuscript/config.yaml metadata."""
    project_dir = tmp_path / "manuscript_project"

    (project_dir / "src").mkdir(parents=True)
    (project_dir / "tests").mkdir()
    (project_dir / "manuscript").mkdir()
    (project_dir / "src" / "__init__.py").write_text("")
    (project_dir / "tests" / "__init__.py").write_text("")

    config_content = """\
paper:
  title: "Research Paper Title"
  version: "1.0"

authors:
  - name: "Dr. Jane Researcher"
    email: "jane@university.edu"
    orcid: "0000-0001-2345-6789"
    affiliation: "University of Science"
    corresponding: true
  - name: "Prof. John Scholar"
    email: "john@institute.org"

publication:
  doi: "10.5281/zenodo.12345678"

keywords:
  - machine learning
  - research
"""
    (project_dir / "manuscript" / "config.yaml").write_text(config_content)

    return project_dir


class TestGetProjectMetadata:
    """Test project metadata extraction."""

    def test_default_metadata_when_no_config_files(self, tmp_path: Path):
        """Test default metadata returned when no config files exist."""
        project_dir = tmp_path / "no_config"
        project_dir.mkdir()

        metadata = get_project_metadata(project_dir)

        assert metadata["name"] == "no_config"
        assert metadata["description"] == ""
        assert metadata["version"] == "0.1.0"
        assert metadata["authors"] == []

    def test_pyproject_toml_metadata(self, project_with_pyproject: Path):
        """Test metadata extraction from pyproject.toml."""
        metadata = get_project_metadata(project_with_pyproject)

        assert metadata["name"] == "pyproject-project"
        assert metadata["version"] == "2.1.0"
        assert metadata["description"] == "A project with pyproject.toml metadata"
        assert "Alice Author" in metadata["authors"]
        assert "Bob Builder" in metadata["authors"]

    def test_manuscript_config_yaml_metadata(self, project_with_manuscript_config: Path):
        """Test metadata extraction from manuscript/config.yaml."""
        metadata = get_project_metadata(project_with_manuscript_config)

        assert metadata["title"] == "Research Paper Title"
        assert "Dr. Jane Researcher" in metadata["authors"]
        assert "Prof. John Scholar" in metadata["authors"]

    def test_manuscript_overrides_pyproject_authors(self, tmp_path: Path):
        """Test manuscript config.yaml authors override pyproject.toml authors."""
        project_dir = tmp_path / "override_project"
        (project_dir / "manuscript").mkdir(parents=True)

        pyproject_content = """\
[project]
name = "override-project"
version = "1.0.0"
authors = [
    {name = "PyProject Author"}
]
"""
        (project_dir / "pyproject.toml").write_text(pyproject_content)

        config_content = """\
paper:
  title: "Override Test"
authors:
  - name: "Config YAML Author"
  - name: "Second Config Author"
"""
        (project_dir / "manuscript" / "config.yaml").write_text(config_content)

        metadata = get_project_metadata(project_dir)

        assert metadata["name"] == "override-project"
        assert metadata["authors"] == ["Config YAML Author", "Second Config Author"]
        assert "PyProject Author" not in metadata["authors"]

    def test_pyproject_with_email_only_authors(self, tmp_path: Path):
        """Test pyproject.toml with authors having only email."""
        project_dir = tmp_path / "email_authors"
        project_dir.mkdir()

        pyproject_content = """\
[project]
name = "email-project"
authors = [
    {email = "only@email.com"},
    {name = "Named Author", email = "named@email.com"}
]
"""
        (project_dir / "pyproject.toml").write_text(pyproject_content)

        metadata = get_project_metadata(project_dir)

        assert "only@email.com" in metadata["authors"]
        assert "Named Author" in metadata["authors"]

    def test_invalid_pyproject_toml_handled_gracefully(self, tmp_path: Path):
        """Test graceful handling of invalid pyproject.toml."""
        project_dir = tmp_path / "invalid_pyproject"
        project_dir.mkdir()

        (project_dir / "pyproject.toml").write_text("this is [not valid toml content\n{broken: yaml}")

        metadata = get_project_metadata(project_dir)

        assert metadata["name"] == "invalid_pyproject"
        assert metadata["description"] == ""
        assert metadata["version"] == "0.1.0"
        assert metadata["authors"] == []

    def test_invalid_config_yaml_handled_gracefully(self, tmp_path: Path):
        """Test graceful handling of invalid config.yaml."""
        project_dir = tmp_path / "invalid_config"
        (project_dir / "manuscript").mkdir(parents=True)

        (project_dir / "manuscript" / "config.yaml").write_text(
            "invalid:\n  - yaml\n    broken: true\n  extra: [unbalanced"
        )

        metadata = get_project_metadata(project_dir)

        assert metadata["name"] == "invalid_config"
        assert metadata["version"] == "0.1.0"

    def test_empty_pyproject_toml(self, tmp_path: Path):
        """Test pyproject.toml with no [project] section."""
        project_dir = tmp_path / "empty_pyproject"
        project_dir.mkdir()

        pyproject_content = """\
[build-system]
requires = ["hatchling"]

[tool.black]
line-length = 88
"""
        (project_dir / "pyproject.toml").write_text(pyproject_content)

        metadata = get_project_metadata(project_dir)

        assert metadata["name"] == "empty_pyproject"
        assert metadata["version"] == "0.1.0"

    def test_config_yaml_without_paper_section(self, tmp_path: Path):
        """Test config.yaml without paper section."""
        project_dir = tmp_path / "no_paper"
        (project_dir / "manuscript").mkdir(parents=True)

        config_content = """\
authors:
  - name: "Only Authors"
publication:
  doi: "10.1234/test"
"""
        (project_dir / "manuscript" / "config.yaml").write_text(config_content)

        metadata = get_project_metadata(project_dir)

        assert "title" not in metadata
        assert metadata["authors"] == ["Only Authors"]
