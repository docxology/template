"""NMF topic extraction from TF-IDF matrices.

Implements Non-negative Matrix Factorization using multiplicative
update rules to discover latent topics in the document corpus.
"""

from __future__ import annotations

import logging

import numpy as np

logger = logging.getLogger(__name__)


def _nmf_multiplicative_updates(
    V: np.ndarray,
    n_topics: int,
    seed: int = 42,
    max_iter: int = 200,
    epsilon: float = 1e-10,
    tol: float = 1e-4,
) -> tuple[np.ndarray, np.ndarray]:
    """Run NMF via multiplicative update rules with early stopping.

    Factorizes V approximately as W @ H where V is (n_docs, n_features),
    W is (n_docs, n_topics), and H is (n_topics, n_features).

    Update rules:
        H <- H * (W^T @ V) / (W^T @ W @ H + epsilon)
        W <- W * (V @ H^T) / (W @ H @ H^T + epsilon)

    Stops early when the relative change in Frobenius reconstruction error
    between consecutive iterations falls below *tol*.

    Args:
        V: Non-negative input matrix of shape (n_docs, n_features).
        n_topics: Number of latent topics to extract.
        seed: Random seed for initialization.
        max_iter: Maximum number of update iterations.
        epsilon: Small constant to avoid division by zero.
        tol: Relative reconstruction-error change for early stopping.

    Returns:
        Tuple of (W, H) factor matrices.
    """
    rng = np.random.RandomState(seed)
    n_docs, n_features = V.shape

    # Initialize W and H with small positive random values
    W = rng.rand(n_docs, n_topics).astype(np.float64) + epsilon
    H = rng.rand(n_topics, n_features).astype(np.float64) + epsilon

    prev_error = np.linalg.norm(V - W @ H, "fro")

    for iteration in range(max_iter):
        # Update H
        numerator_h = W.T @ V
        denominator_h = W.T @ W @ H + epsilon
        H = H * (numerator_h / denominator_h)

        # Update W
        numerator_w = V @ H.T
        denominator_w = W @ H @ H.T + epsilon
        W = W * (numerator_w / denominator_w)

        # Check convergence every 10 iterations to amortize norm cost
        if (iteration + 1) % 10 == 0:
            error = np.linalg.norm(V - W @ H, "fro")
            if prev_error > 0 and abs(prev_error - error) / prev_error < tol:
                logger.debug("NMF converged at iteration %d (error=%.6f)", iteration + 1, error)
                break
            prev_error = error

    return W, H


def fit_nmf_topics(
    tfidf_matrix: np.ndarray,
    feature_names: list[str],
    n_topics: int = 5,
    seed: int = 42,
    top_n: int = 10,
    max_iter: int = 200,
) -> list[dict]:
    """Apply NMF to a TF-IDF matrix and extract topic descriptors.

    Args:
        tfidf_matrix: TF-IDF matrix of shape (n_docs, n_features).
        feature_names: List of feature/term names corresponding to columns.
        n_topics: Number of topics to extract.
        seed: Random seed for reproducibility.
        top_n: Number of top words to return per topic (default: 10).
        max_iter: Maximum NMF update iterations (default: 200).

    Returns:
        List of dicts, each containing:
            topic_id: Integer topic identifier
            top_words: List of top ``top_n`` words by weight
            weights: Corresponding weight values

    Raises:
        ValueError: If matrix is empty or n_topics < 1.
    """
    if tfidf_matrix.size == 0:
        raise ValueError("tfidf_matrix must not be empty")
    if n_topics < 1:
        raise ValueError("n_topics must be >= 1")

    n_docs, n_features = tfidf_matrix.shape

    # Clamp n_topics to feasible range
    effective_topics = min(n_topics, n_docs, n_features)
    if effective_topics < n_topics:
        logger.warning(
            "n_topics clamped %d → %d (n_docs=%d, n_features=%d)",
            n_topics,
            effective_topics,
            n_docs,
            n_features,
        )

    _W, H = _nmf_multiplicative_updates(tfidf_matrix, n_topics=effective_topics, seed=seed, max_iter=max_iter)

    topics: list[dict] = []
    for topic_idx in range(effective_topics):
        topic_weights = H[topic_idx]
        # Get indices of top-N words by weight
        n_top_actual = min(top_n, len(feature_names))
        top_indices = np.argsort(topic_weights)[::-1][:n_top_actual]
        top_words = [feature_names[i] for i in top_indices]
        weights = [float(topic_weights[i]) for i in top_indices]

        topics.append(
            {
                "topic_id": topic_idx,
                "top_words": top_words,
                "weights": weights,
            }
        )

    return topics


def get_document_topics(
    tfidf_matrix: np.ndarray,
    n_topics: int = 5,
    seed: int = 42,
    max_iter: int = 200,
) -> np.ndarray:
    """Compute document-topic distribution matrix.

    Args:
        tfidf_matrix: TF-IDF matrix of shape (n_docs, n_features).
        n_topics: Number of topics.
        seed: Random seed for reproducibility.
        max_iter: Maximum NMF update iterations (default: 200).

    Returns:
        Matrix of shape (n_docs, n_topics) where each row sums to
        approximately 1.0 (rows are L1-normalized).

    Raises:
        ValueError: If matrix is empty or n_topics < 1.
    """
    if tfidf_matrix.size == 0:
        raise ValueError("tfidf_matrix must not be empty")
    if n_topics < 1:
        raise ValueError("n_topics must be >= 1")

    n_docs, n_features = tfidf_matrix.shape
    effective_topics = min(n_topics, n_docs, n_features)
    if effective_topics < n_topics:
        logger.warning(
            "get_document_topics: n_topics clamped %d → %d",
            n_topics,
            effective_topics,
        )

    W, _H = _nmf_multiplicative_updates(tfidf_matrix, n_topics=effective_topics, seed=seed, max_iter=max_iter)

    # L1-normalize each row so it sums to 1
    row_sums = W.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    W_normalized = W / row_sums

    return W_normalized
