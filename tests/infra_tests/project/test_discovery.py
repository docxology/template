#!/usr/bin/env python3
"""Comprehensive tests for infrastructure/project/discovery.py.

Tests project discovery, validation, and metadata extraction functionality.
All tests use real data and tmp_path fixtures following the No Mocks Policy.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.project.discovery import (
    ProjectInfo,
    discover_projects,
    get_default_project,
    get_project_metadata,
    validate_project_structure,
)


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
def project_with_pyproject(tmp_path: Path) -> Path:
    """Create a project with pyproject.toml metadata.

    Returns:
        Path to the project directory.
    """
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
    """Create a project with manuscript/config.yaml metadata.

    Returns:
        Path to the project directory.
    """
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
    (beta / "src" / "main.py").write_text('def main(): pass\n')
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
# TestGetProjectMetadata - Tests for get_project_metadata()
# =============================================================================


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

        # pyproject.toml with one set of authors
        pyproject_content = """\
[project]
name = "override-project"
version = "1.0.0"
authors = [
    {name = "PyProject Author"}
]
"""
        (project_dir / "pyproject.toml").write_text(pyproject_content)

        # config.yaml with different authors (should override)
        config_content = """\
paper:
  title: "Override Test"
authors:
  - name: "Config YAML Author"
  - name: "Second Config Author"
"""
        (project_dir / "manuscript" / "config.yaml").write_text(config_content)

        metadata = get_project_metadata(project_dir)

        # Name should come from pyproject.toml
        assert metadata["name"] == "override-project"
        # Authors should be overridden by config.yaml
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

        # First author has only email, should use that
        assert "only@email.com" in metadata["authors"]
        # Second author has name, should use that
        assert "Named Author" in metadata["authors"]

    def test_invalid_pyproject_toml_handled_gracefully(self, tmp_path: Path):
        """Test graceful handling of invalid pyproject.toml."""
        project_dir = tmp_path / "invalid_pyproject"
        project_dir.mkdir()

        # Write invalid TOML content
        (project_dir / "pyproject.toml").write_text(
            "this is [not valid toml content\n{broken: yaml}"
        )

        # Should return default metadata without raising exception
        metadata = get_project_metadata(project_dir)

        assert metadata["name"] == "invalid_pyproject"
        assert metadata["description"] == ""
        assert metadata["version"] == "0.1.0"
        assert metadata["authors"] == []

    def test_invalid_config_yaml_handled_gracefully(self, tmp_path: Path):
        """Test graceful handling of invalid config.yaml."""
        project_dir = tmp_path / "invalid_config"
        (project_dir / "manuscript").mkdir(parents=True)

        # Write invalid YAML content
        (project_dir / "manuscript" / "config.yaml").write_text(
            "invalid:\n  - yaml\n    broken: true\n  extra: [unbalanced"
        )

        # Should return default metadata without raising exception
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

        # Should use defaults since [project] section is missing
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

        # Should not have title since paper section is missing
        assert "title" not in metadata
        # But should have authors
        assert metadata["authors"] == ["Only Authors"]


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

    def test_discover_excludes_projects_archive(self, tmp_path: Path):
        """Test discovery does not scan projects_archive directory."""
        # Create projects directory with valid project
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()
        active = projects_dir / "active_project"
        (active / "src").mkdir(parents=True)
        (active / "tests").mkdir()
        (active / "src" / "__init__.py").write_text("")
        (active / "tests" / "__init__.py").write_text("")

        # Create projects_archive directory with valid project (should be ignored)
        archive_dir = tmp_path / "projects_archive"
        archive_dir.mkdir()
        archived = archive_dir / "archived_project"
        (archived / "src").mkdir(parents=True)
        (archived / "tests").mkdir()
        (archived / "src" / "__init__.py").write_text("")
        (archived / "tests" / "__init__.py").write_text("")

        projects = discover_projects(tmp_path)

        # Only active project should be discovered
        assert len(projects) == 1
        assert projects[0].name == "active_project"


# =============================================================================
# TestNestedProjectDiscovery - Tests for nested/program project discovery
# =============================================================================


class TestNestedProjectDiscovery:
    """Test discovery of projects nested within program directories."""

    def test_discover_nested_projects_in_program_directory(self, tmp_path: Path):
        """Test discovering projects nested within a program directory."""
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()

        # Create program directory with nested projects (like cognitive_integrity)
        program_dir = projects_dir / "my_program"
        program_dir.mkdir()

        # Create nested project 1
        proj1 = program_dir / "project_one"
        (proj1 / "src").mkdir(parents=True)
        (proj1 / "tests").mkdir()
        (proj1 / "src" / "__init__.py").write_text("")
        (proj1 / "tests" / "__init__.py").write_text("")

        # Create nested project 2
        proj2 = program_dir / "project_two"
        (proj2 / "src").mkdir(parents=True)
        (proj2 / "tests").mkdir()
        (proj2 / "src" / "__init__.py").write_text("")
        (proj2 / "tests" / "__init__.py").write_text("")

        projects = discover_projects(tmp_path)

        assert len(projects) == 2
        qualified_names = [p.qualified_name for p in projects]
        assert "my_program/project_one" in qualified_names
        assert "my_program/project_two" in qualified_names

        # Verify program field is set correctly
        for proj in projects:
            assert proj.program == "my_program"

    def test_program_directory_not_treated_as_project(self, tmp_path: Path):
        """Test that program directories (no src/tests) are not treated as projects."""
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()

        # Create program directory without src/tests
        program_dir = projects_dir / "my_program"
        program_dir.mkdir()
        (program_dir / "README.md").write_text("# My Program")

        # No nested projects, so nothing should be discovered
        projects = discover_projects(tmp_path)
        assert len(projects) == 0

    def test_mixed_standalone_and_program_projects(self, tmp_path: Path):
        """Test discovery finds both standalone projects and nested program projects."""
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()

        # Create standalone project (like code_project)
        standalone = projects_dir / "standalone_project"
        (standalone / "src").mkdir(parents=True)
        (standalone / "tests").mkdir()
        (standalone / "src" / "__init__.py").write_text("")
        (standalone / "tests" / "__init__.py").write_text("")

        # Create program directory with nested projects
        program_dir = projects_dir / "my_program"
        program_dir.mkdir()

        nested = program_dir / "nested_project"
        (nested / "src").mkdir(parents=True)
        (nested / "tests").mkdir()
        (nested / "src" / "__init__.py").write_text("")
        (nested / "tests" / "__init__.py").write_text("")

        projects = discover_projects(tmp_path)

        assert len(projects) == 2
        qualified_names = [p.qualified_name for p in projects]
        assert "standalone_project" in qualified_names
        assert "my_program/nested_project" in qualified_names

        # Verify standalone project has no program
        standalone_proj = next(p for p in projects if p.name == "standalone_project")
        assert standalone_proj.program == ""
        assert standalone_proj.qualified_name == "standalone_project"

        # Verify nested project has program set
        nested_proj = next(p for p in projects if p.name == "nested_project")
        assert nested_proj.program == "my_program"
        assert nested_proj.qualified_name == "my_program/nested_project"

    def test_qualified_name_property(self, tmp_path: Path):
        """Test qualified_name property for both standalone and nested projects."""
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()

        # Standalone
        standalone = projects_dir / "alpha"
        (standalone / "src").mkdir(parents=True)
        (standalone / "tests").mkdir()
        (standalone / "src" / "__init__.py").write_text("")
        (standalone / "tests" / "__init__.py").write_text("")

        # Nested
        program = projects_dir / "beta_program"
        program.mkdir()
        nested = program / "gamma"
        (nested / "src").mkdir(parents=True)
        (nested / "tests").mkdir()
        (nested / "src" / "__init__.py").write_text("")
        (nested / "tests" / "__init__.py").write_text("")

        projects = discover_projects(tmp_path)

        alpha = next(p for p in projects if p.name == "alpha")
        gamma = next(p for p in projects if p.name == "gamma")

        assert alpha.qualified_name == "alpha"
        assert gamma.qualified_name == "beta_program/gamma"

    def test_nested_projects_sorted_alphabetically(self, tmp_path: Path):
        """Test nested projects are sorted alphabetically within their program."""
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()

        program_dir = projects_dir / "my_program"
        program_dir.mkdir()

        # Create projects in non-alphabetical order
        for name in ["zebra", "alpha", "beta"]:
            proj = program_dir / name
            (proj / "src").mkdir(parents=True)
            (proj / "tests").mkdir()
            (proj / "src" / "__init__.py").write_text("")
            (proj / "tests" / "__init__.py").write_text("")

        projects = discover_projects(tmp_path)
        project_names = [p.name for p in projects]

        assert project_names == ["alpha", "beta", "zebra"]

    def test_nested_projects_have_correct_metadata(self, tmp_path: Path):
        """Test nested projects extract metadata correctly."""
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()

        program_dir = projects_dir / "my_program"
        program_dir.mkdir()

        nested = program_dir / "nested_meta"
        (nested / "src").mkdir(parents=True)
        (nested / "tests").mkdir()
        (nested / "manuscript").mkdir()
        (nested / "scripts").mkdir()
        (nested / "src" / "__init__.py").write_text("")
        (nested / "tests" / "__init__.py").write_text("")

        pyproject_content = """\
[project]
name = "nested-meta"
version = "1.2.3"
description = "A nested project with metadata"
"""
        (nested / "pyproject.toml").write_text(pyproject_content)

        projects = discover_projects(tmp_path)

        assert len(projects) == 1
        proj = projects[0]
        assert proj.name == "nested_meta"
        assert proj.program == "my_program"
        assert proj.has_manuscript is True
        assert proj.has_scripts is True
        assert proj.metadata["version"] == "1.2.3"
        assert proj.metadata["description"] == "A nested project with metadata"

# =============================================================================
# TestGetDefaultProject - Tests for get_default_project()
# =============================================================================


class TestGetDefaultProject:
    """Test default project retrieval."""

    def test_get_default_project_when_exists(self, tmp_path: Path):
        """Test getting default project when it exists."""
        # Create projects/project (the default project)
        default = tmp_path / "projects" / "project"
        (default / "src").mkdir(parents=True)
        (default / "tests").mkdir()
        (default / "src" / "__init__.py").write_text("")
        (default / "tests" / "__init__.py").write_text("")

        result = get_default_project(tmp_path)

        assert result is not None
        assert result.name == "project"
        assert result.path == default
        assert result.is_valid is True

    def test_get_default_project_when_not_exists(self, tmp_path: Path):
        """Test getting default project returns None when it doesn't exist."""
        # Create projects directory but no 'project' subdirectory
        (tmp_path / "projects").mkdir()

        result = get_default_project(tmp_path)

        assert result is None

    def test_get_default_project_when_invalid(self, tmp_path: Path):
        """Test getting default project returns None when project is invalid."""
        # Create projects/project but missing tests directory
        default = tmp_path / "projects" / "project"
        (default / "src").mkdir(parents=True)
        (default / "src" / "__init__.py").write_text("")
        # No tests directory - invalid

        result = get_default_project(tmp_path)

        assert result is None

    def test_get_default_project_with_metadata(self, tmp_path: Path):
        """Test default project includes metadata."""
        default = tmp_path / "projects" / "project"
        (default / "src").mkdir(parents=True)
        (default / "tests").mkdir()
        (default / "src" / "__init__.py").write_text("")
        (default / "tests" / "__init__.py").write_text("")

        # Add pyproject.toml
        pyproject_content = """\
[project]
name = "default-project"
version = "3.0.0"
description = "The default project"
"""
        (default / "pyproject.toml").write_text(pyproject_content)

        result = get_default_project(tmp_path)

        assert result is not None
        assert result.metadata["name"] == "default-project"
        assert result.metadata["version"] == "3.0.0"
        assert result.metadata["description"] == "The default project"

    def test_get_default_project_no_projects_directory(self, tmp_path: Path):
        """Test default project returns None when projects directory doesn't exist."""
        # tmp_path exists but has no projects/ subdirectory
        result = get_default_project(tmp_path)

        assert result is None


# =============================================================================
# TestIntegrationScenarios - End-to-end integration tests
# =============================================================================


class TestIntegrationScenarios:
    """Integration tests covering realistic usage scenarios."""

    def test_full_project_discovery_workflow(self, tmp_path: Path):
        """Test complete discovery workflow with mixed valid/invalid projects."""
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()

        # Valid project with full metadata
        valid_full = projects_dir / "research_project"
        (valid_full / "src").mkdir(parents=True)
        (valid_full / "tests").mkdir()
        (valid_full / "manuscript").mkdir()
        (valid_full / "scripts").mkdir()
        (valid_full / "src" / "__init__.py").write_text("")
        (valid_full / "tests" / "__init__.py").write_text("")

        pyproject = """\
[project]
name = "research-project"
version = "1.0.0"
description = "Full research project"
authors = [{name = "Researcher"}]
"""
        (valid_full / "pyproject.toml").write_text(pyproject)

        config = """\
paper:
  title: "Research Paper"
authors:
  - name: "Dr. Researcher"
"""
        (valid_full / "manuscript" / "config.yaml").write_text(config)

        # Valid minimal project
        valid_minimal = projects_dir / "minimal_project"
        (valid_minimal / "src").mkdir(parents=True)
        (valid_minimal / "tests").mkdir()
        (valid_minimal / "src" / "code.py").write_text("# minimal code")
        (valid_minimal / "tests" / "__init__.py").write_text("")

        # Invalid project (empty src)
        invalid = projects_dir / "invalid_project"
        (invalid / "src").mkdir(parents=True)
        (invalid / "tests").mkdir()
        (invalid / "tests" / "__init__.py").write_text("")
        # src is empty - no Python files

        # Hidden project (should be skipped)
        hidden = projects_dir / ".hidden"
        (hidden / "src").mkdir(parents=True)
        (hidden / "tests").mkdir()
        (hidden / "src" / "__init__.py").write_text("")
        (hidden / "tests" / "__init__.py").write_text("")

        # Discover projects
        projects = discover_projects(tmp_path)

        # Should only find 2 valid projects
        assert len(projects) == 2

        # Verify details
        by_name = {p.name: p for p in projects}

        research = by_name["research_project"]
        assert research.has_manuscript is True
        assert research.has_scripts is True
        assert research.metadata["title"] == "Research Paper"
        assert "Dr. Researcher" in research.metadata["authors"]

        minimal = by_name["minimal_project"]
        assert minimal.has_manuscript is False
        assert minimal.has_scripts is False
        assert minimal.metadata["name"] == "minimal_project"

    def test_discover_projects_matches_real_repo_pattern(self, tmp_path: Path):
        """Test discovery matches the pattern used in the real repository."""
        # Simulate the actual repository structure
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()

        # Simulate code_project structure (the primary active project)
        code_project = projects_dir / "code_project"
        (code_project / "src").mkdir(parents=True)
        (code_project / "tests").mkdir()
        (code_project / "scripts").mkdir()
        (code_project / "manuscript").mkdir()
        (code_project / "output").mkdir()
        (code_project / "src" / "__init__.py").write_text("")
        (code_project / "src" / "optimizer.py").write_text("# optimizer code")
        (code_project / "tests" / "__init__.py").write_text("")
        (code_project / "tests" / "test_optimizer.py").write_text("# optimizer tests")

        # Simulate a second active project
        second_project = projects_dir / "second_project"
        (second_project / "src").mkdir(parents=True)
        (second_project / "tests").mkdir()
        (second_project / "scripts").mkdir()
        (second_project / "manuscript").mkdir()
        (second_project / "src" / "__init__.py").write_text("")
        (second_project / "tests" / "__init__.py").write_text("")

        # Simulate projects_archive (should not be discovered)
        archive = tmp_path / "projects_archive"
        (archive / "old_project" / "src").mkdir(parents=True)
        (archive / "old_project" / "tests").mkdir()
        (archive / "old_project" / "src" / "__init__.py").write_text("")
        (archive / "old_project" / "tests" / "__init__.py").write_text("")

        # Discover
        projects = discover_projects(tmp_path)

        assert len(projects) == 2
        names = [p.name for p in projects]
        assert "code_project" in names
        assert "second_project" in names
        assert "old_project" not in names


# =============================================================================
# TestEdgeCases - Edge cases and boundary conditions
# =============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_project_name_with_special_characters(self, tmp_path: Path):
        """Test project with hyphen and underscore in name."""
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()

        project = projects_dir / "my-test_project"
        (project / "src").mkdir(parents=True)
        (project / "tests").mkdir()
        (project / "src" / "__init__.py").write_text("")
        (project / "tests" / "__init__.py").write_text("")

        projects = discover_projects(tmp_path)

        assert len(projects) == 1
        assert projects[0].name == "my-test_project"

    def test_deeply_nested_python_files(self, tmp_path: Path):
        """Test project with deeply nested Python files."""
        project = tmp_path / "projects" / "deep_nested"
        (project / "src" / "a" / "b" / "c").mkdir(parents=True)
        (project / "tests").mkdir()
        (project / "src" / "a" / "b" / "c" / "deep.py").write_text("# deep")
        (project / "tests" / "__init__.py").write_text("")

        is_valid, _ = validate_project_structure(project)

        assert is_valid is True

    def test_pyproject_with_empty_authors(self, tmp_path: Path):
        """Test pyproject.toml with empty authors list."""
        project_dir = tmp_path / "empty_authors"
        project_dir.mkdir()

        pyproject = """\
[project]
name = "empty-authors"
version = "1.0.0"
authors = []
"""
        (project_dir / "pyproject.toml").write_text(pyproject)

        metadata = get_project_metadata(project_dir)

        assert metadata["authors"] == []

    def test_config_yaml_with_empty_authors(self, tmp_path: Path):
        """Test config.yaml with empty authors list."""
        project_dir = tmp_path / "empty_yaml_authors"
        (project_dir / "manuscript").mkdir(parents=True)

        config = """\
paper:
  title: "No Authors Paper"
authors: []
"""
        (project_dir / "manuscript" / "config.yaml").write_text(config)

        metadata = get_project_metadata(project_dir)

        assert metadata["authors"] == []
        assert metadata["title"] == "No Authors Paper"

    def test_symlink_in_projects_directory(self, tmp_path: Path):
        """Test handling of symlinks in projects directory."""
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()

        # Create a real project
        real = projects_dir / "real_project"
        (real / "src").mkdir(parents=True)
        (real / "tests").mkdir()
        (real / "src" / "__init__.py").write_text("")
        (real / "tests" / "__init__.py").write_text("")

        # Create symlink to another directory
        target = tmp_path / "external"
        (target / "src").mkdir(parents=True)
        (target / "tests").mkdir()
        (target / "src" / "__init__.py").write_text("")
        (target / "tests" / "__init__.py").write_text("")

        symlink = projects_dir / "linked_project"
        symlink.symlink_to(target)

        projects = discover_projects(tmp_path)

        # Both should be discovered since symlink is a valid directory
        assert len(projects) == 2
        names = [p.name for p in projects]
        assert "real_project" in names
        assert "linked_project" in names

    def test_binary_file_in_src(self, tmp_path: Path):
        """Test project with binary file alongside Python file in src."""
        project = tmp_path / "projects" / "binary_project"
        (project / "src").mkdir(parents=True)
        (project / "tests").mkdir()
        (project / "src" / "__init__.py").write_text("")
        (project / "src" / "model.pkl").write_bytes(b"\x80\x04\x95\x00")  # binary data
        (project / "tests" / "__init__.py").write_text("")

        is_valid, message = validate_project_structure(project)

        assert is_valid is True
        assert message == "Valid project structure"

    def test_unicode_in_metadata(self, tmp_path: Path):
        """Test metadata with unicode characters."""
        project_dir = tmp_path / "unicode_project"
        (project_dir / "manuscript").mkdir(parents=True)

        config = """\
paper:
  title: "Recherche en Intelligence Artificielle"
authors:
  - name: "Jean-Pierre Lefevre"
  - name: "Maria Garcia"
  - name: "Chen Wei"
"""
        (project_dir / "manuscript" / "config.yaml").write_text(config, encoding="utf-8")

        metadata = get_project_metadata(project_dir)

        assert metadata["title"] == "Recherche en Intelligence Artificielle"
        assert "Jean-Pierre Lefevre" in metadata["authors"]
        assert "Maria Garcia" in metadata["authors"]
        assert "Chen Wei" in metadata["authors"]
