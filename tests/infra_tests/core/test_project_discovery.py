"""Tests for project discovery functionality using real implementations.

Tests the infrastructure.project module for discovering, validating,
and extracting metadata from projects in the projects/ directory.
Follows No Mocks Policy - all tests use real data and real execution.
"""

from pathlib import Path

import pytest

from infrastructure.project.discovery import (ProjectInfo, discover_projects,
                                              get_project_metadata,
                                              validate_project_structure)


class TestValidateProjectStructure:
    """Test project structure validation."""

    def test_valid_project_structure(self, tmp_path):
        """Test validation of a complete project structure."""
        # Create valid project structure
        project_dir = tmp_path / "test_project"
        (project_dir / "src").mkdir(parents=True)
        (project_dir / "tests").mkdir()
        (project_dir / "src" / "__init__.py").write_text("")
        (project_dir / "tests" / "__init__.py").write_text("")
        (project_dir / "tests" / "test_example.py").write_text(
            "def test_example(): pass"
        )

        is_valid, message = validate_project_structure(project_dir)
        assert is_valid is True
        assert "Valid project structure" in message

    def test_missing_src_directory(self, tmp_path):
        """Test validation fails when src/ directory is missing."""
        project_dir = tmp_path / "test_project"
        (project_dir / "tests").mkdir(parents=True)
        (project_dir / "tests" / "__init__.py").write_text("")

        is_valid, message = validate_project_structure(project_dir)
        assert is_valid is False
        assert "Missing required directory: src" in message

    def test_missing_tests_directory(self, tmp_path):
        """Test validation fails when tests/ directory is missing."""
        project_dir = tmp_path / "test_project"
        (project_dir / "src").mkdir(parents=True)
        (project_dir / "src" / "__init__.py").write_text("")

        is_valid, message = validate_project_structure(project_dir)
        assert is_valid is False
        assert "Missing required directory: tests" in message

    def test_src_no_python_files(self, tmp_path):
        """Test validation fails when src/ has no Python files."""
        project_dir = tmp_path / "test_project"
        (project_dir / "src").mkdir(parents=True)
        (project_dir / "tests").mkdir()
        (project_dir / "src" / "data.txt").write_text("not python")
        (project_dir / "tests" / "__init__.py").write_text("")

        is_valid, message = validate_project_structure(project_dir)
        assert is_valid is False
        assert "src/ directory contains no Python files" in message

    def test_nonexistent_directory(self):
        """Test validation fails for nonexistent directory."""
        nonexistent = Path("/nonexistent/path")
        is_valid, message = validate_project_structure(nonexistent)
        assert is_valid is False
        assert "does not exist" in message

    def test_file_instead_of_directory(self, tmp_path):
        """Test validation fails when path is a file instead of directory."""
        file_path = tmp_path / "not_a_directory"
        file_path.write_text("content")

        is_valid, message = validate_project_structure(file_path)
        assert is_valid is False
        assert "Not a directory" in message


class TestGetProjectMetadata:
    """Test project metadata extraction."""

    def test_pyproject_metadata(self, tmp_path):
        """Test metadata extraction from pyproject.toml."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()

        # Create pyproject.toml
        pyproject_content = """
[project]
name = "test_project"
version = "1.0.0"
description = "A test project"
authors = [
    {name = "Test Author", email = "test@example.com"}
]
"""
        (project_dir / "pyproject.toml").write_text(pyproject_content)

        metadata = get_project_metadata(project_dir)
        assert metadata["name"] == "test_project"
        assert metadata["version"] == "1.0.0"
        assert metadata["description"] == "A test project"
        assert metadata["authors"] == ["Test Author"]

    def test_manuscript_config_metadata(self, tmp_path):
        """Test metadata extraction from manuscript/config.yaml."""
        project_dir = tmp_path / "test_project"
        (project_dir / "manuscript").mkdir(parents=True)

        # Create config.yaml
        config_content = """
paper:
  title: "Test Paper Title"

authors:
  - name: "Config Author"
    email: "config@example.com"
"""
        (project_dir / "manuscript" / "config.yaml").write_text(config_content)

        metadata = get_project_metadata(project_dir)
        assert metadata["title"] == "Test Paper Title"
        assert metadata["authors"] == ["Config Author"]

    def test_default_metadata(self, tmp_path):
        """Test default metadata when no config files exist."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()

        metadata = get_project_metadata(project_dir)
        assert metadata["name"] == "test_project"
        assert metadata["description"] == ""
        assert metadata["version"] == "0.1.0"
        assert metadata["authors"] == []

    def test_manuscript_overrides_pyproject(self, tmp_path):
        """Test that manuscript config overrides pyproject.toml for authors."""
        project_dir = tmp_path / "test_project"
        (project_dir / "manuscript").mkdir(parents=True)

        # pyproject.toml
        pyproject_content = """
[project]
name = "test_project"
authors = [
    {name = "PyProject Author"}
]
"""
        (project_dir / "pyproject.toml").write_text(pyproject_content)

        # config.yaml (should override)
        config_content = """
authors:
  - name: "Config Author"
"""
        (project_dir / "manuscript" / "config.yaml").write_text(config_content)

        metadata = get_project_metadata(project_dir)
        assert metadata["name"] == "test_project"  # From pyproject
        assert metadata["authors"] == ["Config Author"]  # From config


class TestDiscoverProjects:
    """Test project discovery."""

    def test_discover_multiple_projects(self, tmp_path):
        """Test discovery of multiple valid projects."""
        # Create projects directory
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()

        # Create first project
        proj1_dir = projects_dir / "project1"
        (proj1_dir / "src").mkdir(parents=True)
        (proj1_dir / "tests").mkdir()
        (proj1_dir / "src" / "__init__.py").write_text("")
        (proj1_dir / "tests" / "__init__.py").write_text("")

        # Create second project
        proj2_dir = projects_dir / "project2"
        (proj2_dir / "src").mkdir(parents=True)
        (proj2_dir / "tests").mkdir()
        (proj2_dir / "src" / "__init__.py").write_text("")
        (proj2_dir / "tests" / "__init__.py").write_text("")

        # Create invalid project (missing tests)
        invalid_dir = projects_dir / "invalid"
        (invalid_dir / "src").mkdir(parents=True)
        (invalid_dir / "src" / "__init__.py").write_text("")

        # Create dot directory (should be ignored)
        dot_dir = projects_dir / ".hidden"
        dot_dir.mkdir()

        # Test discovery with real file system
        projects = discover_projects(tmp_path)
        assert len(projects) == 2  # Only valid projects, not dot directory

    def test_empty_projects_directory(self, tmp_path):
        """Test discovery when projects directory is empty."""
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()

        projects = discover_projects(projects_dir)
        assert projects == []

    def test_projects_directory_not_exists(self, tmp_path):
        """Test discovery when projects directory doesn't exist."""
        nonexistent = tmp_path / "nonexistent_projects"

        projects = discover_projects(nonexistent)
        assert projects == []


class TestProjectInfo:
    """Test ProjectInfo dataclass."""

    def test_project_info_creation(self):
        """Test creating ProjectInfo instance."""
        path = Path("/path/to/project")
        metadata = {"name": "test", "version": "1.0.0"}

        info = ProjectInfo(
            name="test",
            path=path,
            has_src=True,
            has_tests=True,
            has_scripts=False,
            has_manuscript=True,
            metadata=metadata,
        )

        assert info.name == "test"
        assert info.path == path
        assert info.has_src is True
        assert info.has_tests is True
        assert info.has_scripts is False
        assert info.has_manuscript is True
        assert info.metadata == metadata
        assert info.is_valid is True

    def test_project_info_invalid(self):
        """Test ProjectInfo.is_valid property."""
        # Valid project
        valid_info = ProjectInfo(
            name="valid",
            path=Path("/path"),
            has_src=True,
            has_tests=True,
            has_scripts=False,
            has_manuscript=False,
            metadata={},
        )
        assert valid_info.is_valid is True

        # Invalid project (missing src)
        invalid_info = ProjectInfo(
            name="invalid",
            path=Path("/path"),
            has_src=False,
            has_tests=True,
            has_scripts=False,
            has_manuscript=False,
            metadata={},
        )
        assert invalid_info.is_valid is False

        # Invalid project (missing tests)
        invalid_info2 = ProjectInfo(
            name="invalid2",
            path=Path("/path"),
            has_src=True,
            has_tests=False,
            has_scripts=False,
            has_manuscript=False,
            metadata={},
        )
        assert invalid_info2.is_valid is False
