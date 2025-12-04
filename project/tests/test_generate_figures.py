"""Tests for generate_figures.py script.

Tests the figure generation script that creates publication-quality
visualizations for the ways analysis manuscript.
"""

import pytest
from pathlib import Path
import tempfile
import shutil

# Add project src and scripts to path
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "scripts"))
sys.path.insert(0, str(project_root.parent))

from generate_figures import (
    generate_ways_network_figure,
    generate_room_hierarchy_figure,
    generate_type_distribution_figure,
    generate_type_room_heatmap,
    generate_partner_wordcloud,
    generate_framework_treemap,
    generate_example_length_violin
)


class TestFigureGeneration:
    """Test suite for figure generation functions."""

    def test_generate_ways_network_figure(self):
        """Test ways network figure generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_network.png"
            generate_ways_network_figure(output_path)
            
            assert output_path.exists()
            assert output_path.stat().st_size > 1000  # Should be substantial file

    def test_generate_room_hierarchy_figure(self):
        """Test room hierarchy figure generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_hierarchy.png"
            generate_room_hierarchy_figure(output_path)
            
            assert output_path.exists()
            assert output_path.stat().st_size > 1000

    def test_generate_type_distribution_figure(self):
        """Test type distribution figure generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_type_dist.png"
            generate_type_distribution_figure(output_path)
            
            assert output_path.exists()
            assert output_path.stat().st_size > 1000

    def test_generate_type_room_heatmap(self):
        """Test type × room heatmap generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_heatmap.png"
            generate_type_room_heatmap(output_path)
            
            assert output_path.exists()
            assert output_path.stat().st_size > 1000

    def test_generate_partner_wordcloud(self):
        """Test partner word cloud generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_wordcloud.png"
            generate_partner_wordcloud(output_path)
            
            assert output_path.exists()
            assert output_path.stat().st_size > 1000

    def test_generate_framework_treemap(self):
        """Test framework treemap generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_treemap.png"
            generate_framework_treemap(output_path)
            
            assert output_path.exists()
            assert output_path.stat().st_size > 1000

    def test_generate_example_length_violin(self):
        """Test example length violin plot generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_violin.png"
            generate_example_length_violin(output_path)
            
            assert output_path.exists()
            assert output_path.stat().st_size > 1000

    def test_all_figures_generate(self):
        """Test that all figures can be generated in sequence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            figures = [
                ("network.png", generate_ways_network_figure),
                ("hierarchy.png", generate_room_hierarchy_figure),
                ("type_dist.png", generate_type_distribution_figure),
                ("heatmap.png", generate_type_room_heatmap),
                ("wordcloud.png", generate_partner_wordcloud),
                ("treemap.png", generate_framework_treemap),
                ("violin.png", generate_example_length_violin),
            ]
            
            for filename, func in figures:
                output_path = Path(tmpdir) / filename
                func(output_path)
                assert output_path.exists(), f"Failed to generate {filename}"
                assert output_path.stat().st_size > 1000, f"{filename} is too small"
