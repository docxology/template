from __future__ import annotations
from pathlib import Path
import networkx as nx
from visualization.citation_plots import plot_citation_network, plot_degree_distribution


def _make_small_graph() -> nx.DiGraph:
    """Create a small citation graph for testing."""
    g = nx.DiGraph()
    g.add_node("paper_a", title="Paper A", year=2020, citation_count=10)
    g.add_node("paper_b", title="Paper B", year=2021, citation_count=5)
    g.add_node("paper_c", title="Paper C", year=2019, citation_count=20)
    g.add_node("paper_d", title="Paper D", year=2022, citation_count=2)
    g.add_node("paper_e", title="Paper E", year=2023, citation_count=1)
    g.add_edges_from(
        [
            ("paper_b", "paper_a"),
            ("paper_c", "paper_a"),
            ("paper_d", "paper_b"),
            ("paper_d", "paper_c"),
            ("paper_e", "paper_a"),
            ("paper_e", "paper_d"),
        ]
    )
    return g


class TestCitationPlots:
    """Tests for citation network visualization functions."""

    def test_plot_citation_network_creates_file(self, tmp_path: Path) -> None:
        graph = _make_small_graph()
        output = tmp_path / "citation_net.png"
        result = plot_citation_network(graph, output)
        assert result == output
        assert output.exists()
        assert output.stat().st_size > 0
        # Content validation: PIL check
        from PIL import Image

        img = Image.open(output)
        assert img.width > 0 and img.height > 0
        # Additional check for non-blank figure using matplotlib
        import matplotlib.image as mpimg

        img_arr = mpimg.imread(output)
        assert img_arr.mean() > 0.01, "Figure appears blank"

    def test_plot_citation_network_with_communities(self, tmp_path: Path) -> None:
        graph = _make_small_graph()
        for node in graph.nodes():
            graph.nodes[node]["community"] = 0 if node < "paper_d" else 1
        output = tmp_path / "citation_net_communities.png"
        result = plot_citation_network(graph, output)
        assert result == output
        assert output.exists()
        assert output.stat().st_size > 0
        # Content validation: PIL check
        from PIL import Image

        img = Image.open(output)
        assert img.width > 0 and img.height > 0
        # Additional check for non-blank figure using matplotlib
        import matplotlib.image as mpimg

        img_arr = mpimg.imread(output)
        assert img_arr.mean() > 0.01, "Figure appears blank"

    def test_plot_citation_network_empty_graph(self, tmp_path: Path) -> None:
        graph = nx.DiGraph()
        output = tmp_path / "empty_net.png"
        result = plot_citation_network(graph, output)
        assert result == output
        assert output.exists()
        assert output.stat().st_size > 0
        # Content validation: PIL check
        from PIL import Image

        img = Image.open(output)
        assert img.width > 0 and img.height > 0
        # Additional check for non-blank figure using matplotlib
        import matplotlib.image as mpimg

        img_arr = mpimg.imread(output)
        assert img_arr.mean() > 0.01, "Figure appears blank"

    def test_plot_citation_network_max_nodes(self, tmp_path: Path) -> None:
        graph = _make_small_graph()
        output = tmp_path / "limited_net.png"
        result = plot_citation_network(graph, output, max_nodes=3)
        assert result == output
        assert output.exists()
        assert output.stat().st_size > 0
        # Content validation: PIL check
        from PIL import Image

        img = Image.open(output)
        assert img.width > 0 and img.height > 0
        # Additional check for non-blank figure using matplotlib
        import matplotlib.image as mpimg

        img_arr = mpimg.imread(output)
        assert img_arr.mean() > 0.01, "Figure appears blank"

    def test_plot_degree_distribution_creates_file(self, tmp_path: Path) -> None:
        graph = _make_small_graph()
        output = tmp_path / "degree_dist.png"
        result = plot_degree_distribution(graph, output)
        assert result == output
        assert output.exists()
        assert output.stat().st_size > 0
        # Content validation: PIL check
        from PIL import Image

        img = Image.open(output)
        assert img.width > 0 and img.height > 0

    def test_plot_degree_distribution_empty_graph(self, tmp_path: Path) -> None:
        graph = nx.DiGraph()
        output = tmp_path / "empty_degree.png"
        result = plot_degree_distribution(graph, output)
        assert result == output
        assert output.exists()
        assert output.stat().st_size > 0
        # Content validation: PIL check
        from PIL import Image

        img = Image.open(output)
        assert img.width > 0 and img.height > 0

    def test_plot_degree_distribution_loglog_scale_for_high_degree(self, tmp_path: Path) -> None:
        """Graphs with max in-degree > 20 trigger the log-log scale branch."""
        graph = nx.DiGraph()
        # Create a hub node that receives 25 in-edges (max_degree = 25 > 20).
        graph.add_node("hub")
        for i in range(25):
            graph.add_node(f"src_{i}")
            graph.add_edge(f"src_{i}", "hub")
        output = tmp_path / "loglog_degree.png"
        result = plot_degree_distribution(graph, output)
        assert result == output
        assert output.exists()
        assert output.stat().st_size > 0
        from PIL import Image
        img = Image.open(output)
        assert img.width > 0 and img.height > 0
