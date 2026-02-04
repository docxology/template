"""Comprehensive tests for src/figure_manager.py to ensure 100% coverage."""

import json
import tempfile
from pathlib import Path

import pytest

from infrastructure.documentation.figure_manager import (FigureManager,
                                                         FigureMetadata)


class TestFigureMetadata:
    """Test FigureMetadata dataclass."""

    def test_metadata_creation(self):
        """Test creating figure metadata."""
        meta = FigureMetadata(
            figure_id="figure_001",
            filename="test.png",
            caption="Test caption",
            label="fig:test",
        )
        assert meta.figure_id == "figure_001"
        assert meta.filename == "test.png"
        assert meta.caption == "Test caption"
        assert meta.label == "fig:test"

    def test_to_dict(self):
        """Test converting to dictionary."""
        meta = FigureMetadata(
            figure_id="figure_001",
            filename="test.png",
            caption="Test",
            label="fig:test",
        )
        data = meta.to_dict()
        assert data["figure_id"] == "figure_001"
        assert data["filename"] == "test.png"

    def test_from_dict(self):
        """Test creating from dictionary."""
        data = {
            "figure_id": "figure_001",
            "filename": "test.png",
            "caption": "Test",
            "label": "fig:test",
            "section": None,
            "width": "0.8\\textwidth",
            "placement": "h",
            "generated_by": None,
            "metadata": {},
        }
        meta = FigureMetadata.from_dict(data)
        assert meta.figure_id == "figure_001"
        assert meta.filename == "test.png"


class TestFigureManager:
    """Test FigureManager class."""

    def test_initialization(self, tmp_path):
        """Test manager initialization."""
        registry_file = tmp_path / "registry.json"
        manager = FigureManager(registry_file=str(registry_file))
        assert manager.registry_file == registry_file
        assert len(manager.figures) == 0

    def test_register_figure(self, tmp_path):
        """Test registering a figure."""
        manager = FigureManager(registry_file=str(tmp_path / "registry.json"))
        fig_meta = manager.register_figure(
            filename="test.png", caption="Test caption", label="fig:test"
        )
        assert fig_meta.label == "fig:test"
        assert fig_meta.figure_id.startswith("figure_")
        assert "fig:test" in manager.figures

    def test_register_figure_auto_label(self, tmp_path):
        """Test auto-generating label."""
        manager = FigureManager(registry_file=str(tmp_path / "registry.json"))
        fig_meta = manager.register_figure(
            filename="convergence_plot.png", caption="Convergence plot"
        )
        assert fig_meta.label == "fig:convergence_plot"

    def test_get_figure(self, tmp_path):
        """Test getting figure by label."""
        manager = FigureManager(registry_file=str(tmp_path / "registry.json"))
        fig_meta = manager.register_figure(
            filename="test.png", caption="Test", label="fig:test"
        )
        retrieved = manager.get_figure("fig:test")
        assert retrieved == fig_meta

    def test_get_all_figures(self, tmp_path):
        """Test getting all figures."""
        manager = FigureManager(registry_file=str(tmp_path / "registry.json"))
        manager.register_figure("test1.png", "Caption 1", label="fig:test1")
        manager.register_figure("test2.png", "Caption 2", label="fig:test2")
        all_figures = manager.get_all_figures()
        assert len(all_figures) == 2

    def test_generate_latex_figure_block(self, tmp_path):
        """Test generating LaTeX figure block."""
        manager = FigureManager(registry_file=str(tmp_path / "registry.json"))
        manager.register_figure(
            filename="test.png", caption="Test caption", label="fig:test"
        )
        latex = manager.generate_latex_figure_block("fig:test")
        assert "\\begin{figure}" in latex
        assert "\\includegraphics" in latex
        assert "\\caption{Test caption}" in latex
        assert "\\label{fig:test}" in latex

    def test_generate_reference(self, tmp_path):
        """Test generating reference."""
        manager = FigureManager(registry_file=str(tmp_path / "registry.json"))
        ref = manager.generate_reference("fig:test")
        assert ref == "\\ref{fig:test}"

    def test_generate_figure_list(self, tmp_path):
        """Test generating figure list."""
        manager = FigureManager(registry_file=str(tmp_path / "registry.json"))
        manager.register_figure("test.png", "Test caption", label="fig:test")
        figure_list = manager.generate_figure_list()
        assert "## Figure List" in figure_list
        assert "fig:test" in figure_list

    def test_save_and_load_registry(self, tmp_path):
        """Test saving and loading registry."""
        registry_file = tmp_path / "registry.json"
        manager1 = FigureManager(registry_file=str(registry_file))
        manager1.register_figure("test.png", "Test", label="fig:test")

        # Create new manager and load
        manager2 = FigureManager(registry_file=str(registry_file))
        assert "fig:test" in manager2.figures

    def test_initialization_default_registry(self, tmp_path, monkeypatch):
        """Test initialization with default registry file."""
        # Change to tmp_path to avoid creating output/ directory
        monkeypatch.chdir(tmp_path)
        manager = FigureManager(registry_file=None)
        assert manager.registry_file.name == "figure_registry.json"

    def test_load_registry_with_figures(self, tmp_path):
        """Test loading registry with existing figures."""
        registry_file = tmp_path / "registry.json"
        # Create registry with figures
        data = {
            "fig:test": {
                "figure_id": "figure_001",
                "filename": "test.png",
                "caption": "Test",
                "label": "fig:test",
                "section": None,
                "width": "0.8\\textwidth",
                "placement": "h",
                "generated_by": None,
                "metadata": {},
            }
        }
        with open(registry_file, "w") as f:
            json.dump(data, f)

        manager = FigureManager(registry_file=str(registry_file))
        assert "fig:test" in manager.figures
        assert manager.counter > 0

    def test_load_registry_empty_dict(self, tmp_path):
        """Test loading registry with empty dictionary."""
        registry_file = tmp_path / "registry.json"
        # Create empty registry
        with open(registry_file, "w") as f:
            json.dump({}, f)

        manager = FigureManager(registry_file=str(registry_file))
        # When registry is empty, self.figures is empty, so if self.figures: is False
        assert len(manager.figures) == 0
        assert manager.counter == 0

    def test_load_registry_corrupted(self, tmp_path):
        """Test loading corrupted registry."""
        registry_file = tmp_path / "registry.json"
        # Write invalid JSON
        with open(registry_file, "w") as f:
            f.write("invalid json{")

        manager = FigureManager(registry_file=str(registry_file))
        # Should start fresh
        assert len(manager.figures) == 0
        assert manager.counter == 0

    def test_generate_latex_figure_block_not_found(self, tmp_path):
        """Test generating LaTeX block for non-existent figure."""
        manager = FigureManager(registry_file=str(tmp_path / "registry.json"))
        latex = manager.generate_latex_figure_block("fig:nonexistent")
        assert "% Figure fig:nonexistent not found in registry" in latex

    def test_generate_figure_list_with_section(self, tmp_path):
        """Test generating figure list with section."""
        manager = FigureManager(registry_file=str(tmp_path / "registry.json"))
        manager.register_figure(
            "test.png", "Test caption", label="fig:test", section="Introduction"
        )
        figure_list = manager.generate_figure_list()
        assert "Section: Introduction" in figure_list

    def test_generate_table_of_figures(self, tmp_path):
        """Test generating table of figures."""
        manager = FigureManager(registry_file=str(tmp_path / "registry.json"))
        manager.register_figure("test1.png", "Caption 1", label="fig:test1")
        manager.register_figure("test2.png", "Caption 2", label="fig:test2")
        table = manager.generate_table_of_figures()
        assert "\\listoffigures" in table
        assert "\\begin{figure}" in table
        assert "fig:test1" in table
        assert "fig:test2" in table

    def test_register_figure_with_metadata(self, tmp_path):
        """Test registering figure with metadata."""
        manager = FigureManager(registry_file=str(tmp_path / "registry.json"))
        metadata = {"key": "value", "number": 42}
        fig_meta = manager.register_figure("test.png", "Test", metadata=metadata)
        assert fig_meta.metadata == metadata
