"""Tests for offline deterministic embeddings (no mocks; real sklearn computation)."""

from __future__ import annotations

import numpy as np
import pytest

from analysis.embeddings import (
    cluster_embeddings,
    cosine_similarity_matrix,
    embed_corpus,
    embed_texts,
    most_similar,
    project_2d,
)
from literature.models import Paper

# A small corpus where texts 0 and 1 are near-duplicates and 2 is unrelated.
_TEXTS = [
    "modafinil promotes wakefulness and reduces excessive daytime sleepiness in narcolepsy",
    "modafinil promotes wakefulness and reduces daytime sleepiness in narcolepsy patients",
    "dopamine transporter occupancy and pharmacokinetics of stimulant metabolism in liver",
    "functional magnetic resonance imaging of prefrontal cortex during attention tasks",
]


def test_embed_texts_shape_and_normalization() -> None:
    mat = embed_texts(_TEXTS, n_components=3, seed=42)
    assert mat.shape[0] == 4
    assert mat.shape[1] >= 1
    norms = np.linalg.norm(mat, axis=1)
    # Non-empty rows are L2-normalized to ~1.
    assert np.allclose(norms, 1.0, atol=1e-9)


def test_embed_texts_is_deterministic() -> None:
    a = embed_texts(_TEXTS, n_components=3, seed=42)
    b = embed_texts(_TEXTS, n_components=3, seed=42)
    assert np.array_equal(a, b)


def test_embed_texts_empty_input() -> None:
    assert embed_texts([]).shape == (0, 1)


def test_embed_texts_all_stopwords_returns_zeros() -> None:
    mat = embed_texts(["the the the", "a an the"], seed=42)
    assert mat.shape[0] == 2
    assert np.allclose(mat, 0.0)


def test_near_duplicates_are_nearest_neighbors() -> None:
    mat = embed_texts(_TEXTS, n_components=3, seed=42)
    ids = [f"p{i}" for i in range(len(_TEXTS))]
    nn = most_similar(mat, ids, query_index=0, top_k=3)
    # The near-duplicate (index 1) must be the closest neighbour of index 0.
    assert nn[0][0] == "p1"
    # And it must be strictly closer than the unrelated documents.
    assert nn[0][1] > nn[1][1]


def test_cosine_similarity_matrix_properties() -> None:
    mat = embed_texts(_TEXTS, n_components=3, seed=42)
    sim = cosine_similarity_matrix(mat)
    assert sim.shape == (4, 4)
    # Diagonal is self-similarity ~1 for normalized non-zero rows.
    assert np.allclose(np.diag(sim), 1.0, atol=1e-9)
    # Symmetric.
    assert np.allclose(sim, sim.T)


def test_embed_corpus_fields() -> None:
    papers = [
        Paper(title="Modafinil and wakefulness", abstract=_TEXTS[0], doi="10.5555/a"),
        Paper(title="Armodafinil cognition", abstract=_TEXTS[1], doi="10.5555/b"),
        Paper(title="Dopamine pharmacology", abstract=_TEXTS[2], doi="10.5555/c"),
    ]
    ids, mat = embed_corpus(papers, field="abstract", n_components=2, seed=42)
    assert ids == ["doi:10.5555/a", "doi:10.5555/b", "doi:10.5555/c"]
    assert mat.shape[0] == 3
    # title_abstract field also works.
    _, mat2 = embed_corpus(papers, field="title_abstract", n_components=2, seed=42)
    assert mat2.shape[0] == 3


def test_embed_corpus_full_text_field_uses_mapping_and_fallback() -> None:
    papers = [
        Paper(title="A", abstract=_TEXTS[0], doi="10.5555/a"),
        Paper(title="B", abstract=_TEXTS[2], doi="10.5555/b"),
    ]
    fulltext = {"doi:10.5555/a": _TEXTS[0] + " " + _TEXTS[1]}  # b falls back to its abstract
    ids, mat = embed_corpus(papers, field="full_text", fulltext=fulltext, n_components=2, seed=42)
    assert mat.shape[0] == 2
    # Determinism on the full-text path too.
    _, mat_again = embed_corpus(papers, field="full_text", fulltext=fulltext, n_components=2, seed=42)
    assert np.array_equal(mat, mat_again)


def test_embed_corpus_rejects_unknown_field() -> None:
    with pytest.raises(ValueError):
        embed_corpus([Paper(title="x")], field="bogus")


def test_cluster_embeddings_labels() -> None:
    mat = embed_texts(_TEXTS, n_components=3, seed=42)
    labels = cluster_embeddings(mat, n_clusters=2, seed=42)
    assert labels.shape == (4,)
    assert set(labels.tolist()) <= {0, 1}
    # Deterministic clustering.
    assert np.array_equal(labels, cluster_embeddings(mat, n_clusters=2, seed=42))


def test_cluster_clamps_to_n() -> None:
    mat = embed_texts(_TEXTS[:2], n_components=1, seed=42)
    labels = cluster_embeddings(mat, n_clusters=10, seed=42)
    assert labels.shape == (2,)


def test_project_2d_shape() -> None:
    mat = embed_texts(_TEXTS, n_components=3, seed=42)
    proj = project_2d(mat, seed=42)
    assert proj.shape == (4, 2)
    assert np.array_equal(proj, project_2d(mat, seed=42))


def test_project_2d_low_dim_pads() -> None:
    mat = embed_texts(["the the"], seed=42)  # zero/empty -> shape (1,1)
    proj = project_2d(mat, seed=42)
    assert proj.shape == (1, 2)


def test_empty_helpers() -> None:
    empty = np.zeros((0, 1))
    assert cosine_similarity_matrix(empty).shape == (0, 0)
    assert cluster_embeddings(empty).shape == (0,)
    assert project_2d(empty).shape == (0, 2)


def test_embed_texts_single_token_vocab() -> None:
    """Texts with vocab_size <= 1 use the early L2-normalize branch (no SVD)."""
    # Two documents both containing only "modafinil" — vocabulary collapses to 1 token.
    mat = embed_texts(["modafinil", "modafinil"], n_components=5, max_features=1, seed=42)
    assert mat.shape[0] == 2
    # The single-token path returns normalized TF-IDF directly (shape[1] == 1).
    assert mat.shape[1] == 1


def test_project_2d_already_2d_input() -> None:
    """project_2d with input already of shape (n, 2) pads nothing and returns directly."""
    mat = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=float)
    proj = project_2d(mat, seed=42)
    assert proj.shape == (2, 2)


def test_embed_corpus_title_field() -> None:
    """embed_corpus with field='title' uses only paper titles."""
    papers = [
        Paper(title="Modafinil wakefulness", abstract="does not matter here", doi="10.5555/t1"),
        Paper(title="Armodafinil cognition", abstract="irrelevant text", doi="10.5555/t2"),
    ]
    ids, mat = embed_corpus(papers, field="title", n_components=2, seed=42)
    assert ids == ["doi:10.5555/t1", "doi:10.5555/t2"]
    assert mat.shape[0] == 2
