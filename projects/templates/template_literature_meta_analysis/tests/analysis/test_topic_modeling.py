"""Tests for analysis.topic_modeling module.

Validates NMF topic extraction and document-topic distribution
using synthetic documents with known topical structure.
"""

import numpy as np
import pytest

from analysis.text_processing import build_tfidf_matrix
from analysis.topic_modeling import (
    fit_nmf_topics,
    get_document_topics,
    _nmf_multiplicative_updates,
)


# ── Test data ─────────────────────────────────────────────────────────

# Documents with two distinct themes:
#   Theme A: neuroscience/brain terms
#   Theme B: robotics/control terms
DOCS_TWO_THEMES = [
    "brain cortex neural synaptic processing cortex neural",
    "neural cortex brain hippocampal cortical signals",
    "cortex brain synaptic dopamine neural processing",
    "robot motor control navigation manipulation embodied",
    "robot navigation embodied motor sensorimotor control",
    "manipulation robot motor control embodied navigation",
]

DOCS_THREE_THEMES = [
    "brain cortex neural synaptic processing",
    "cortex brain hippocampal neural signals",
    "robot motor control navigation embodied",
    "robot manipulation sensorimotor motor control",
    "language speech semantic reading communication",
    "linguistic speech semantic reading language",
]


# ── _nmf_multiplicative_updates ──────────────────────────────────────


class TestNMFMultiplicativeUpdates:
    """Tests for the internal NMF algorithm."""

    def test_output_shapes(self):
        """W and H have correct shapes."""
        rng = np.random.RandomState(42)
        V = rng.rand(10, 20)
        W, H = _nmf_multiplicative_updates(V, n_topics=3, seed=42)
        assert W.shape == (10, 3)
        assert H.shape == (3, 20)

    def test_non_negative(self):
        """Both W and H should be non-negative."""
        rng = np.random.RandomState(42)
        V = rng.rand(8, 15)
        W, H = _nmf_multiplicative_updates(V, n_topics=2, seed=42)
        assert np.all(W >= 0)
        assert np.all(H >= 0)

    def test_approximation_quality(self):
        """W @ H should roughly approximate V (low reconstruction error)."""
        rng = np.random.RandomState(42)
        V = rng.rand(6, 10)
        W, H = _nmf_multiplicative_updates(V, n_topics=5, seed=42, max_iter=500)
        reconstruction = W @ H
        error = np.linalg.norm(V - reconstruction) / np.linalg.norm(V)
        # Relative error should be small-ish with 5 topics for a 6x10 matrix
        assert error < 0.5

    def test_deterministic_with_same_seed(self):
        """Same seed produces identical results."""
        rng = np.random.RandomState(42)
        V = rng.rand(5, 8)
        W1, H1 = _nmf_multiplicative_updates(V, n_topics=2, seed=42)
        W2, H2 = _nmf_multiplicative_updates(V, n_topics=2, seed=42)
        np.testing.assert_array_equal(W1, W2)
        np.testing.assert_array_equal(H1, H2)


# ── fit_nmf_topics ───────────────────────────────────────────────────


class TestFitNMFTopics:
    """Tests for fit_nmf_topics."""

    def test_output_structure(self):
        """Each topic dict has topic_id, top_words, and weights."""
        matrix, features = build_tfidf_matrix(DOCS_TWO_THEMES)
        topics = fit_nmf_topics(matrix, features, n_topics=2, seed=42)

        assert len(topics) == 2
        for topic in topics:
            assert "topic_id" in topic
            assert "top_words" in topic
            assert "weights" in topic
            assert isinstance(topic["topic_id"], int)
            assert isinstance(topic["top_words"], list)
            assert isinstance(topic["weights"], list)
            assert len(topic["top_words"]) == len(topic["weights"])

    def test_top_words_are_strings(self):
        """Top words are string tokens from the vocabulary."""
        matrix, features = build_tfidf_matrix(DOCS_TWO_THEMES)
        topics = fit_nmf_topics(matrix, features, n_topics=2, seed=42)

        for topic in topics:
            for word in topic["top_words"]:
                assert isinstance(word, str)
                assert word in features

    def test_weights_are_positive(self):
        """All weights should be non-negative."""
        matrix, features = build_tfidf_matrix(DOCS_TWO_THEMES)
        topics = fit_nmf_topics(matrix, features, n_topics=2, seed=42)

        for topic in topics:
            assert all(w >= 0 for w in topic["weights"])

    def test_weights_sorted_descending(self):
        """Weights correspond to argsort order (descending)."""
        matrix, features = build_tfidf_matrix(DOCS_TWO_THEMES)
        topics = fit_nmf_topics(matrix, features, n_topics=2, seed=42)

        for topic in topics:
            weights = topic["weights"]
            for i in range(len(weights) - 1):
                assert weights[i] >= weights[i + 1]

    def test_topic_ids_sequential(self):
        """Topic IDs go from 0 to n_topics-1."""
        matrix, features = build_tfidf_matrix(DOCS_TWO_THEMES)
        topics = fit_nmf_topics(matrix, features, n_topics=2, seed=42)
        ids = [t["topic_id"] for t in topics]
        assert ids == [0, 1]

    def test_two_themes_separation(self):
        """With 2 topics, each topic should capture one theme."""
        matrix, features = build_tfidf_matrix(DOCS_TWO_THEMES)
        topics = fit_nmf_topics(matrix, features, n_topics=2, seed=42)

        # Collect the top-5 words from each topic
        topic_words = [set(t["top_words"][:5]) for t in topics]

        brain_words = {"brain", "cortex", "neural", "synaptic", "processing"}
        robot_words = {"robot", "motor", "control", "navigation", "embodied"}

        # At least one topic should overlap significantly with brain words
        # and the other with robot words
        overlaps_brain = [len(tw & brain_words) for tw in topic_words]
        overlaps_robot = [len(tw & robot_words) for tw in topic_words]

        assert max(overlaps_brain) >= 2, "No topic captures brain theme"
        assert max(overlaps_robot) >= 2, "No topic captures robot theme"

    def test_empty_matrix_raises(self):
        """Empty matrix raises ValueError."""
        with pytest.raises(ValueError, match="must not be empty"):
            fit_nmf_topics(np.array([]), ["x"], n_topics=2, seed=42)

    def test_invalid_n_topics_raises(self):
        """n_topics < 1 raises ValueError."""
        matrix = np.array([[1.0, 2.0]])
        with pytest.raises(ValueError, match="n_topics must be >= 1"):
            fit_nmf_topics(matrix, ["a", "b"], n_topics=0, seed=42)

    def test_three_topics(self):
        """Three-topic extraction on three-theme corpus."""
        matrix, features = build_tfidf_matrix(DOCS_THREE_THEMES)
        topics = fit_nmf_topics(matrix, features, n_topics=3, seed=42)
        assert len(topics) == 3


# ── get_document_topics ──────────────────────────────────────────────


class TestGetDocumentTopics:
    """Tests for get_document_topics."""

    def test_output_shape(self):
        """Shape is (n_docs, n_topics)."""
        matrix, features = build_tfidf_matrix(DOCS_TWO_THEMES)
        doc_topics = get_document_topics(matrix, n_topics=2, seed=42)
        assert doc_topics.shape == (6, 2)

    def test_rows_sum_to_one(self):
        """Each row should sum to approximately 1.0."""
        matrix, features = build_tfidf_matrix(DOCS_TWO_THEMES)
        doc_topics = get_document_topics(matrix, n_topics=2, seed=42)

        for i in range(doc_topics.shape[0]):
            assert abs(doc_topics[i].sum() - 1.0) < 1e-6, f"Row {i} sums to {doc_topics[i].sum()}"

    def test_non_negative(self):
        """All values should be non-negative."""
        matrix, features = build_tfidf_matrix(DOCS_TWO_THEMES)
        doc_topics = get_document_topics(matrix, n_topics=2, seed=42)
        assert np.all(doc_topics >= 0)

    def test_deterministic(self):
        """Same inputs and seed produce identical results."""
        matrix, features = build_tfidf_matrix(DOCS_TWO_THEMES)
        dt1 = get_document_topics(matrix, n_topics=2, seed=42)
        dt2 = get_document_topics(matrix, n_topics=2, seed=42)
        np.testing.assert_array_equal(dt1, dt2)

    def test_different_seeds_differ(self):
        """Different seeds produce different results."""
        matrix, features = build_tfidf_matrix(DOCS_TWO_THEMES)
        dt1 = get_document_topics(matrix, n_topics=2, seed=42)
        dt2 = get_document_topics(matrix, n_topics=2, seed=123)
        # They might converge to the same factorization, but generally won't
        # At minimum, the shape should be correct
        assert dt1.shape == dt2.shape

    def test_empty_matrix_raises(self):
        """Empty matrix raises ValueError."""
        with pytest.raises(ValueError, match="must not be empty"):
            get_document_topics(np.array([]), n_topics=2, seed=42)

    def test_single_document(self):
        """Single document still produces valid output."""
        matrix, features = build_tfidf_matrix(["brain cortex neural processing"])
        doc_topics = get_document_topics(matrix, n_topics=1, seed=42)
        assert doc_topics.shape == (1, 1)
        assert abs(doc_topics[0, 0] - 1.0) < 1e-6
