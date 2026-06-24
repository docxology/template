from __future__ import annotations
from pathlib import Path
import numpy as np
from visualization.advanced_plots import (
    plot_word_cloud,
    plot_pca_embeddings,
    plot_term_heatmap,
    plot_dendrogram,
    plot_topic_term_bars,
    plot_cooccurrence_matrix,
)


def _make_synthetic_tfidf(
    n_docs: int = 20, n_features: int = 50, seed: int = 42
) -> tuple[np.ndarray, list[str], list[str]]:
    """Create synthetic TF-IDF matrix with labels and feature names."""
    rng = np.random.RandomState(seed)
    matrix = rng.rand(n_docs, n_features).astype(np.float64)
    # L2-normalize
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    matrix /= norms
    feature_names = [f"term_{i}" for i in range(n_features)]
    domains = ["A2_philosophy", "C1_neuroscience", "C2_robotics", "B_tools"]
    labels = [domains[i % len(domains)] for i in range(n_docs)]
    return matrix, feature_names, labels


class TestAdvancedPlots:
    """Tests for advanced visualization functions."""

    # -- word cloud ---
    def test_plot_word_cloud_creates_file(self, tmp_path: Path) -> None:
        weights = {"active": 0.9, "inference": 0.85, "free": 0.7, "energy": 0.65, "model": 0.6, "brain": 0.5}
        output = tmp_path / "word_cloud.png"
        result = plot_word_cloud(weights, output)
        assert result == output
        assert output.exists()
        assert output.stat().st_size > 0
        # Content validation: PIL check
        from PIL import Image

        img = Image.open(output)
        assert img.width > 0 and img.height > 0

    def test_plot_word_cloud_empty(self, tmp_path: Path) -> None:
        output = tmp_path / "empty_wc.png"
        result = plot_word_cloud({}, output)
        assert result == output
        assert output.exists()
        assert output.stat().st_size > 0
        # Content validation: PIL check (empty word cloud still produces valid image)
        from PIL import Image

        img = Image.open(output)
        assert img.width > 0 and img.height > 0

    # -- PCA embeddings ---
    def test_plot_pca_embeddings_creates_file(self, tmp_path: Path) -> None:
        matrix, features, labels = _make_synthetic_tfidf()
        output = tmp_path / "pca.png"
        result = plot_pca_embeddings(matrix, labels, features, output)
        assert result == output
        assert output.exists()
        assert output.stat().st_size > 0
        # Content validation: PIL check
        from PIL import Image

        img = Image.open(output)
        assert img.width > 0 and img.height > 0

    def test_plot_pca_embeddings_insufficient_data(self, tmp_path: Path) -> None:
        matrix = np.array([[1.0]])
        output = tmp_path / "pca_small.png"
        result = plot_pca_embeddings(matrix, ["A2_philosophy"], ["term_0"], output)
        assert result == output
        assert output.exists()
        # Content validation: PIL check
        from PIL import Image

        img = Image.open(output)
        assert img.width > 0 and img.height > 0

    # -- term heatmap ---
    def test_plot_term_heatmap_creates_file(self, tmp_path: Path) -> None:
        matrix, features, labels = _make_synthetic_tfidf()
        output = tmp_path / "heatmap.png"
        result = plot_term_heatmap(matrix, features, labels, output, n_terms=10)
        assert result == output
        assert output.exists()
        assert output.stat().st_size > 0
        # Content validation: PIL check
        from PIL import Image

        img = Image.open(output)
        assert img.width > 0 and img.height > 0

    def test_plot_term_heatmap_empty(self, tmp_path: Path) -> None:
        output = tmp_path / "empty_hm.png"
        result = plot_term_heatmap(np.array([]), [], [], output)
        assert result == output
        assert output.exists()
        # Content validation: PIL check
        from PIL import Image

        img = Image.open(output)
        assert img.width > 0 and img.height > 0

    # -- dendrogram ---
    def test_plot_dendrogram_creates_file(self, tmp_path: Path) -> None:
        matrix, features, labels = _make_synthetic_tfidf()
        output = tmp_path / "dendro.png"
        result = plot_dendrogram(matrix, labels, output)
        assert result == output
        assert output.exists()
        assert output.stat().st_size > 0
        # Content validation: PIL check
        from PIL import Image

        img = Image.open(output)
        assert img.width > 0 and img.height > 0

    def test_plot_dendrogram_single_label(self, tmp_path: Path) -> None:
        matrix = np.random.rand(5, 10)
        output = tmp_path / "dendro_single.png"
        result = plot_dendrogram(matrix, ["A2_philosophy"] * 5, output)
        assert result == output
        assert output.exists()
        # Content validation: PIL check
        from PIL import Image

        img = Image.open(output)
        assert img.width > 0 and img.height > 0

    # -- topic-term bars ---
    def test_plot_topic_term_bars_creates_file(self, tmp_path: Path) -> None:
        topics = [
            {"topic_id": 0, "top_words": ["brain", "cortex", "neural"], "weights": [0.9, 0.7, 0.5]},
            {"topic_id": 1, "top_words": ["robot", "motor", "arm"], "weights": [0.8, 0.6, 0.4]},
        ]
        output = tmp_path / "topic_bars.png"
        result = plot_topic_term_bars(topics, output)
        assert result == output
        assert output.exists()
        assert output.stat().st_size > 0
        # Content validation: PIL check
        from PIL import Image

        img = Image.open(output)
        assert img.width > 0 and img.height > 0

    def test_plot_topic_term_bars_empty(self, tmp_path: Path) -> None:
        output = tmp_path / "empty_topics.png"
        result = plot_topic_term_bars([], output)
        assert result == output
        assert output.exists()
        # Content validation: PIL check
        from PIL import Image

        img = Image.open(output)
        assert img.width > 0 and img.height > 0

    def test_plot_topic_term_bars_single(self, tmp_path: Path) -> None:
        topics = [{"topic_id": 0, "top_words": ["x", "y"], "weights": [1.0, 0.5]}]
        output = tmp_path / "single_topic.png"
        result = plot_topic_term_bars(topics, output)
        assert result == output
        assert output.exists()
        # Content validation: PIL check
        from PIL import Image

        img = Image.open(output)
        assert img.width > 0 and img.height > 0

    # -- co-occurrence matrix ---
    def test_plot_cooccurrence_matrix_creates_file(self, tmp_path: Path) -> None:
        docs = [
            ["brain", "cortex", "neural", "active"],
            ["brain", "active", "inference", "model"],
            ["robot", "motor", "active", "control"],
            ["cortex", "neural", "prediction", "brain"],
        ]
        output = tmp_path / "cooc.png"
        result = plot_cooccurrence_matrix(docs, output, n_terms=6)
        assert result == output
        assert output.exists()
        assert output.stat().st_size > 0
        # Content validation: PIL check
        from PIL import Image

        img = Image.open(output)
        assert img.width > 0 and img.height > 0

    def test_plot_topic_term_bars_empty_words_panel(self, tmp_path: Path) -> None:
        topics = [
            {"topic_id": 0, "top_words": [], "weights": []},
            {"topic_id": 1, "top_words": ["inference"], "weights": [0.9]},
        ]
        output = tmp_path / "mixed_topics.png"
        result = plot_topic_term_bars(topics, output)
        assert result == output
        assert output.exists()

    def test_plot_topic_term_bars_four_topics_pads_grid(self, tmp_path: Path) -> None:
        topics = [
            {
                "topic_id": idx,
                "top_words": [f"word_{idx}a", f"word_{idx}b"],
                "weights": [0.8, 0.4],
            }
            for idx in range(4)
        ]
        output = tmp_path / "four_topics.png"
        result = plot_topic_term_bars(topics, output)
        assert result == output
        assert output.exists()

    def test_plot_cooccurrence_matrix_single_term(self, tmp_path: Path) -> None:
        docs = [["onlyterm"], ["onlyterm"], ["onlyterm"]]
        output = tmp_path / "single_term_cooc.png"
        result = plot_cooccurrence_matrix(docs, output)
        assert result == output
        assert output.exists()

    def test_plot_cooccurrence_matrix_empty(self, tmp_path: Path) -> None:
        output = tmp_path / "empty_cooc.png"
        result = plot_cooccurrence_matrix([], output)
        assert result == output
        assert output.exists()

    def test_plot_cooccurrence_matrix_non_overlapping_terms(self, tmp_path: Path) -> None:
        docs = [["alpha"], ["beta"]]
        output = tmp_path / "disjoint_cooc.png"
        result = plot_cooccurrence_matrix(docs, output)
        assert result == output
        assert output.exists()
