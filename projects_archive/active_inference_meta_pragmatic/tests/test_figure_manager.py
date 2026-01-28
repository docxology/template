"""Tests for utils/figure_manager.py module.

Comprehensive tests for the FigureManager class and FigureMetadata,
ensuring all figure registration functionality works correctly.
"""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from src.utils.figure_manager import FigureManager, FigureMetadata


class TestFigureMetadata:
    """Test FigureMetadata dataclass functionality."""

    def test_initialization_minimal(self):
        """Test FigureMetadata initialization with minimal parameters."""
        metadata = FigureMetadata(filename="test.png", caption="Test figure")

        assert metadata.filename == "test.png"
        assert metadata.caption == "Test figure"
        assert metadata.label is None
        assert metadata.section is None
        assert metadata.generated_by is None
        assert metadata.parameters is None

    def test_initialization_complete(self):
        """Test FigureMetadata initialization with all parameters."""
        metadata = FigureMetadata(
            filename="test.png",
            caption="Test figure",
            label="fig:test",
            section="03_methodology",
            generated_by="test_script.py",
            parameters={"param1": "value1", "param2": 42},
        )

        assert metadata.filename == "test.png"
        assert metadata.caption == "Test figure"
        assert metadata.label == "fig:test"
        assert metadata.section == "03_methodology"
        assert metadata.generated_by == "test_script.py"
        assert metadata.parameters == {"param1": "value1", "param2": 42}

    def test_to_dict(self):
        """Test FigureMetadata to_dict method."""
        metadata = FigureMetadata(
            filename="test.png",
            caption="Test figure",
            label="fig:test",
            parameters={"param": "value"},
        )

        result = metadata.to_dict()

        assert isinstance(result, dict)
        assert result["filename"] == "test.png"
        assert result["caption"] == "Test figure"
        assert result["label"] == "fig:test"
        assert result["parameters"] == {"param": "value"}


class TestFigureManager:
    """Test FigureManager class functionality."""

    def test_initialization_default(self):
        """Test FigureManager initialization with default registry file."""
        with TemporaryDirectory() as tmpdir:
            manager = FigureManager()

            assert manager.registry_file == Path("output/figures/figure_registry.json")
            assert isinstance(manager.figures, dict)
            assert len(manager.figures) == 0

    def test_initialization_custom_registry(self):
        """Test FigureManager initialization with custom registry file."""
        with TemporaryDirectory() as tmpdir:
            registry_path = Path(tmpdir) / "custom_registry.json"
            manager = FigureManager(registry_file=str(registry_path))

            assert manager.registry_file == registry_path
            assert manager.registry_file.parent.exists()

    def test_register_figure_minimal(self):
        """Test figure registration with minimal parameters."""
        with TemporaryDirectory() as tmpdir:
            registry_path = Path(tmpdir) / "registry.json"
            manager = FigureManager(registry_file=str(registry_path))

            metadata = manager.register_figure(
                filename="test.png", caption="Test figure"
            )

            assert isinstance(metadata, FigureMetadata)
            assert metadata.filename == "test.png"
            assert metadata.caption == "Test figure"
            assert metadata.label == "fig:test"  # Auto-generated from filename
            assert "fig:test" in manager.figures

    def test_register_figure_with_label(self):
        """Test figure registration with explicit label."""
        with TemporaryDirectory() as tmpdir:
            registry_path = Path(tmpdir) / "registry.json"
            manager = FigureManager(registry_file=str(registry_path))

            metadata = manager.register_figure(
                filename="test.png", caption="Test figure", label="fig:custom_label"
            )

            assert metadata.label == "fig:custom_label"
            assert "fig:custom_label" in manager.figures
            assert "fig:test" not in manager.figures

    def test_register_figure_with_section(self):
        """Test figure registration with section information."""
        with TemporaryDirectory() as tmpdir:
            registry_path = Path(tmpdir) / "registry.json"
            manager = FigureManager(registry_file=str(registry_path))

            metadata = manager.register_figure(
                filename="test.png", caption="Test figure", section="03_methodology"
            )

            assert metadata.section == "03_methodology"

    def test_register_figure_with_generated_by(self):
        """Test figure registration with generated_by information."""
        with TemporaryDirectory() as tmpdir:
            registry_path = Path(tmpdir) / "registry.json"
            manager = FigureManager(registry_file=str(registry_path))

            metadata = manager.register_figure(
                filename="test.png",
                caption="Test figure",
                generated_by="test_script.py",
            )

            assert metadata.generated_by == "test_script.py"

    def test_register_figure_with_parameters(self):
        """Test figure registration with additional parameters."""
        with TemporaryDirectory() as tmpdir:
            registry_path = Path(tmpdir) / "registry.json"
            manager = FigureManager(registry_file=str(registry_path))

            metadata = manager.register_figure(
                filename="test.png", caption="Test figure", param1="value1", param2=42
            )

            assert metadata.parameters == {"param1": "value1", "param2": 42}

    def test_register_figure_auto_label_generation(self):
        """Test automatic label generation from filename."""
        with TemporaryDirectory() as tmpdir:
            registry_path = Path(tmpdir) / "registry.json"
            manager = FigureManager(registry_file=str(registry_path))

            # Test with simple filename
            metadata1 = manager.register_figure(filename="simple.png", caption="Simple")
            assert metadata1.label == "fig:simple"

            # Test with path
            metadata2 = manager.register_figure(
                filename="path/to/figure.png", caption="Path figure"
            )
            assert metadata2.label == "fig:figure"

            # Test with complex filename
            metadata3 = manager.register_figure(
                filename="complex_figure_name_v2.png", caption="Complex"
            )
            assert metadata3.label == "fig:complex_figure_name_v2"

    def test_register_multiple_figures(self):
        """Test registering multiple figures."""
        with TemporaryDirectory() as tmpdir:
            registry_path = Path(tmpdir) / "registry.json"
            manager = FigureManager(registry_file=str(registry_path))

            metadata1 = manager.register_figure(
                filename="figure1.png", caption="First figure"
            )
            metadata2 = manager.register_figure(
                filename="figure2.png", caption="Second figure"
            )
            metadata3 = manager.register_figure(
                filename="figure3.png", caption="Third figure"
            )

            assert len(manager.figures) == 3
            assert "fig:figure1" in manager.figures
            assert "fig:figure2" in manager.figures
            assert "fig:figure3" in manager.figures

    def test_registry_persistence(self):
        """Test that registry is saved and loaded correctly."""
        with TemporaryDirectory() as tmpdir:
            registry_path = Path(tmpdir) / "registry.json"

            # Create manager and register figure
            manager1 = FigureManager(registry_file=str(registry_path))
            manager1.register_figure(
                filename="test.png", caption="Test figure", label="fig:test"
            )

            # Create new manager and verify it loads the registry
            manager2 = FigureManager(registry_file=str(registry_path))

            assert len(manager2.figures) == 1
            assert "fig:test" in manager2.figures
            assert manager2.figures["fig:test"].filename == "test.png"
            assert manager2.figures["fig:test"].caption == "Test figure"

    def test_registry_load_corrupted_file(self):
        """Test that corrupted registry file is handled gracefully."""
        with TemporaryDirectory() as tmpdir:
            registry_path = Path(tmpdir) / "registry.json"

            # Write invalid JSON
            registry_path.write_text("invalid json content {")

            # Manager should start with empty registry
            manager = FigureManager(registry_file=str(registry_path))

            assert len(manager.figures) == 0

    def test_registry_load_missing_file(self):
        """Test that missing registry file is handled gracefully."""
        with TemporaryDirectory() as tmpdir:
            registry_path = Path(tmpdir) / "nonexistent" / "registry.json"

            # Manager should create directory and start with empty registry
            manager = FigureManager(registry_file=str(registry_path))

            assert len(manager.figures) == 0
            assert registry_path.parent.exists()

    def test_registry_save_format(self):
        """Test that registry is saved in correct JSON format."""
        with TemporaryDirectory() as tmpdir:
            registry_path = Path(tmpdir) / "registry.json"
            manager = FigureManager(registry_file=str(registry_path))

            manager.register_figure(
                filename="test.png",
                caption="Test figure",
                label="fig:test",
                param1="value1",
            )

            # Verify JSON file exists and is valid
            assert registry_path.exists()
            with open(registry_path, "r") as f:
                data = json.load(f)

            assert isinstance(data, dict)
            assert "fig:test" in data
            assert data["fig:test"]["filename"] == "test.png"
            assert data["fig:test"]["caption"] == "Test figure"
            assert data["fig:test"]["parameters"]["param1"] == "value1"

    def test_register_figure_overwrite(self):
        """Test that registering figure with same label overwrites previous."""
        with TemporaryDirectory() as tmpdir:
            registry_path = Path(tmpdir) / "registry.json"
            manager = FigureManager(registry_file=str(registry_path))

            metadata1 = manager.register_figure(
                filename="old.png", caption="Old caption", label="fig:same"
            )

            metadata2 = manager.register_figure(
                filename="new.png", caption="New caption", label="fig:same"
            )

            assert len(manager.figures) == 1
            assert manager.figures["fig:same"].filename == "new.png"
            assert manager.figures["fig:same"].caption == "New caption"

    def test_register_figure_empty_parameters(self):
        """Test that empty kwargs result in None parameters."""
        with TemporaryDirectory() as tmpdir:
            registry_path = Path(tmpdir) / "registry.json"
            manager = FigureManager(registry_file=str(registry_path))

            metadata = manager.register_figure(
                filename="test.png", caption="Test figure"
            )

            assert metadata.parameters is None
