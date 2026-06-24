"""Tests for analysis.text_processing module.

Validates tokenization, stopword removal, and TF-IDF matrix
construction using small known datasets with hand-verified outputs.
"""

import math

import numpy as np
import pytest

from analysis.text_processing import (
    STOPWORDS,
    build_tfidf_matrix,
    remove_stopwords,
    tokenize,
)


# ── tokenize ──────────────────────────────────────────────────────────


class TestTokenize:
    """Tests for the tokenize function."""

    def test_basic_sentence(self):
        """Lowercase splitting on a simple sentence."""
        result = tokenize("Hello World")
        assert result == ["hello", "world"]

    def test_punctuation_removed(self):
        """Punctuation acts as a splitter and is not in output."""
        result = tokenize("active-inference, bayesian brain.")
        assert "active" in result
        assert "inference" in result
        assert "bayesian" in result
        assert "brain" in result
        # No punctuation tokens
        assert "," not in result
        assert "." not in result

    def test_short_tokens_filtered(self):
        """Single-character tokens are excluded."""
        result = tokenize("I am a big fan of AI")
        # "i", "a" are length 1 => excluded
        assert "i" not in result
        assert "a" not in result
        assert "am" in result
        assert "big" in result
        assert "fan" in result
        assert "of" in result
        assert "ai" in result

    def test_numeric_tokens_kept(self):
        """Numeric tokens of length >= 2 are retained."""
        result = tokenize("section 42 has 7 parts")
        assert "42" in result
        assert "section" in result
        assert "has" in result
        assert "parts" in result
        # "7" is length 1 => excluded
        assert "7" not in result

    def test_empty_string(self):
        """Empty input returns empty list."""
        assert tokenize("") == []

    def test_all_short_tokens(self):
        """All single-char input yields empty result."""
        assert tokenize("a b c d") == []

    def test_mixed_case_lowered(self):
        """Mixed case is lowered consistently."""
        result = tokenize("TF-IDF Matrix CONSTRUCTION")
        assert "tf" in result
        assert "idf" in result
        assert "matrix" in result
        assert "construction" in result


# ── remove_stopwords ──────────────────────────────────────────────────


class TestRemoveStopwords:
    """Tests for the remove_stopwords function."""

    def test_common_stopwords_removed(self):
        """Standard English stopwords are filtered out."""
        tokens = ["the", "brain", "is", "a", "predictive", "machine"]
        result = remove_stopwords(tokens)
        assert "brain" in result
        assert "predictive" in result
        assert "machine" in result
        assert "the" not in result
        assert "is" not in result
        assert "a" not in result

    def test_extra_stopwords(self):
        """Custom extra stopwords are also removed."""
        tokens = ["active", "inference", "model", "figure"]
        result = remove_stopwords(tokens, extra_stopwords={"model", "figure"})
        assert result == ["active", "inference"]

    def test_no_stopwords_in_input(self):
        """Tokens without stopwords pass through unchanged."""
        tokens = ["bayesian", "cortex", "dopamine"]
        result = remove_stopwords(tokens)
        assert result == ["bayesian", "cortex", "dopamine"]

    def test_all_stopwords(self):
        """All-stopword input yields empty list."""
        tokens = ["the", "is", "a", "and", "or"]
        result = remove_stopwords(tokens)
        assert result == []

    def test_empty_input(self):
        """Empty list returns empty list."""
        assert remove_stopwords([]) == []

    def test_stopwords_constant_has_common_words(self):
        """STOPWORDS constant includes typical English stopwords."""
        for word in ["the", "is", "a", "and", "or", "but", "in", "on", "at"]:
            assert word in STOPWORDS


# ── build_tfidf_matrix ────────────────────────────────────────────────


class TestBuildTfidfMatrix:
    """Tests for the build_tfidf_matrix function."""

    def test_basic_shape(self):
        """Matrix shape matches (n_docs, n_features)."""
        docs = [
            "the brain processes signals",
            "neural networks learn patterns",
            "active inference predicts outcomes",
        ]
        matrix, features = build_tfidf_matrix(docs)
        assert matrix.shape[0] == 3
        assert matrix.shape[1] == len(features)
        assert len(features) > 0

    def test_row_normalization(self):
        """Each non-zero row should be L2-normalized to unit length."""
        docs = [
            "brain cortex neural signals processing",
            "robot motor control navigation embodied",
            "bayesian inference predictive processing variational",
        ]
        matrix, _features = build_tfidf_matrix(docs)
        for i in range(matrix.shape[0]):
            norm = np.linalg.norm(matrix[i])
            if norm > 0:
                assert abs(norm - 1.0) < 1e-6, f"Row {i} norm = {norm}"

    def test_known_tfidf_values(self):
        """Verify TF-IDF calculation with hand-computed values."""
        # Two documents, each with distinct terms plus one shared
        docs = [
            "brain brain cortex",
            "brain robot robot",
        ]
        matrix, features = build_tfidf_matrix(docs)
        n_docs = 2

        # "brain" appears in both docs => df=2
        # "cortex" appears in doc 0 only => df=1
        # "robot" appears in doc 1 only => df=1

        assert "brain" in features
        assert "cortex" in features
        assert "robot" in features

        brain_idx = features.index("brain")
        cortex_idx = features.index("cortex")
        robot_idx = features.index("robot")

        # Doc 0: tokens after stopword removal = ["brain", "brain", "cortex"] (3 tokens)
        # TF(brain, doc0) = 2/3, IDF(brain) = log(2/3)+1
        # TF(cortex, doc0) = 1/3, IDF(cortex) = log(2/2)+1 = log(1)+1 = 1
        idf_brain = math.log(n_docs / (2 + 1)) + 1
        idf_cortex = math.log(n_docs / (1 + 1)) + 1

        # Before normalization:
        raw_00 = (2 / 3) * idf_brain  # brain in doc0
        raw_01 = (1 / 3) * idf_cortex  # cortex in doc0
        # Doc 0 has 0 for robot
        norm_0 = math.sqrt(raw_00**2 + raw_01**2)

        expected_brain_doc0 = raw_00 / norm_0
        expected_cortex_doc0 = raw_01 / norm_0

        assert abs(matrix[0, brain_idx] - expected_brain_doc0) < 1e-6
        assert abs(matrix[0, cortex_idx] - expected_cortex_doc0) < 1e-6
        assert abs(matrix[0, robot_idx] - 0.0) < 1e-6

    def test_max_features_limits_vocabulary(self):
        """max_features caps the vocabulary size."""
        docs = [
            "alpha beta gamma delta epsilon zeta",
            "alpha beta gamma theta iota kappa",
        ]
        matrix, features = build_tfidf_matrix(docs, max_features=3)
        assert len(features) <= 3
        assert matrix.shape[1] <= 3

    def test_empty_documents_raises(self):
        """Empty document list raises ValueError."""
        with pytest.raises(ValueError, match="must not be empty"):
            build_tfidf_matrix([])

    def test_all_stopword_documents(self):
        """Documents with only stopwords produce a zero-column matrix."""
        docs = ["the and is", "a or but"]
        matrix, features = build_tfidf_matrix(docs)
        assert matrix.shape[1] == 0
        assert features == []

    def test_single_document(self):
        """Single document produces valid matrix."""
        docs = ["active inference free energy principle"]
        matrix, features = build_tfidf_matrix(docs)
        assert matrix.shape[0] == 1
        assert matrix.shape[1] > 0
        # Single doc: row should still be normalized
        norm = np.linalg.norm(matrix[0])
        if norm > 0:
            assert abs(norm - 1.0) < 1e-6

    def test_duplicate_terms_within_document(self):
        """Repeated terms get higher TF weight."""
        docs = [
            "inference inference inference brain",
            "brain brain brain inference",
        ]
        matrix, features = build_tfidf_matrix(docs)
        inference_idx = features.index("inference")
        brain_idx = features.index("brain")

        # Doc 0 should weight "inference" more, doc 1 should weight "brain" more
        # But both terms have same IDF (df=2 for both), so the raw TF differs
        # Doc 0: TF(inference)=3/4 vs TF(brain)=1/4
        # Doc 1: TF(brain)=3/4 vs TF(inference)=1/4
        # After normalization, the proportional relationship holds
        assert matrix[0, inference_idx] > matrix[0, brain_idx]
        assert matrix[1, brain_idx] > matrix[1, inference_idx]

    def test_filters_ultra_common_terms_in_large_corpus(self):
        """Terms in >95% of documents are dropped when n_docs >= 20."""
        filler = "inference energy model predictive coding variational"
        docs = [f"{filler} uniquetoken{idx}" for idx in range(24)]
        matrix, features = build_tfidf_matrix(docs, max_features=50)
        assert matrix.shape[0] == 24
        assert "inference" not in features
        assert any(name.startswith("uniquetoken") for name in features)
