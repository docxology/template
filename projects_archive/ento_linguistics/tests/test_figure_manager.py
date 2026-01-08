"""Tests for src/utils/figure_manager.py to improve coverage."""
import json
import tempfile
from pathlib import Path

import pytest

from src.utils.figure_manager import FigureManager, FigureMetadata


class TestFigureMetadata:
    """Test FigureMetadata dataclass."""
    
    def test_metadata_creation(self):
        """Test creating figure metadata."""
        metadata = FigureMetadata(
            filename="test.png",
            caption="Test figure",
            label="fig:test",
            section="Introduction"
        )
        assert metadata.filename == "test.png"
        assert metadata.caption == "Test figure"
        assert metadata.label == "fig:test"
        assert metadata.section == "Introduction"
    
    def test_metadata_to_dict(self):
        """Test converting metadata to dictionary."""
        metadata = FigureMetadata(
            filename="test.png",
            caption="Test",
            label="fig:test",
            parameters={"param1": "value1"}
        )
        data = metadata.to_dict()
        assert data["filename"] == "test.png"
        assert data["caption"] == "Test"
        assert data["label"] == "fig:test"
        assert data["parameters"] == {"param1": "value1"}


class TestFigureManager:
    """Test FigureManager class."""
    
    def test_manager_initialization_default(self, tmp_path):
        """Test initializing manager with default registry path structure."""
        # Use a temporary registry file to ensure isolation from existing data
        registry_file = tmp_path / "test_registry.json"
        manager = FigureManager(str(registry_file))
        assert manager.registry_file == registry_file
        assert len(manager.figures) == 0
    
    def test_manager_initialization_custom(self, tmp_path):
        """Test initializing manager with custom registry path."""
        registry_file = tmp_path / "custom_registry.json"
        manager = FigureManager(str(registry_file))
        assert manager.registry_file == registry_file
        assert len(manager.figures) == 0
    
    def test_register_figure_with_label(self, tmp_path):
        """Test registering a figure with explicit label."""
        registry_file = tmp_path / "registry.json"
        manager = FigureManager(str(registry_file))
        
        metadata = manager.register_figure(
            filename="test.png",
            caption="Test figure",
            label="fig:test",
            section="Introduction"
        )
        
        assert metadata.label == "fig:test"
        assert metadata.filename == "test.png"
        assert "fig:test" in manager.figures
    
    def test_register_figure_auto_label(self, tmp_path):
        """Test registering a figure with auto-generated label."""
        registry_file = tmp_path / "registry.json"
        manager = FigureManager(str(registry_file))
        
        metadata = manager.register_figure(
            filename="my_figure.png",
            caption="My figure"
        )
        
        assert metadata.label == "fig:my_figure"
        assert metadata.filename == "my_figure.png"
        assert "fig:my_figure" in manager.figures
    
    def test_register_figure_with_parameters(self, tmp_path):
        """Test registering a figure with additional parameters."""
        registry_file = tmp_path / "registry.json"
        manager = FigureManager(str(registry_file))
        
        metadata = manager.register_figure(
            filename="test.png",
            caption="Test",
            param1="value1",
            param2=42
        )
        
        assert metadata.parameters == {"param1": "value1", "param2": 42}
    
    def test_get_figure_existing(self, tmp_path):
        """Test getting an existing figure."""
        registry_file = tmp_path / "registry.json"
        manager = FigureManager(str(registry_file))
        
        manager.register_figure(
            filename="test.png",
            caption="Test",
            label="fig:test"
        )
        
        metadata = manager.get_figure("fig:test")
        assert metadata is not None
        assert metadata.filename == "test.png"
    
    def test_get_figure_nonexistent(self, tmp_path):
        """Test getting a non-existent figure."""
        registry_file = tmp_path / "registry.json"
        manager = FigureManager(str(registry_file))
        
        metadata = manager.get_figure("fig:nonexistent")
        assert metadata is None
    
    def test_load_registry_existing(self, tmp_path):
        """Test loading existing registry file."""
        registry_file = tmp_path / "registry.json"
        registry_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create registry file
        registry_data = {
            "fig:test": {
                "filename": "test.png",
                "caption": "Test figure",
                "label": "fig:test"
            }
        }
        registry_file.write_text(json.dumps(registry_data))
        
        manager = FigureManager(str(registry_file))
        assert "fig:test" in manager.figures
        assert manager.figures["fig:test"].filename == "test.png"
    
    def test_load_registry_corrupted(self, tmp_path):
        """Test loading corrupted registry file."""
        registry_file = tmp_path / "registry.json"
        registry_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create corrupted registry file
        registry_file.write_text("invalid json content {")
        
        manager = FigureManager(str(registry_file))
        # Should start fresh with empty registry
        assert len(manager.figures) == 0
    
    def test_save_registry(self, tmp_path):
        """Test saving registry to file."""
        registry_file = tmp_path / "registry.json"
        manager = FigureManager(str(registry_file))
        
        manager.register_figure(
            filename="test.png",
            caption="Test",
            label="fig:test"
        )
        
        # Verify file was created and contains data
        assert registry_file.exists()
        data = json.loads(registry_file.read_text())
        assert "fig:test" in data
        assert data["fig:test"]["filename"] == "test.png"
