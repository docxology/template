"""Tests for concept visualization functionality."""

from __future__ import annotations

import matplotlib
import numpy as np
import pytest

matplotlib.use("Agg")  # Use non-interactive backend for testing
from pathlib import Path

import matplotlib.pyplot as plt

# Check if networkx is available (required for concept visualization)
try:
    import networkx as nx

    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False

# Only import visualization classes if dependencies are available
if NETWORKX_AVAILABLE:
    try:
        from src.concept_visualization import ConceptVisualizer
        from src.analysis.conceptual_mapping import Concept, ConceptMap
    except ImportError:
        from src.visualization.concept_visualization import ConceptVisualizer
        from src.analysis.conceptual_mapping import Concept, ConceptMap
else:
    ConceptVisualizer = None
    ConceptMap = None
    Concept = None


@pytest.mark.skipif(
    not NETWORKX_AVAILABLE, reason="networkx not available for visualization tests"
)
class TestConceptVisualizer:
    """Test ConceptVisualizer functionality."""

    @pytest.fixture
    def visualizer(self) -> ConceptVisualizer:
        """Create a ConceptVisualizer instance."""
        return ConceptVisualizer()

    @pytest.fixture
    def sample_concept_map(self) -> ConceptMap:
        """Create a sample concept map for testing."""
        concept_map = ConceptMap()

        # Add some sample concepts
        concept1 = Concept(
            name="colony_organization",
            description="How ant colonies are organized",
            terms={"colony", "queen", "worker"},
            domains={"unit_of_individuality", "power_and_labor"},
        )
        concept1.confidence = 0.8

        concept2 = Concept(
            name="division_of_labor",
            description="Task specialization in colonies",
            terms={"worker", "forager", "nurse"},
            domains={"behavior_and_identity", "power_and_labor"},
        )
        concept2.confidence = 0.7

        concept_map.concepts["colony_organization"] = concept1
        concept_map.concepts["division_of_labor"] = concept2

        # Add relationships
        concept_map.add_relationship("colony_organization", "division_of_labor", 0.8)

        return concept_map

    def test_visualizer_initialization(self, visualizer: ConceptVisualizer) -> None:
        """Test visualizer initialization."""
        assert visualizer.figsize == (12, 8)
        assert visualizer.DOMAIN_COLORS is not None
        assert len(visualizer.DOMAIN_COLORS) == 6

    def test_domain_colors_complete(self, visualizer: ConceptVisualizer) -> None:
        """Test that all six domains have colors defined."""
        expected_domains = {
            "unit_of_individuality",
            "behavior_and_identity",
            "power_and_labor",
            "sex_and_reproduction",
            "kin_and_relatedness",
            "economics",
        }
        assert set(visualizer.DOMAIN_COLORS.keys()) == expected_domains

    def test_visualize_concept_map(
        self,
        visualizer: ConceptVisualizer,
        sample_concept_map: ConceptMap,
        tmp_path: Path,
    ) -> None:
        """Test concept map visualization."""
        filepath = tmp_path / "test_concept_map.png"

        fig = visualizer.visualize_concept_map(sample_concept_map, filepath)

        # Verify figure was created and saved
        assert isinstance(fig, plt.Figure)
        assert filepath.exists()
        assert filepath.stat().st_size > 0  # File has content

        plt.close(fig)

    def test_create_domain_comparison_plot(
        self, visualizer: ConceptVisualizer, tmp_path: Path
    ) -> None:
        """Test domain comparison plot creation."""
        domain_data = {
            "unit_of_individuality": {"terms": 50, "confidence": 0.8},
            "behavior_and_identity": {"terms": 75, "confidence": 0.7},
            "power_and_labor": {"terms": 60, "confidence": 0.9},
        }

        filepath = tmp_path / "domain_comparison.png"

        fig = visualizer.create_domain_comparison_plot(domain_data, filepath)

        # Verify figure was created and saved
        assert isinstance(fig, plt.Figure)
        assert filepath.exists()
        assert filepath.stat().st_size > 0  # File has content

        plt.close(fig)

    def test_visualize_terminology_network(
        self, visualizer: ConceptVisualizer, tmp_path: Path
    ) -> None:
        """Test terminology network visualization."""
        terms = [
            ("colony", {"domains": ["unit_of_individuality"], "frequency": 10}),
            ("queen", {"domains": ["power_and_labor"], "frequency": 8}),
            ("worker", {"domains": ["power_and_labor"], "frequency": 12}),
            ("forager", {"domains": ["behavior_and_identity"], "frequency": 6}),
            ("nurse", {"domains": ["behavior_and_identity"], "frequency": 5}),
        ]
        relationships = {
            ("colony", "queen"): 0.8,
            ("colony", "worker"): 0.9,
            ("worker", "forager"): 0.7,
        }

        filepath = tmp_path / "term_network.png"

        fig = visualizer.visualize_terminology_network(terms, relationships, filepath)

        # Verify figure was created and saved
        assert isinstance(fig, plt.Figure)
        assert filepath.exists()
        assert filepath.stat().st_size > 0  # File has content

        plt.close(fig)

    def test_get_concept_color(
        self, visualizer: ConceptVisualizer, sample_concept_map: ConceptMap
    ) -> None:
        """Test concept color retrieval."""
        color = visualizer._get_concept_color("colony_organization", sample_concept_map)
        # Should be one of the domain colors (power_and_labor is first in iteration)
        assert color in [
            "#1f77b4",
            "#2ca02c",
            "#7f7f7f",
        ]  # unit_of_individuality, power_and_labor, or default

        # Test unknown concept
        color = visualizer._get_concept_color("unknown_concept", sample_concept_map)
        assert color == "#7f7f7f"  # Default gray

    def test_figure_saving(self, visualizer: ConceptVisualizer, tmp_path: Path) -> None:
        """Test figure saving functionality."""
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 2])

        filepath = tmp_path / "test_figure.png"

        # Test basic saving
        fig.savefig(filepath)

        # Verify file was saved
        assert filepath.exists()
        assert filepath.stat().st_size > 0  # File has content

        plt.close(fig)

    def test_figure_size_configuration(self) -> None:
        """Test custom figure size configuration."""
        custom_size = (16, 12)
        visualizer = ConceptVisualizer(figsize=custom_size)

        assert visualizer.figsize == custom_size

    def test_multiple_figure_formats(self, tmp_path: Path) -> None:
        """Test saving figures in different formats."""
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 2, 3])

        for ext in [".png", ".pdf", ".svg"]:
            filepath = tmp_path / f"test_figure{ext}"

            fig.savefig(filepath)

            # Verify file was saved in each format
            assert filepath.exists()
            assert filepath.stat().st_size > 0  # File has content

        plt.close(fig)

    def test_empty_concept_map_handling(self) -> None:
        """Test handling of empty concept maps."""
        empty_map = ConceptMap()

        # Should not crash when creating empty map
        assert len(empty_map.concepts) == 0
        assert len(empty_map.concept_relationships) == 0

    def test_concept_map_with_no_relationships(self) -> None:
        """Test concept map with concepts but no relationships."""
        concept_map = ConceptMap()
        concept = Concept("test_concept", "Test concept", {"term1"}, {"domain1"})
        concept_map.concepts["test"] = concept

        assert len(concept_map.concepts) == 1
        assert len(concept_map.concept_relationships) == 0

    def test_visualize_concept_hierarchy(
        self, visualizer: ConceptVisualizer, tmp_path: Path
    ) -> None:
        """Test concept hierarchy visualization."""
        # Test with empty hierarchy (should not save file)
        hierarchy_data = {}
        filepath = tmp_path / "empty_hierarchy.png"
        fig = visualizer.visualize_concept_hierarchy(hierarchy_data, filepath)
        assert isinstance(fig, plt.Figure)
        # Empty data doesn't save the file
        plt.close(fig)

        # Test with hierarchy data
        hierarchy_data = {
            "centrality_scores": {
                "concept1": 0.8,
                "concept2": 0.6,
                "concept3": 0.4,
                "concept4": 0.2,
            },
            "core_concepts": ["concept1"],
            "peripheral_concepts": ["concept2", "concept3"],
        }
        filepath = tmp_path / "hierarchy.png"
        fig = visualizer.visualize_concept_hierarchy(hierarchy_data, filepath)
        assert isinstance(fig, plt.Figure)
        assert filepath.exists()
        plt.close(fig)

    def test_create_anthropomorphic_analysis_plot(
        self, visualizer: ConceptVisualizer, tmp_path: Path
    ) -> None:
        """Test anthropomorphic analysis plot creation."""
        anthropomorphic_data = {
            "sentences": [
                "The colony behaves intelligently",
                "Workers communicate effectively",
                "The queen makes decisions",
            ],
            "anthropomorphic_terms": ["behaves", "communicate", "decisions"],
        }

        filepath = tmp_path / "anthropomorphic.png"
        fig = visualizer.create_anthropomorphic_analysis_plot(
            anthropomorphic_data, filepath
        )
        assert isinstance(fig, plt.Figure)
        assert filepath.exists()
        plt.close(fig)

    def test_export_visualization_metadata(
        self, visualizer: ConceptVisualizer, tmp_path: Path
    ) -> None:
        """Test visualization metadata export."""
        # Create some test figures
        fig1, ax1 = plt.subplots()
        ax1.plot([1, 2, 3], [1, 2, 3])
        ax1.set_title("Test Figure 1")

        fig2, ax2 = plt.subplots()
        ax2.bar(["A", "B", "C"], [1, 2, 3])
        ax2.set_title("Test Figure 2")

        figures = {"figure1": fig1, "figure2": fig2}

        metadata_path = tmp_path / "visualization_metadata.json"
        visualizer.export_visualization_metadata(figures, metadata_path)

        assert metadata_path.exists()

        plt.close(fig1)
        plt.close(fig2)

    def test_add_domain_legend(self, visualizer: ConceptVisualizer) -> None:
        """Test domain legend addition."""
        fig, ax = plt.subplots()
        visualizer._add_domain_legend(ax)
        # Should not crash and add some legend elements
        assert ax.get_legend() is not None
        plt.close(fig)

    def test_get_term_color(self, visualizer: ConceptVisualizer) -> None:
        """Test term color retrieval."""
        # Create a mock graph with node attributes
        G = nx.Graph()
        G.add_node("term1", domains=["unit_of_individuality"])
        G.add_node("term2", domains=["power_and_labor"])
        G.add_node("term3", domains=["unknown_domain"])

        color1 = visualizer._get_term_color("term1", G)
        color2 = visualizer._get_term_color("term2", G)
        color3 = visualizer._get_term_color("term3", G)

        # Should return domain colors or default
        assert color1 in visualizer.DOMAIN_COLORS.values() or color1 == "#7f7f7f"
        assert color2 in visualizer.DOMAIN_COLORS.values() or color2 == "#7f7f7f"
        assert color3 == "#7f7f7f"  # Default for unknown domain
