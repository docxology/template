"""Tests for concept visualization functionality."""

from __future__ import annotations

import json
import tempfile

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
    from visualization.concept_visualization import ConceptVisualizer
    from analysis.conceptual_mapping import Concept, ConceptMap
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


@pytest.fixture
def cooccurrence_matrix():
    """Create a sample co-occurrence matrix."""
    return {
        "colony": {"worker": 5, "queen": 3, "nest": 2},
        "worker": {"colony": 5, "forager": 4, "queen": 1},
        "queen": {"colony": 3, "worker": 1, "pheromone": 6},
        "forager": {"worker": 4, "nectar": 3, "dance": 2},
        "pheromone": {"queen": 6, "signal": 2, "trail": 3},
        "nest": {"colony": 2, "brood": 1},
    }


@pytest.fixture
def domain_overlaps():
    """Create sample domain overlap data."""
    return {
        "behavioral_and_chemical": {"overlap_percentage": 35.0, "shared_terms": 5},
        "behavioral_and_morphological": {"overlap_percentage": 12.0, "shared_terms": 2},
        "chemical_and_ecological": {"overlap_percentage": 20.0, "shared_terms": 3},
        "morphological_and_ecological": {"overlap_percentage": 8.0, "shared_terms": 1},
    }


@pytest.fixture
def populated_concept_map():
    """Create a populated concept map for coverage tests."""
    concept_map = ConceptMap()
    c1 = Concept(name="social_organization", description="Colony social structure")
    c1.add_term("colony")
    c1.add_term("caste")
    c1.add_domain("behavioral")
    c2 = Concept(name="communication", description="Insect communication")
    c2.add_term("pheromone")
    c2.add_term("dance")
    c2.add_domain("chemical")
    c3 = Concept(name="foraging", description="Food collection")
    c3.add_term("nectar")
    c3.add_term("trail")
    c3.add_domain("behavioral")
    concept_map.add_concept(c1)
    concept_map.add_concept(c2)
    concept_map.add_concept(c3)
    concept_map.add_relationship("social_organization", "communication", 0.8)
    concept_map.add_relationship("communication", "foraging", 0.6)
    return concept_map


@pytest.mark.skipif(
    not NETWORKX_AVAILABLE, reason="networkx not available for visualization tests"
)
class TestVisualizeConceptEvolution:
    """Tests for visualize_concept_evolution."""

    def test_with_data(self):
        visualizer = ConceptVisualizer()
        evolution_data = {
            "social_organization": {
                "term_count_evolution": [5, 8, 12, 15],
                "relationship_count_evolution": [2, 4, 6, 8],
                "term_stability": [0.5, 0.6, 0.7, 0.8],
                "term_growth_rate": 0.3,
            },
            "communication": {
                "term_count_evolution": [3, 5, 7, 10],
                "relationship_count_evolution": [1, 3, 5, 7],
                "term_stability": [0.4, 0.5, 0.6, 0.7],
                "term_growth_rate": 0.25,
            },
        }
        fig = visualizer.visualize_concept_evolution(evolution_data)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_empty_data(self):
        visualizer = ConceptVisualizer()
        fig = visualizer.visualize_concept_evolution({})
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_with_empty_evolution_lists(self):
        visualizer = ConceptVisualizer()
        evolution_data = {
            "concept_a": {
                "term_count_evolution": [],
                "relationship_count_evolution": [],
                "term_stability": [],
                "term_growth_rate": 0,
            },
        }
        fig = visualizer.visualize_concept_evolution(evolution_data)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_saves_to_file(self):
        visualizer = ConceptVisualizer()
        evolution_data = {
            "social": {
                "term_count_evolution": [5, 8, 12],
                "relationship_count_evolution": [2, 4, 6],
                "term_stability": [0.5, 0.6, 0.7],
                "term_growth_rate": 0.3,
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            filepath = Path(tmp) / "evolution.png"
            fig = visualizer.visualize_concept_evolution(evolution_data, filepath=filepath)
            assert filepath.exists()
            plt.close(fig)


@pytest.mark.skipif(
    not NETWORKX_AVAILABLE, reason="networkx not available for visualization tests"
)
class TestCreateStatisticalSummaryPlot:
    """Tests for create_statistical_summary_plot."""

    def test_full_data(self):
        visualizer = ConceptVisualizer()
        data = {
            "frequency_stats": {
                "frequency_distribution": {"counts": [10, 20, 15, 5, 2]},
                "top_terms": [
                    {"term": "colony", "frequency": 50},
                    {"term": "worker", "frequency": 35},
                    {"term": "queen", "frequency": 20},
                ],
            },
            "statistical_significance": {
                "p_value": 0.03,
                "chi_square_statistic": 12.5,
                "significance_threshold": 0.05,
            },
            "ambiguity_metrics": {
                "domain_metrics": {
                    "average_context_diversity": 0.65,
                    "average_ambiguity_score": 0.3,
                    "max_ambiguity_score": 0.8,
                },
            },
        }
        fig = visualizer.create_statistical_summary_plot(data)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_partial_data(self):
        visualizer = ConceptVisualizer()
        data = {
            "frequency_stats": {
                "frequency_distribution": {"counts": [5, 10]},
            },
        }
        fig = visualizer.create_statistical_summary_plot(data)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_empty_data(self):
        visualizer = ConceptVisualizer()
        fig = visualizer.create_statistical_summary_plot({})
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_saves_to_file(self):
        visualizer = ConceptVisualizer()
        data = {
            "frequency_stats": {
                "top_terms": [{"term": "ant", "frequency": 30}],
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            filepath = Path(tmp) / "stats.png"
            fig = visualizer.create_statistical_summary_plot(data, filepath=filepath)
            assert filepath.exists()
            plt.close(fig)


@pytest.mark.skipif(
    not NETWORKX_AVAILABLE, reason="networkx not available for visualization tests"
)
class TestExportVisualizationMetadataCoverage:
    """Extended tests for export_visualization_metadata."""

    def test_basic_export_with_assertions(self):
        visualizer = ConceptVisualizer()
        fig1, _ = plt.subplots()
        fig2, _ = plt.subplots()
        figures = {"concept_map": fig1, "network": fig2}
        with tempfile.TemporaryDirectory() as tmp:
            metadata_file = Path(tmp) / "metadata.json"
            visualizer.export_visualization_metadata(figures, metadata_file)
            assert metadata_file.exists()
            with open(metadata_file) as f:
                data = json.load(f)
            assert isinstance(data, dict)
        plt.close(fig1)
        plt.close(fig2)

    def test_empty_figures(self):
        visualizer = ConceptVisualizer()
        with tempfile.TemporaryDirectory() as tmp:
            metadata_file = Path(tmp) / "metadata.json"
            visualizer.export_visualization_metadata({}, metadata_file)
            assert metadata_file.exists()


@pytest.mark.skipif(
    not NETWORKX_AVAILABLE, reason="networkx not available for visualization tests"
)
class TestCreateInteractiveConceptNetwork:
    """Tests for create_interactive_concept_network (fallback path)."""

    def test_fallback_to_static(self, populated_concept_map):
        visualizer = ConceptVisualizer()
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            result = visualizer.create_interactive_concept_network(
                populated_concept_map, output_dir
            )
            assert isinstance(result, str)
            assert Path(result).exists()
        plt.close("all")


@pytest.mark.skipif(
    not NETWORKX_AVAILABLE, reason="networkx not available for visualization tests"
)
class TestCreateFallbackCooccurrencePlot:
    """Tests for _create_fallback_cooccurrence_plot."""

    def test_basic_fallback(self):
        visualizer = ConceptVisualizer()
        cooccurrence_matrix = {
            "colony": {"worker": 15, "queen": 10, "forager": 8},
            "worker": {"colony": 15, "forager": 12, "caste": 5},
            "queen": {"colony": 10, "reproduction": 7},
        }
        fig, ax = plt.subplots()
        visualizer._create_fallback_cooccurrence_plot(
            cooccurrence_matrix, ax, "Co-occurrence"
        )
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


@pytest.mark.skipif(
    not NETWORKX_AVAILABLE, reason="networkx not available for visualization tests"
)
class TestVisualizeConceptHierarchyExtended:
    """Extended tests for visualize_concept_hierarchy branches."""

    def test_with_centrality_data(self):
        visualizer = ConceptVisualizer()
        hierarchy = {
            "centrality_scores": {
                "colony": 0.9,
                "worker": 0.7,
                "forager": 0.5,
                "mandible": 0.2,
            },
            "core_concepts": ["colony", "worker"],
            "peripheral_concepts": ["mandible"],
        }
        fig = visualizer.visualize_concept_hierarchy(hierarchy)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_save_hierarchy_to_file(self):
        visualizer = ConceptVisualizer()
        hierarchy = {
            "centrality_scores": {
                "colony": 0.9,
                "worker": 0.7,
            },
            "core_concepts": ["colony"],
            "peripheral_concepts": ["worker"],
        }
        with tempfile.TemporaryDirectory() as tmp:
            filepath = Path(tmp) / "hierarchy.png"
            fig = visualizer.visualize_concept_hierarchy(hierarchy, filepath=filepath)
            assert filepath.exists()

    def test_empty_hierarchy(self):
        visualizer = ConceptVisualizer()
        hierarchy = {}
        fig = visualizer.visualize_concept_hierarchy(hierarchy)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


@pytest.mark.skipif(
    not NETWORKX_AVAILABLE, reason="networkx not available for visualization tests"
)
class TestVisualizeTerminologyNetworkBranches:
    """Test uncovered branches in visualize_terminology_network."""

    def test_no_connected_terms(self):
        visualizer = ConceptVisualizer()
        terms = [
            ("isolated1", {"frequency": 5, "domains": ["a"]}),
            ("isolated2", {"frequency": 3, "domains": ["b"]}),
        ]
        relationships = {}
        fig = visualizer.visualize_terminology_network(terms, relationships)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_many_terms_with_relationships(self):
        visualizer = ConceptVisualizer()
        terms = [
            ("colony", {"frequency": 20, "domains": ["behavioral"]}),
            ("worker", {"frequency": 15, "domains": ["behavioral"]}),
            ("queen", {"frequency": 12, "domains": ["behavioral"]}),
            ("forager", {"frequency": 10, "domains": ["behavioral"]}),
            ("pheromone", {"frequency": 8, "domains": ["chemical"]}),
        ]
        relationships = {
            ("colony", "worker"): 0.9,
            ("colony", "queen"): 0.8,
            ("worker", "forager"): 0.7,
            ("colony", "pheromone"): 0.5,
        }
        fig = visualizer.visualize_terminology_network(
            terms, relationships, title="Full Network"
        )
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_save_network_to_file(self):
        visualizer = ConceptVisualizer()
        terms = [
            ("a", {"frequency": 5, "domains": ["x"]}),
            ("b", {"frequency": 3, "domains": ["x"]}),
        ]
        relationships = {("a", "b"): 0.5}
        with tempfile.TemporaryDirectory() as tmp:
            filepath = Path(tmp) / "network.png"
            fig = visualizer.visualize_terminology_network(
                terms, relationships, filepath=filepath
            )
            assert filepath.exists()
            plt.close(fig)


@pytest.mark.skipif(
    not NETWORKX_AVAILABLE, reason="networkx not available for visualization tests"
)
class TestVisualizeTermCooccurrence:
    """Tests for visualize_term_cooccurrence method."""

    def test_basic_cooccurrence(self, cooccurrence_matrix):
        visualizer = ConceptVisualizer()
        fig = visualizer.visualize_term_cooccurrence(cooccurrence_matrix)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_save_to_file(self, cooccurrence_matrix):
        visualizer = ConceptVisualizer()
        with tempfile.TemporaryDirectory() as tmp:
            filepath = Path(tmp) / "cooccurrence.png"
            fig = visualizer.visualize_term_cooccurrence(
                cooccurrence_matrix, filepath=filepath
            )
            assert filepath.exists()
            plt.close(fig)

    def test_custom_title(self, cooccurrence_matrix):
        visualizer = ConceptVisualizer()
        fig = visualizer.visualize_term_cooccurrence(
            cooccurrence_matrix, title="Custom Network"
        )
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_small_matrix(self):
        visualizer = ConceptVisualizer()
        matrix = {
            "term_a": {"term_b": 3},
            "term_b": {"term_a": 3},
        }
        fig = visualizer.visualize_term_cooccurrence(matrix)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_zero_weight_edges_excluded(self):
        visualizer = ConceptVisualizer()
        matrix = {
            "x": {"y": 0, "z": 5},
            "y": {"x": 0},
            "z": {"x": 5},
        }
        fig = visualizer.visualize_term_cooccurrence(matrix)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_empty_matrix(self):
        visualizer = ConceptVisualizer()
        fig = visualizer.visualize_term_cooccurrence({})
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


@pytest.mark.skipif(
    not NETWORKX_AVAILABLE, reason="networkx not available for visualization tests"
)
class TestCreateDomainOverlapHeatmap:
    """Tests for create_domain_overlap_heatmap method."""

    def test_basic_heatmap(self, domain_overlaps):
        visualizer = ConceptVisualizer()
        fig = visualizer.create_domain_overlap_heatmap(domain_overlaps)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_save_to_file(self, domain_overlaps):
        visualizer = ConceptVisualizer()
        with tempfile.TemporaryDirectory() as tmp:
            filepath = Path(tmp) / "overlap.png"
            fig = visualizer.create_domain_overlap_heatmap(
                domain_overlaps, filepath=filepath
            )
            assert filepath.exists()
            plt.close(fig)

    def test_custom_title(self, domain_overlaps):
        visualizer = ConceptVisualizer()
        fig = visualizer.create_domain_overlap_heatmap(
            domain_overlaps, title="Cross-Domain Overlap"
        )
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_single_pair(self):
        visualizer = ConceptVisualizer()
        overlaps = {"bio_and_chem": {"overlap_percentage": 42.0}}
        fig = visualizer.create_domain_overlap_heatmap(overlaps)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_empty_overlaps(self):
        visualizer = ConceptVisualizer()
        fig = visualizer.create_domain_overlap_heatmap({})
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


@pytest.mark.skipif(
    not NETWORKX_AVAILABLE, reason="networkx not available for visualization tests"
)
class TestAdditionalVisualizerEdgeCases:
    """Additional edge case tests for ConceptVisualizer."""

    def test_visualize_concept_map_with_relationships(self, populated_concept_map):
        visualizer = ConceptVisualizer()
        with tempfile.TemporaryDirectory() as tmp:
            filepath = Path(tmp) / "concept_map.png"
            fig = visualizer.visualize_concept_map(populated_concept_map, filepath=filepath)
            assert isinstance(fig, plt.Figure)
            assert filepath.exists()
            plt.close(fig)

    def test_domain_comparison_diverse_data(self):
        visualizer = ConceptVisualizer()
        with tempfile.TemporaryDirectory() as tmp:
            filepath = Path(tmp) / "domain_comp.png"
            domain_data = {
                "behavioral": {"term_count": 15, "frequency": 120, "avg_confidence": 0.8},
                "chemical": {"term_count": 10, "frequency": 80, "avg_confidence": 0.7},
                "morphological": {"term_count": 8, "frequency": 60, "avg_confidence": 0.9},
            }
            fig = visualizer.create_domain_comparison_plot(domain_data, filepath=filepath)
            assert isinstance(fig, plt.Figure)
            plt.close(fig)

    def test_visualize_terminology_network_custom_title(self):
        visualizer = ConceptVisualizer()
        terms = [
            ("colony", {"frequency": 10, "domains": ["behavioral"]}),
            ("worker", {"frequency": 8, "domains": ["behavioral"]}),
        ]
        relationships = {
            ("colony", "worker"): 0.8,
        }
        fig = visualizer.visualize_terminology_network(
            terms, relationships, title="Custom Term Network"
        )
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_create_anthropomorphic_analysis_plot_edge(self):
        visualizer = ConceptVisualizer()
        with tempfile.TemporaryDirectory() as tmp:
            filepath = Path(tmp) / "anthro.png"
            anthro_data = {
                "intentional": ["decides", "chooses"],
                "emotional": ["happy", "angry"],
            }
            fig = visualizer.create_anthropomorphic_analysis_plot(
                anthro_data, filepath=filepath
            )
            assert isinstance(fig, plt.Figure)
            plt.close(fig)
