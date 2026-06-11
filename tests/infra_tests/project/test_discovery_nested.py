"""Nested and integration discovery scenarios for infrastructure.project.discovery."""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.project.discovery import discover_projects, get_default_project
from infrastructure.project.metadata import get_project_metadata
from infrastructure.project.validation import validate_project_structure

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

        # Create standalone project (like template_code_project)
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

        # Simulate template_code_project structure (the primary active project)
        template_code_project = projects_dir / "template_code_project"
        (template_code_project / "src").mkdir(parents=True)
        (template_code_project / "tests").mkdir()
        (template_code_project / "scripts").mkdir()
        (template_code_project / "manuscript").mkdir()
        (template_code_project / "output").mkdir()
        (template_code_project / "src" / "__init__.py").write_text("")
        (template_code_project / "src" / "optimizer.py").write_text("# optimizer code")
        (template_code_project / "tests" / "__init__.py").write_text("")
        (template_code_project / "tests" / "test_optimizer.py").write_text("# optimizer tests")

        # Simulate a second active project
        second_project = projects_dir / "second_project"
        (second_project / "src").mkdir(parents=True)
        (second_project / "tests").mkdir()
        (second_project / "scripts").mkdir()
        (second_project / "manuscript").mkdir()
        (second_project / "src" / "__init__.py").write_text("")
        (second_project / "tests" / "__init__.py").write_text("")

        # Simulate projects/archive/ subfolder (should not be discovered)
        archive = projects_dir / "archive"
        (archive / "old_project" / "src").mkdir(parents=True)
        (archive / "old_project" / "tests").mkdir()
        (archive / "old_project" / "src" / "__init__.py").write_text("")
        (archive / "old_project" / "tests" / "__init__.py").write_text("")

        # Discover
        projects = discover_projects(tmp_path)

        assert len(projects) == 2
        names = [p.name for p in projects]
        assert "template_code_project" in names
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
