"""Tests for utils/figure_manager.py module.

Comprehensive tests for the FigureManager class and FigureMetadata dataclass,
ensuring all figure registration and management functionality is tested.
"""

import json
import tempfile
from pathlib import Path

import pytest
from src.utils.figure_manager import FigureManager, FigureMetadata


class TestFigureMetadata:
    """Test FigureMetadata dataclass functionality."""

    def test_initialization_minimal(self):
        """Test FigureMetadata initialization with minimal fields."""
        metadata = FigureMetadata(filename="test.png", caption="Test figure")

        assert metadata.filename == "test.png"
        assert metadata.caption == "Test figure"
        assert metadata.label is None
        assert metadata.section is None
        assert metadata.generated_by is None
        assert metadata.parameters is None

    def test_initialization_complete(self):
        """Test FigureMetadata initialization with all fields."""
        metadata = FigureMetadata(
            filename="test.png",
            caption="Test figure",
            label="fig:test",
            section="Section 1",
            generated_by="test_script.py",
            parameters={"width": 0.8, "height": 0.6},
        )

        assert metadata.filename == "test.png"
        assert metadata.caption == "Test figure"
        assert metadata.label == "fig:test"
        assert metadata.section == "Section 1"
        assert metadata.generated_by == "test_script.py"
        assert metadata.parameters == {"width": 0.8, "height": 0.6}

    def test_to_dict(self):
        """Test FigureMetadata.to_dict() method."""
        metadata = FigureMetadata(
            filename="test.png",
            caption="Test figure",
            label="fig:test",
            section="Section 1",
            generated_by="test_script.py",
            parameters={"width": 0.8},
        )

        result = metadata.to_dict()

        assert isinstance(result, dict)
        assert result["filename"] == "test.png"
        assert result["caption"] == "Test figure"
        assert result["label"] == "fig:test"
        assert result["section"] == "Section 1"
        assert result["generated_by"] == "test_script.py"
        assert result["parameters"] == {"width": 0.8}


class TestFigureManager:
    """Test FigureManager class functionality."""

    @pytest.fixture
    def temp_registry_file(self, tmp_path):
        """Create temporary registry file path."""
        return tmp_path / "figure_registry.json"

    def test_initialization_default(self, tmp_path):
        """Test FigureManager initialization with default registry file."""
        registry_path = tmp_path / "figure_registry.json"
        manager = FigureManager(registry_file=registry_path)

        assert manager.registry_file == registry_path
        assert isinstance(manager.figures, dict)
        assert len(manager.figures) == 0

    def test_initialization_custom_registry(self, temp_registry_file):
        """Test FigureManager initialization with custom registry file."""
        manager = FigureManager(registry_file=str(temp_registry_file))

        assert manager.registry_file == temp_registry_file
        assert isinstance(manager.figures, dict)

    def test_register_figure_without_label(self, temp_registry_file):
        """Test figure registration without explicit label (auto-generated)."""
        manager = FigureManager(registry_file=str(temp_registry_file))

        metadata = manager.register_figure(
            filename="test_figure.png", caption="A test figure"
        )

        assert metadata.label == "fig:test_figure"
        assert metadata.filename == "test_figure.png"
        assert metadata.caption == "A test figure"
        assert "fig:test_figure" in manager.figures

    def test_register_figure_with_label(self, temp_registry_file):
        """Test figure registration with explicit label."""
        manager = FigureManager(registry_file=str(temp_registry_file))

        metadata = manager.register_figure(
            filename="test.png", caption="Test", label="fig:custom_label"
        )

        assert metadata.label == "fig:custom_label"
        assert "fig:custom_label" in manager.figures

    def test_register_figure_with_section(self, temp_registry_file):
        """Test figure registration with section information."""
        manager = FigureManager(registry_file=str(temp_registry_file))

        metadata = manager.register_figure(
            filename="test.png", caption="Test", section="03_methodology"
        )

        assert metadata.section == "03_methodology"

    def test_register_figure_with_generated_by(self, temp_registry_file):
        """Test figure registration with generated_by information."""
        manager = FigureManager(registry_file=str(temp_registry_file))

        metadata = manager.register_figure(
            filename="test.png", caption="Test", generated_by="generate_figures.py"
        )

        assert metadata.generated_by == "generate_figures.py"

    def test_register_figure_with_parameters(self, temp_registry_file):
        """Test figure registration with additional parameters."""
        manager = FigureManager(registry_file=str(temp_registry_file))

        metadata = manager.register_figure(
            filename="test.png", caption="Test", width=0.8, height=0.6, dpi=300
        )

        assert metadata.parameters == {"width": 0.8, "height": 0.6, "dpi": 300}

    def test_register_multiple_figures(self, temp_registry_file):
        """Test registering multiple figures."""
        manager = FigureManager(registry_file=str(temp_registry_file))

        metadata1 = manager.register_figure("fig1.png", "Figure 1", label="fig:one")
        metadata2 = manager.register_figure("fig2.png", "Figure 2", label="fig:two")
        metadata3 = manager.register_figure("fig3.png", "Figure 3", label="fig:three")

        assert len(manager.figures) == 3
        assert "fig:one" in manager.figures
        assert "fig:two" in manager.figures
        assert "fig:three" in manager.figures

    def test_register_figure_label_collision(self, temp_registry_file):
        """Test that registering with same label overwrites previous."""
        manager = FigureManager(registry_file=str(temp_registry_file))

        metadata1 = manager.register_figure("fig1.png", "Figure 1", label="fig:same")
        metadata2 = manager.register_figure("fig2.png", "Figure 2", label="fig:same")

        assert len(manager.figures) == 1
        assert manager.figures["fig:same"].filename == "fig2.png"
        assert manager.figures["fig:same"].caption == "Figure 2"

    def test_load_registry_existing(self, temp_registry_file):
        """Test loading existing registry file."""
        # Create registry file with data
        registry_data = {
            "fig:test1": {
                "filename": "test1.png",
                "caption": "Test 1",
                "label": "fig:test1",
                "section": None,
                "generated_by": None,
                "parameters": None,
            },
            "fig:test2": {
                "filename": "test2.png",
                "caption": "Test 2",
                "label": "fig:test2",
                "section": "Section 1",
                "generated_by": "script.py",
                "parameters": {"width": 0.8},
            },
        }

        temp_registry_file.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_registry_file, "w") as f:
            json.dump(registry_data, f, indent=2)

        manager = FigureManager(registry_file=str(temp_registry_file))

        assert len(manager.figures) == 2
        assert "fig:test1" in manager.figures
        assert "fig:test2" in manager.figures
        assert manager.figures["fig:test1"].filename == "test1.png"
        assert manager.figures["fig:test2"].section == "Section 1"

    def test_load_registry_nonexistent(self, temp_registry_file):
        """Test loading non-existent registry file (starts fresh)."""
        manager = FigureManager(registry_file=str(temp_registry_file))

        assert len(manager.figures) == 0
        assert isinstance(manager.figures, dict)

    def test_load_registry_corrupted(self, temp_registry_file):
        """Test loading corrupted registry file (starts fresh)."""
        # Create corrupted JSON file
        temp_registry_file.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_registry_file, "w") as f:
            f.write("This is not valid JSON { invalid }")

        manager = FigureManager(registry_file=str(temp_registry_file))

        # Should start fresh instead of crashing
        assert len(manager.figures) == 0
        assert isinstance(manager.figures, dict)

    def test_save_registry(self, temp_registry_file):
        """Test saving registry to file."""
        manager = FigureManager(registry_file=str(temp_registry_file))

        # Register some figures
        manager.register_figure("fig1.png", "Figure 1", label="fig:one")
        manager.register_figure("fig2.png", "Figure 2", label="fig:two")

        # Verify file was created
        assert temp_registry_file.exists()

        # Load and verify
        with open(temp_registry_file, "r") as f:
            data = json.load(f)

        assert len(data) == 2
        assert "fig:one" in data
        assert "fig:two" in data
        assert data["fig:one"]["filename"] == "fig1.png"

    def test_save_registry_creates_directory(self, tmp_path):
        """Test that save_registry creates parent directories."""
        nested_file = tmp_path / "nested" / "deep" / "registry.json"
        manager = FigureManager(registry_file=str(nested_file))

        manager.register_figure("test.png", "Test")

        assert nested_file.exists()
        assert nested_file.parent.exists()

    def test_register_figure_auto_label_from_path(self, temp_registry_file):
        """Test auto-label generation from filename with path."""
        manager = FigureManager(registry_file=str(temp_registry_file))

        metadata = manager.register_figure(
            filename="output/figures/complex_figure_name.png", caption="Test"
        )

        assert metadata.label == "fig:complex_figure_name"

    def test_register_figure_auto_label_from_stem(self, temp_registry_file):
        """Test auto-label generation uses file stem (no extension)."""
        manager = FigureManager(registry_file=str(temp_registry_file))

        metadata1 = manager.register_figure("test.png", "Test")
        metadata2 = manager.register_figure("test.pdf", "Test")

        # Both should have same label (stem is same)
        assert metadata1.label == metadata2.label == "fig:test"

    def test_register_figure_empty_parameters(self, temp_registry_file):
        """Test figure registration with no additional parameters."""
        manager = FigureManager(registry_file=str(temp_registry_file))

        metadata = manager.register_figure(filename="test.png", caption="Test")

        assert metadata.parameters is None

    def test_figure_registry_persistence(self, temp_registry_file):
        """Test that registry persists across manager instances."""
        # First manager instance
        manager1 = FigureManager(registry_file=str(temp_registry_file))
        manager1.register_figure("fig1.png", "Figure 1", label="fig:one")
        manager1.register_figure("fig2.png", "Figure 2", label="fig:two")

        # Second manager instance (should load existing registry)
        manager2 = FigureManager(registry_file=str(temp_registry_file))

        assert len(manager2.figures) == 2
        assert "fig:one" in manager2.figures
        assert "fig:two" in manager2.figures

        # Register new figure
        manager2.register_figure("fig3.png", "Figure 3", label="fig:three")

        # Third manager instance (should have all three)
        manager3 = FigureManager(registry_file=str(temp_registry_file))

        assert len(manager3.figures) == 3
        assert "fig:one" in manager3.figures
        assert "fig:two" in manager3.figures
        assert "fig:three" in manager3.figures

    def test_register_figure_complex_parameters(self, temp_registry_file):
        """Test figure registration with complex parameter types."""
        manager = FigureManager(registry_file=str(temp_registry_file))

        metadata = manager.register_figure(
            filename="test.png",
            caption="Test",
            width=0.8,
            height=0.6,
            style="publication",
            dpi=300,
            format="png",
        )

        assert metadata.parameters is not None
        assert metadata.parameters["width"] == 0.8
        assert metadata.parameters["height"] == 0.6
        assert metadata.parameters["style"] == "publication"
        assert metadata.parameters["dpi"] == 300
        assert metadata.parameters["format"] == "png"
