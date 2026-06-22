#!/usr/bin/env python3
"""Comprehensive tests for infrastructure/project/discovery.py.

Tests project discovery, validation, and metadata extraction functionality.
All tests use real data and tmp_path fixtures following the No Mocks Policy.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.project.project_info import ProjectInfo
from infrastructure.project.metadata import get_project_metadata
from infrastructure.project.validation import validate_project_structure
from infrastructure.project.discovery import discover_projects, get_default_project, resolve_project_root


def test_project_package_exports_match_docs() -> None:
    """`infrastructure.project` exports convenience public API."""
    from infrastructure.project import (
        ProjectInfo as ExportedProjectInfo,
        discover_projects as exported_discover_projects,
        get_project_metadata as exported_get_project_metadata,
        resolve_project_root as exported_resolve_project_root,
        validate_project_structure as exported_validate_project_structure,
    )

    assert ExportedProjectInfo is ProjectInfo
    assert exported_discover_projects is discover_projects
    assert exported_get_project_metadata is get_project_metadata
    assert exported_resolve_project_root is resolve_project_root
    assert exported_validate_project_structure is validate_project_structure


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def valid_project_structure(tmp_path: Path) -> Path:
    """Create a valid project structure with all components.

    Returns:
        Path to the project directory.
    """
    project_dir = tmp_path / "valid_project"

    # Required directories
    (project_dir / "src").mkdir(parents=True)
    (project_dir / "tests").mkdir()

    # Optional directories
    (project_dir / "scripts").mkdir()
    (project_dir / "manuscript").mkdir()
    (project_dir / "output").mkdir()

    # Required Python files
    (project_dir / "src" / "__init__.py").write_text('"""Valid project source."""\n')
    (project_dir / "src" / "core.py").write_text(
        '"""Core module."""\n\ndef compute(x: int) -> int:\n    return x * 2\n'
    )
    (project_dir / "tests" / "__init__.py").write_text('"""Test package."""\n')
    (project_dir / "tests" / "test_core.py").write_text(
        '"""Test core module."""\n\ndef test_compute():\n    from valid_project.src.core import compute\n    assert compute(2) == 4\n'
    )

    return project_dir


@pytest.fixture
def minimal_project_structure(tmp_path: Path) -> Path:
    """Create a minimal valid project (only src and tests).

    Returns:
        Path to the project directory.
    """
    project_dir = tmp_path / "minimal_project"

    (project_dir / "src").mkdir(parents=True)
    (project_dir / "tests").mkdir()
    (project_dir / "src" / "__init__.py").write_text("")
    (project_dir / "tests" / "__init__.py").write_text("")

    return project_dir


@pytest.fixture
def multi_project_repo(tmp_path: Path) -> Path:
    """Create a repository with multiple projects.

    Returns:
        Path to the repository root.
    """
    repo_root = tmp_path
    projects_dir = repo_root / "projects"
    projects_dir.mkdir()

    # Create project_alpha
    alpha = projects_dir / "project_alpha"
    (alpha / "src").mkdir(parents=True)
    (alpha / "tests").mkdir()
    (alpha / "src" / "__init__.py").write_text("")
    (alpha / "tests" / "__init__.py").write_text("")

    # Create project_beta with scripts and manuscript
    beta = projects_dir / "project_beta"
    (beta / "src").mkdir(parents=True)
    (beta / "tests").mkdir()
    (beta / "scripts").mkdir()
    (beta / "manuscript").mkdir()
    (beta / "src" / "main.py").write_text("def main(): pass\n")
    (beta / "tests" / "__init__.py").write_text("")

    # Create project_gamma (valid)
    gamma = projects_dir / "project_gamma"
    (gamma / "src").mkdir(parents=True)
    (gamma / "tests").mkdir()
    (gamma / "src" / "__init__.py").write_text("")
    (gamma / "tests" / "__init__.py").write_text("")

    return repo_root


# =============================================================================
# TestProjectInfo - Tests for ProjectInfo dataclass
# =============================================================================


class TestProjectInfo:
    """Test the ProjectInfo dataclass."""

    def test_create_project_info_with_all_attributes(self):
        """Test creating ProjectInfo with all attributes."""
        path = Path("/path/to/project")
        metadata = {
            "name": "test_project",
            "version": "1.0.0",
            "description": "A test project",
            "authors": ["Author One", "Author Two"],
        }

        info = ProjectInfo(
            name="test_project",
            path=path,
            has_src=True,
            has_tests=True,
            has_scripts=True,
            has_manuscript=True,
            metadata=metadata,
        )

        assert info.name == "test_project"
        assert info.path == path
        assert info.has_src is True
        assert info.has_tests is True
        assert info.has_scripts is True
        assert info.has_manuscript is True
        assert info.metadata == metadata
        assert info.metadata["authors"] == ["Author One", "Author Two"]

    def test_is_valid_with_src_and_tests(self):
        """Test is_valid returns True when both src and tests exist."""
        info = ProjectInfo(
            name="valid",
            path=Path("/path"),
            has_src=True,
            has_tests=True,
            has_scripts=False,
            has_manuscript=False,
            metadata={},
        )

        assert info.is_valid is True

    def test_is_valid_false_without_src(self):
        """Test is_valid returns False when src is missing."""
        info = ProjectInfo(
            name="no_src",
            path=Path("/path"),
            has_src=False,
            has_tests=True,
            has_scripts=True,
            has_manuscript=True,
            metadata={},
        )

        assert info.is_valid is False

    def test_is_valid_false_without_tests(self):
        """Test is_valid returns False when tests is missing."""
        info = ProjectInfo(
            name="no_tests",
            path=Path("/path"),
            has_src=True,
            has_tests=False,
            has_scripts=True,
            has_manuscript=True,
            metadata={},
        )

        assert info.is_valid is False

    def test_is_valid_false_without_both(self):
        """Test is_valid returns False when both src and tests are missing."""
        info = ProjectInfo(
            name="empty",
            path=Path("/path"),
            has_src=False,
            has_tests=False,
            has_scripts=False,
            has_manuscript=False,
            metadata={},
        )

        assert info.is_valid is False

    def test_project_info_with_empty_metadata(self):
        """Test ProjectInfo with empty metadata dictionary."""
        info = ProjectInfo(
            name="minimal",
            path=Path("/minimal"),
            has_src=True,
            has_tests=True,
            has_scripts=False,
            has_manuscript=False,
            metadata={},
        )

        assert info.metadata == {}
        assert info.is_valid is True


# =============================================================================
# TestValidateProjectStructure - Tests for validate_project_structure()
# =============================================================================


class TestValidateProjectStructure:
    """Test project structure validation."""

    def test_valid_complete_project(self, valid_project_structure: Path):
        """Test validation passes for a complete project structure."""
        is_valid, message = validate_project_structure(valid_project_structure)

        assert is_valid is True
        assert message == "Valid project structure"

    def test_valid_minimal_project(self, minimal_project_structure: Path):
        """Test validation passes for minimal project (only src and tests)."""
        is_valid, message = validate_project_structure(minimal_project_structure)

        assert is_valid is True
        assert message == "Valid project structure"

    def test_missing_src_directory(self, tmp_path: Path):
        """Test validation fails when src/ directory is missing."""
        project_dir = tmp_path / "no_src"
        (project_dir / "tests").mkdir(parents=True)
        (project_dir / "tests" / "__init__.py").write_text("")

        is_valid, message = validate_project_structure(project_dir)

        assert is_valid is False
        assert "Missing required directory: src" in message

    def test_missing_tests_directory(self, tmp_path: Path):
        """Test validation fails when tests/ directory is missing."""
        project_dir = tmp_path / "no_tests"
        (project_dir / "src").mkdir(parents=True)
        (project_dir / "src" / "__init__.py").write_text("")

        is_valid, message = validate_project_structure(project_dir)

        assert is_valid is False
        assert "Missing required directory: tests" in message

    def test_src_with_no_python_files(self, tmp_path: Path):
        """Test validation fails when src/ contains no Python files."""
        project_dir = tmp_path / "no_py"
        (project_dir / "src").mkdir(parents=True)
        (project_dir / "tests").mkdir()
        (project_dir / "src" / "readme.txt").write_text("Not a Python file")
        (project_dir / "src" / "data.json").write_text("{}")
        (project_dir / "tests" / "__init__.py").write_text("")

        is_valid, message = validate_project_structure(project_dir)

        assert is_valid is False
        assert "src/ directory contains no Python files" in message

    def test_nonexistent_directory(self):
        """Test validation fails for nonexistent directory."""
        nonexistent = Path("/this/path/does/not/exist/at/all")

        is_valid, message = validate_project_structure(nonexistent)

        assert is_valid is False
        assert "does not exist" in message

    def test_file_instead_of_directory(self, tmp_path: Path):
        """Test validation fails when path is a file instead of directory."""
        file_path = tmp_path / "actually_a_file.txt"
        file_path.write_text("I am a file, not a directory")

        is_valid, message = validate_project_structure(file_path)

        assert is_valid is False
        assert "Not a directory" in message

    def test_src_with_nested_python_files(self, tmp_path: Path):
        """Test validation passes when Python files are in nested directories."""
        project_dir = tmp_path / "nested"
        (project_dir / "src" / "submodule").mkdir(parents=True)
        (project_dir / "tests").mkdir()
        (project_dir / "src" / "submodule" / "core.py").write_text("# nested module")
        (project_dir / "tests" / "__init__.py").write_text("")

        is_valid, message = validate_project_structure(project_dir)

        assert is_valid is True
        assert message == "Valid project structure"

    def test_empty_project_directories(self, tmp_path: Path):
        """Test validation fails when src and tests exist but are empty."""
        project_dir = tmp_path / "empty_dirs"
        (project_dir / "src").mkdir(parents=True)
        (project_dir / "tests").mkdir()
        # Both directories exist but are empty - no Python files

        is_valid, message = validate_project_structure(project_dir)

        assert is_valid is False
        assert "src/ directory contains no Python files" in message


# =============================================================================
# TestDiscoverProjects - Tests for discover_projects()
# =============================================================================


class TestDiscoverProjects:
    """Test project discovery."""

    def test_discover_multiple_projects(self, multi_project_repo: Path):
        """Test discovering multiple valid projects."""
        projects = discover_projects(multi_project_repo)

        # Should find all three projects
        assert len(projects) == 3

        # Verify project names (sorted alphabetically)
        project_names = [p.name for p in projects]
        assert "project_alpha" in project_names
        assert "project_beta" in project_names
        assert "project_gamma" in project_names

    def test_discover_with_string_path(self, multi_project_repo: Path):
        """Test discover_projects accepts string path."""
        projects = discover_projects(str(multi_project_repo))

        assert len(projects) == 3

    def test_discover_empty_projects_directory(self, tmp_path: Path):
        """Test discovery returns empty list when projects directory is empty."""
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()

        projects = discover_projects(tmp_path)

        assert projects == []

    def test_discover_nonexistent_projects_directory(self, tmp_path: Path):
        """Test discovery returns empty list when projects directory doesn't exist."""
        # tmp_path exists but has no projects/ subdirectory
        projects = discover_projects(tmp_path)

        assert projects == []

    def test_discover_skips_hidden_directories(self, tmp_path: Path):
        """Test discovery skips directories starting with dot."""
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()

        # Create hidden directory (should be skipped)
        hidden = projects_dir / ".hidden_project"
        (hidden / "src").mkdir(parents=True)
        (hidden / "tests").mkdir()
        (hidden / "src" / "__init__.py").write_text("")
        (hidden / "tests" / "__init__.py").write_text("")

        # Create visible directory (should be found)
        visible = projects_dir / "visible_project"
        (visible / "src").mkdir(parents=True)
        (visible / "tests").mkdir()
        (visible / "src" / "__init__.py").write_text("")
        (visible / "tests" / "__init__.py").write_text("")

        projects = discover_projects(tmp_path)

        assert len(projects) == 1
        assert projects[0].name == "visible_project"

    def test_discover_skips_files_in_projects_directory(self, tmp_path: Path):
        """Test discovery skips regular files in projects directory."""
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()

        # Create a file (should be skipped)
        (projects_dir / "README.md").write_text("# Projects")
        (projects_dir / "notes.txt").write_text("Some notes")

        # Create a valid project
        valid = projects_dir / "valid_project"
        (valid / "src").mkdir(parents=True)
        (valid / "tests").mkdir()
        (valid / "src" / "__init__.py").write_text("")
        (valid / "tests" / "__init__.py").write_text("")

        projects = discover_projects(tmp_path)

        assert len(projects) == 1
        assert projects[0].name == "valid_project"

    def test_discover_skips_invalid_projects(self, tmp_path: Path):
        """Test discovery skips projects that fail validation."""
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()

        # Invalid project (missing tests)
        invalid1 = projects_dir / "invalid_no_tests"
        (invalid1 / "src").mkdir(parents=True)
        (invalid1 / "src" / "__init__.py").write_text("")

        # Invalid project (missing src)
        invalid2 = projects_dir / "invalid_no_src"
        (invalid2 / "tests").mkdir(parents=True)
        (invalid2 / "tests" / "__init__.py").write_text("")

        # Valid project
        valid = projects_dir / "valid_project"
        (valid / "src").mkdir(parents=True)
        (valid / "tests").mkdir()
        (valid / "src" / "__init__.py").write_text("")
        (valid / "tests" / "__init__.py").write_text("")

        projects = discover_projects(tmp_path)

        assert len(projects) == 1
        assert projects[0].name == "valid_project"

    def test_discover_returns_sorted_projects(self, tmp_path: Path):
        """Test discovered projects are sorted alphabetically."""
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()

        # Create projects in non-alphabetical order
        for name in ["zebra", "alpha", "mike", "beta"]:
            proj = projects_dir / name
            (proj / "src").mkdir(parents=True)
            (proj / "tests").mkdir()
            (proj / "src" / "__init__.py").write_text("")
            (proj / "tests" / "__init__.py").write_text("")

        projects = discover_projects(tmp_path)
        project_names = [p.name for p in projects]

        assert project_names == ["alpha", "beta", "mike", "zebra"]

    def test_discover_populates_project_info_correctly(self, tmp_path: Path):
        """Test discovered projects have correct ProjectInfo attributes."""
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()

        # Create project with all optional directories
        full = projects_dir / "full_project"
        (full / "src").mkdir(parents=True)
        (full / "tests").mkdir()
        (full / "scripts").mkdir()
        (full / "manuscript").mkdir()
        (full / "src" / "__init__.py").write_text("")
        (full / "tests" / "__init__.py").write_text("")

        projects = discover_projects(tmp_path)

        assert len(projects) == 1
        project = projects[0]

        assert project.name == "full_project"
        assert project.path == full
        assert project.has_src is True
        assert project.has_tests is True
        assert project.has_scripts is True
        assert project.has_manuscript is True
        assert project.is_valid is True

    @pytest.mark.parametrize("subdir", ["working", "ongoing", "published", "archive", "other"])
    def test_discover_excludes_archive_subfolder(self, tmp_path: Path, subdir: str):
        """Test discovery does not scan any NON_RENDERED_SUBDIRS subfolder."""
        # Create projects directory with valid project
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()
        active = projects_dir / "active_project"
        (active / "src").mkdir(parents=True)
        (active / "tests").mkdir()
        (active / "src" / "__init__.py").write_text("")
        (active / "tests" / "__init__.py").write_text("")

        # Create projects/<subdir>/ subfolder with valid project (should be ignored)
        non_rendered_dir = projects_dir / subdir
        non_rendered_dir.mkdir()
        nested = non_rendered_dir / "nested_project"
        (nested / "src").mkdir(parents=True)
        (nested / "tests").mkdir()
        (nested / "src" / "__init__.py").write_text("")
        (nested / "tests" / "__init__.py").write_text("")

        projects = discover_projects(tmp_path)

        # Only active project should be discovered; nested_project must not appear
        assert len(projects) == 1
        assert projects[0].name == "active_project"


