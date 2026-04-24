"""Tests for infrastructure.validation.content.figure_validator module.

Comprehensive tests for figure validation functionality including
registry loading, reference detection, and validation reporting.
"""

import json


from infrastructure.validation.content.figure_validator import validate_figure_registry


class TestValidateFigureRegistry:
    """Test validate_figure_registry function."""

    def test_validate_all_references_registered(self, tmp_path):
        """Test validation when all references are registered."""
        # Create registry
        registry_path = tmp_path / "registry.json"
        registry = {
            "fig:example1": {"path": "figures/example1.png"},
            "fig:example2": {"path": "figures/example2.png"},
        }
        with open(registry_path, "w") as f:
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
        registry = {"fig:example1": {"path": "figures/example1.png"}}
        with open(registry_path, "w") as f:
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
        registry_path.write_text("{invalid json}")

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
        with open(registry_path, "w") as f:
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
            "fig:example2": {"path": "figures/example2.png"},
        }
        with open(registry_path, "w") as f:
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
            "fig:example2": {"path": "figures/example2.png"},
        }
        with open(registry_path, "w") as f:
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

    def test_validate_handles_file_read_errors(self, tmp_path):
        """Test that file read errors are handled gracefully."""
        import os

        # Create registry
        registry_path = tmp_path / "registry.json"
        registry = {"fig:example1": {"path": "figures/example1.png"}}
        with open(registry_path, "w") as f:
            json.dump(registry, f)

        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        test_file = manuscript_dir / "01_introduction.md"
        test_file.write_text("\\ref{fig:example1}")

        # Make the file truly unreadable at the OS level
        os.chmod(test_file, 0o000)
        try:
            success, issues = validate_figure_registry(registry_path, manuscript_dir)

            # Should still complete validation (warns but continues)
            assert isinstance(success, bool)
        finally:
            # Restore permissions so tmp_path cleanup can delete it
            os.chmod(test_file, 0o644)

    def test_validate_empty_manuscript_directory(self, tmp_path):
        """Test validation with empty manuscript directory."""
        registry_path = tmp_path / "registry.json"
        registry = {"fig:example1": {"path": "figures/example1.png"}}
        with open(registry_path, "w") as f:
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
        with open(registry_path, "w") as f:
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
        with open(registry_path, "w") as f:
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


class TestListShapeRegistry:
    """Test that the validator accepts the list-shape registry emitted by
    project scripts (each item carries a ``label`` field)."""

    def test_validate_list_shape_registry_all_registered(self, tmp_path):
        """List-shape registry where every reference resolves."""
        registry_path = tmp_path / "registry.json"
        registry = [
            {"filename": "a.png", "path": "figures/a.png", "label": "fig:a"},
            {"filename": "b.png", "path": "figures/b.png", "label": "fig:b"},
        ]
        registry_path.write_text(json.dumps(registry))

        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        (manuscript_dir / "01_intro.md").write_text(
            "See \\ref{fig:a} and \\label{fig:b}"
        )

        success, issues = validate_figure_registry(registry_path, manuscript_dir)

        assert success is True
        assert issues == []

    def test_validate_list_shape_registry_unregistered(self, tmp_path):
        """List-shape registry must still flag unregistered references."""
        registry_path = tmp_path / "registry.json"
        registry = [{"filename": "a.png", "label": "fig:a"}]
        registry_path.write_text(json.dumps(registry))

        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        (manuscript_dir / "01_intro.md").write_text(
            "\\ref{fig:a} \\ref{fig:missing}"
        )

        success, issues = validate_figure_registry(registry_path, manuscript_dir)

        assert success is False
        assert any("fig:missing" in issue for issue in issues)

    def test_validate_list_shape_registry_missing_label_field(self, tmp_path, caplog):
        """Items lacking ``label`` are skipped with a warning, not a crash."""
        registry_path = tmp_path / "registry.json"
        registry = [
            {"filename": "a.png", "label": "fig:a"},
            {"filename": "orphan.png"},  # no label
            {"filename": "b.png", "label": "fig:b"},
        ]
        registry_path.write_text(json.dumps(registry))

        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        (manuscript_dir / "01_intro.md").write_text("\\ref{fig:a} \\ref{fig:b}")

        with caplog.at_level("WARNING"):
            success, issues = validate_figure_registry(registry_path, manuscript_dir)

        assert success is True
        assert issues == []
        assert any("without a 'label' field" in rec.message for rec in caplog.records)

    def test_validate_invalid_top_level_type(self, tmp_path):
        """A JSON top-level scalar yields a clean load error, not a crash."""
        registry_path = tmp_path / "registry.json"
        registry_path.write_text("42")

        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        (manuscript_dir / "01_intro.md").write_text("\\ref{fig:a}")

        success, issues = validate_figure_registry(registry_path, manuscript_dir)

        assert success is False
        assert len(issues) == 1
        assert "unexpected top-level JSON type" in issues[0]
        assert "int" in issues[0]
