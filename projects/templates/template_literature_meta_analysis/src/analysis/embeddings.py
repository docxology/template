"""First-class, offline, deterministic document embeddings.

The default method is TF-IDF -> truncated SVD (a.k.a. LSA): no network, no GPU, no
large model download, and byte-stable across runs (fixed ``random_state``). This
makes embeddings part of the idempotent default pipeline. An optional transformer
upgrade (``sentence-transformers``) is documented in the README and gated behind the
``embeddings`` extra; it is never required for CI.

Vectors are produced for any text field of a corpus — ``title``, ``abstract``,
``title_abstract``, or ``full_text`` (supplied via a mapping) — and the module
provides the similarity, nearest-neighbour, clustering, and 2-D projection
primitives that the visualization and meta-report layers consume.

Determinism is the load-bearing property: ``embed_texts(x) == embed_texts(x)``
exactly, for the same inputs and parameters.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from literature.models import Paper

DEFAULT_SEED = 42
_VALID_FIELDS = ("title", "abstract", "title_abstract", "full_text")


def _l2_normalize(mat: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return mat / norms


def embed_texts(
    texts: list[str],
    *,
    n_components: int = 50,
    max_features: int = 2000,
    seed: int = DEFAULT_SEED,
) -> np.ndarray:
    """Embed ``texts`` into an L2-normalized dense matrix of shape ``[n, k]``.

    TF-IDF features are reduced with :class:`~sklearn.decomposition.TruncatedSVD`.
    ``k`` is clamped to a value valid for the (n_samples, vocabulary) shape, so tiny
    inputs degrade gracefully rather than raising.
    """
    from sklearn.decomposition import TruncatedSVD
    from sklearn.feature_extraction.text import TfidfVectorizer

    n = len(texts)
    if n == 0:
        return np.zeros((0, 1), dtype=float)

    vectorizer = TfidfVectorizer(max_features=max_features, stop_words="english")
    try:
        tfidf = vectorizer.fit_transform(texts)
    except ValueError:
        # Empty vocabulary (e.g. all stop-words / blank) — return zero embeddings.
        return np.zeros((n, 1), dtype=float)

    vocab_size = tfidf.shape[1]
    if vocab_size <= 1:
        return _l2_normalize(np.asarray(tfidf.todense(), dtype=float))

    k = min(n_components, vocab_size - 1, n)
    k = max(1, k)
    svd = TruncatedSVD(n_components=k, random_state=seed)
    reduced = svd.fit_transform(tfidf)
    return _l2_normalize(np.asarray(reduced, dtype=float))


def _field_text(paper: Paper, field: str, fulltext: Optional[dict[str, str]]) -> str:
    if field == "title":
        return paper.title or ""
    if field == "abstract":
        return paper.abstract or ""
    if field == "title_abstract":
        return f"{paper.title or ''} {paper.abstract or ''}".strip()
    if field == "full_text":
        if fulltext and paper.canonical_id in fulltext:
            return fulltext[paper.canonical_id]
        return paper.abstract or ""  # graceful fallback when full text is absent
    raise ValueError(f"Unknown field {field!r}; expected one of {_VALID_FIELDS}")


def embed_corpus(
    papers: list[Paper],
    field: str = "abstract",
    *,
    fulltext: Optional[dict[str, str]] = None,
    n_components: int = 50,
    max_features: int = 2000,
    seed: int = DEFAULT_SEED,
) -> tuple[list[str], np.ndarray]:
    """Embed a corpus by a chosen text ``field``; return ``(canonical_ids, matrix)``."""
    if field not in _VALID_FIELDS:
        raise ValueError(f"Unknown field {field!r}; expected one of {_VALID_FIELDS}")
    ids = [p.canonical_id for p in papers]
    texts = [_field_text(p, field, fulltext) for p in papers]
    mat = embed_texts(texts, n_components=n_components, max_features=max_features, seed=seed)
    return ids, mat


def cosine_similarity_matrix(mat: np.ndarray) -> np.ndarray:
    """Pairwise cosine similarity. Rows are L2-normalized, so this is ``mat @ mat.T``."""
    if mat.shape[0] == 0:
        return np.zeros((0, 0), dtype=float)
    return np.asarray(mat @ mat.T, dtype=float)


def most_similar(mat: np.ndarray, ids: list[str], query_index: int, top_k: int = 5) -> list[tuple[str, float]]:
    """Return the ``top_k`` most similar records to ``ids[query_index]`` (excluding self)."""
    sims = cosine_similarity_matrix(mat)[query_index]
    order = np.argsort(-sims)
    out: list[tuple[str, float]] = []
    for j in order:
        if int(j) == query_index:
            continue
        out.append((ids[int(j)], float(sims[int(j)])))
        if len(out) >= top_k:
            break
    return out


def cluster_embeddings(mat: np.ndarray, n_clusters: int = 5, seed: int = DEFAULT_SEED) -> np.ndarray:
    """KMeans cluster labels for the embedding rows. ``n_clusters`` is clamped to ``n``."""
    from sklearn.cluster import KMeans

    n = mat.shape[0]
    if n == 0:
        return np.zeros((0,), dtype=int)
    k = max(1, min(n_clusters, n))
    km = KMeans(n_clusters=k, random_state=seed, n_init=10)
    return km.fit_predict(mat).astype(int)


def project_2d(mat: np.ndarray, seed: int = DEFAULT_SEED) -> np.ndarray:
    """Project embeddings to 2 dimensions for plotting (deterministic)."""
    n = mat.shape[0]
    if n == 0:
        return np.zeros((0, 2), dtype=float)
    if mat.shape[1] <= 2:
        out = np.zeros((n, 2), dtype=float)
        out[:, : mat.shape[1]] = mat
        return out
    from sklearn.decomposition import TruncatedSVD

    k = min(2, n, mat.shape[1] - 1)
    k = max(1, k)
    svd = TruncatedSVD(n_components=k, random_state=seed)
    reduced = svd.fit_transform(mat)
    if reduced.shape[1] < 2:
        out = np.zeros((n, 2), dtype=float)
        out[:, : reduced.shape[1]] = reduced
        return out
    return np.asarray(reduced, dtype=float)
