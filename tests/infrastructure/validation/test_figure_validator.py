"""Tests for infrastructure.validation.figure_validator module.

Comprehensive tests for figure validation functionality including
registry loading, reference detection, and validation reporting.
"""

import json
from pathlib import Path
import pytest

from infrastructure.validation.figure_validator import validate_figure_registry


class TestValidateFigureRegistry:
    """Test validate_figure_registry function."""

    def test_validate_all_references_registered(self, tmp_path):
        """Test validation when all references are registered."""
        # Create registry
        registry_path = tmp_path / "registry.json"
        registry = {
            "fig:example1": {"path": "figures/example1.png"},
            "fig:example2": {"path": "figures/example2.png"}
        }
        with open(registry_path, 'w') as f:
            json.dump(registry, f)
        
        # Create manuscript with references
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        (manuscript_dir / "01_introduction.md").write_text(
            "See \\ref{fig:example1} and \\label{fig:example2}"
        )
        
        success, issues = validate_figure_registry(registry_path, manuscript_dir)
        
        assert success is True
        assert len(issues) == 0

    def test_validate_unregistered_references(self, tmp_path):
        """Test detection of unregistered figure references."""
        # Create registry with only one figure
        registry_path = tmp_path / "registry.json"
        registry = {
            "fig:example1": {"path": "figures/example1.png"}
        }
        with open(registry_path, 'w') as f:
            json.dump(registry, f)
        
        # Create manuscript with unregistered reference
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        (manuscript_dir / "01_introduction.md").write_text(
            "See \\ref{fig:example1} and \\ref{fig:unregistered}"
        )
        
        success, issues = validate_figure_registry(registry_path, manuscript_dir)
        
        assert success is False
        assert len(issues) > 0
        assert any("fig:unregistered" in issue for issue in issues)

    def test_validate_registry_not_found(self, tmp_path):
        """Test validation when registry doesn't exist."""
        registry_path = tmp_path / "nonexistent.json"
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        
        success, issues = validate_figure_registry(registry_path, manuscript_dir)
        
        # Should succeed if registry doesn't exist (not an error)
        assert success is True
        assert len(issues) == 0

    def test_validate_invalid_registry_json(self, tmp_path):
        """Test validation with invalid JSON registry."""
        registry_path = tmp_path / "registry.json"
        registry_path.write_text('{invalid json}')
        
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        
        success, issues = validate_figure_registry(registry_path, manuscript_dir)
        
        assert success is False
        assert len(issues) > 0
        assert any("Failed to load" in issue for issue in issues)

    def test_validate_skips_documentation_files(self, tmp_path):
        """Test that documentation files are skipped."""
        # Create registry
        registry_path = tmp_path / "registry.json"
        registry = {"fig:example1": {"path": "figures/example1.png"}}
        with open(registry_path, 'w') as f:
            json.dump(registry, f)
        
        # Create manuscript with documentation files
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        (manuscript_dir / "AGENTS.md").write_text("\\ref{fig:unregistered}")
        (manuscript_dir / "README.md").write_text("\\ref{fig:unregistered}")
        (manuscript_dir / "01_introduction.md").write_text("\\ref{fig:example1}")
        
        success, issues = validate_figure_registry(registry_path, manuscript_dir)
        
        # Should succeed because AGENTS.md and README.md are skipped
        assert success is True
        assert len(issues) == 0

    def test_validate_multiple_markdown_files(self, tmp_path):
        """Test validation across multiple markdown files."""
        # Create registry
        registry_path = tmp_path / "registry.json"
        registry = {
            "fig:example1": {"path": "figures/example1.png"},
            "fig:example2": {"path": "figures/example2.png"}
        }
        with open(registry_path, 'w') as f:
            json.dump(registry, f)
        
        # Create multiple manuscript files
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        (manuscript_dir / "01_introduction.md").write_text("\\ref{fig:example1}")
        (manuscript_dir / "02_methods.md").write_text("\\ref{fig:example2}")
        
        success, issues = validate_figure_registry(registry_path, manuscript_dir)
        
        assert success is True
        assert len(issues) == 0

    def test_validate_ref_and_label_patterns(self, tmp_path):
        """Test that both \\ref and \\label patterns are detected."""
        # Create registry
        registry_path = tmp_path / "registry.json"
        registry = {
            "fig:example1": {"path": "figures/example1.png"},
            "fig:example2": {"path": "figures/example2.png"}
        }
        with open(registry_path, 'w') as f:
            json.dump(registry, f)
        
        # Create manuscript with both patterns
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        (manuscript_dir / "01_introduction.md").write_text(
            "See \\ref{fig:example1} and \\label{fig:example2}"
        )
        
        success, issues = validate_figure_registry(registry_path, manuscript_dir)
        
        assert success is True
        assert len(issues) == 0

    def test_validate_handles_file_read_errors(self, tmp_path, monkeypatch):
        """Test that file read errors are handled gracefully."""
        # Create registry
        registry_path = tmp_path / "registry.json"
        registry = {"fig:example1": {"path": "figures/example1.png"}}
        with open(registry_path, 'w') as f:
            json.dump(registry, f)
        
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        test_file = manuscript_dir / "01_introduction.md"
        test_file.write_text("\\ref{fig:example1}")
        
        # Mock read_text to raise exception
        def mock_read_text(*args, **kwargs):
            raise PermissionError("Cannot read file")
        
        monkeypatch.setattr(Path, 'read_text', mock_read_text)
        
        success, issues = validate_figure_registry(registry_path, manuscript_dir)
        
        # Should still complete validation (warns but continues)
        assert isinstance(success, bool)

    def test_validate_empty_manuscript_directory(self, tmp_path):
        """Test validation with empty manuscript directory."""
        registry_path = tmp_path / "registry.json"
        registry = {"fig:example1": {"path": "figures/example1.png"}}
        with open(registry_path, 'w') as f:
            json.dump(registry, f)
        
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        
        success, issues = validate_figure_registry(registry_path, manuscript_dir)
        
        assert success is True
        assert len(issues) == 0

    def test_validate_nonexistent_manuscript_directory(self, tmp_path):
        """Test validation when manuscript directory doesn't exist."""
        registry_path = tmp_path / "registry.json"
        registry = {"fig:example1": {"path": "figures/example1.png"}}
        with open(registry_path, 'w') as f:
            json.dump(registry, f)
        
        manuscript_dir = tmp_path / "nonexistent"
        
        success, issues = validate_figure_registry(registry_path, manuscript_dir)
        
        assert success is True
        assert len(issues) == 0

    def test_validate_multiple_unregistered_references(self, tmp_path):
        """Test detection of multiple unregistered references."""
        # Create registry
        registry_path = tmp_path / "registry.json"
        registry = {"fig:example1": {"path": "figures/example1.png"}}
        with open(registry_path, 'w') as f:
            json.dump(registry, f)
        
        # Create manuscript with multiple unregistered references
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        (manuscript_dir / "01_introduction.md").write_text(
            "\\ref{fig:example1} \\ref{fig:unregistered1} \\ref{fig:unregistered2}"
        )
        
        success, issues = validate_figure_registry(registry_path, manuscript_dir)
        
        assert success is False
        assert len(issues) == 2
        assert any("fig:unregistered1" in issue for issue in issues)
        assert any("fig:unregistered2" in issue for issue in issues)



