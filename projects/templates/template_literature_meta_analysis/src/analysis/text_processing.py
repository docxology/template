"""Text processing for paper abstracts.

Provides tokenization, stopword removal, and TF-IDF matrix
construction for the literature meta-analysis.
"""

from __future__ import annotations

import logging
import math
import re

import numpy as np

logger = logging.getLogger(__name__)

STOPWORDS: set[str] = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "but",
    "if",
    "in",
    "on",
    "at",
    "to",
    "for",
    "of",
    "with",
    "by",
    "from",
    "as",
    "is",
    "was",
    "are",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "shall",
    "should",
    "may",
    "might",
    "must",
    "can",
    "could",
    "not",
    "no",
    "nor",
    "so",
    "too",
    "very",
    "just",
    "also",
    "than",
    "then",
    "that",
    "this",
    "these",
    "those",
    "it",
    "its",
    "he",
    "she",
    "they",
    "we",
    "you",
    "me",
    "him",
    "her",
    "us",
    "them",
    "my",
    "your",
    "his",
    "our",
    "their",
    "mine",
    "yours",
    "hers",
    "ours",
    "theirs",
    "who",
    "whom",
    "which",
    "what",
    "where",
    "when",
    "how",
    "all",
    "each",
    "every",
    "both",
    "few",
    "more",
    "most",
    "other",
    "some",
    "such",
    "any",
    "only",
    "own",
    "same",
    "about",
    "up",
    "out",
    "into",
    "over",
    "after",
    "before",
    "between",
    "under",
    "again",
    "further",
    "once",
    "here",
    "there",
    "why",
    "because",
    "during",
    "while",
    "through",
    "above",
    "below",
    "itself",
    "himself",
    "herself",
    "themselves",
    "ourselves",
    "yourself",
    "yourselves",
    "myself",
    "am",
    "does",
    "doing",
}


def tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase alpha-numeric tokens.

    Splits on non-alphanumeric characters and filters out tokens
    shorter than 2 characters.

    Args:
        text: Raw input text.

    Returns:
        List of lowercase tokens with length >= 2.
    """
    tokens = re.split(r"[^a-zA-Z0-9]+", text.lower())
    return [t for t in tokens if len(t) >= 2]


def remove_stopwords(tokens: list[str], extra_stopwords: set[str] | None = None) -> list[str]:
    """Remove common English stopwords from token list.

    Args:
        tokens: List of tokens to filter.
        extra_stopwords: Optional additional stopwords to remove.

    Returns:
        Filtered list with stopwords removed.
    """
    stop = STOPWORDS
    if extra_stopwords:
        stop = stop | extra_stopwords
    return [t for t in tokens if t not in stop]


def tokenize_documents(documents: list[str]) -> list[list[str]]:
    """Tokenize and de-stopword a list of document strings."""
    return [remove_stopwords(tokenize(doc)) for doc in documents]


def build_tfidf_matrix(documents: list[str], max_features: int = 1000) -> tuple[np.ndarray, list[str]]:
    """Build a TF-IDF matrix from raw document texts.

    Implements TF-IDF manually:
        TF  = term_count / total_terms_in_doc
        IDF = log(N / (df + 1)) + 1
        TF-IDF = TF * IDF
    Rows are L2-normalized to unit length.

    Args:
        documents: List of raw document strings.
        max_features: Maximum number of features (vocabulary size).

    Returns:
        Tuple of (tfidf_matrix, feature_names) where tfidf_matrix
        is shape (n_docs, n_features) and feature_names is the
        corresponding vocabulary list.

    Raises:
        ValueError: If documents list is empty.
    """
    if not documents:
        raise ValueError("documents list must not be empty")

    n_docs = len(documents)

    # Tokenize and remove stopwords for each document
    doc_tokens: list[list[str]] = []
    for doc in documents:
        tokens = tokenize(doc)
        tokens = remove_stopwords(tokens)
        doc_tokens.append(tokens)

    # Compute document frequency for each term
    df: dict[str, int] = {}
    for tokens in doc_tokens:
        unique_tokens = set(tokens)
        for token in unique_tokens:
            df[token] = df.get(token, 0) + 1

    # Select features by document frequency, but cap ultra-common terms
    # when the corpus is large enough for the cutoff to be meaningful.
    # Terms appearing in > 95% of documents (when n_docs >= 20) carry
    # negligible discriminative signal and act as corpus-level stopwords.
    if n_docs >= 20:
        df_upper = max(1, int(0.95 * n_docs))
        filtered_terms = [t for t in df if df[t] < df_upper]
        empty_docs = sum(1 for t in doc_tokens if not t)
        if empty_docs:
            logger.warning("build_tfidf_matrix: %d empty documents (after stopword removal)", empty_docs)
    else:
        filtered_terms = list(df.keys())
    sorted_terms = sorted(filtered_terms, key=lambda t: (-df[t], t))
    vocabulary = sorted_terms[:max_features]
    vocab_index = {term: idx for idx, term in enumerate(vocabulary)}
    n_features = len(vocabulary)

    if n_features == 0:
        return np.zeros((n_docs, 0), dtype=np.float64), []

    # Build TF-IDF matrix
    matrix = np.zeros((n_docs, n_features), dtype=np.float64)

    for doc_idx, tokens in enumerate(doc_tokens):
        if not tokens:
            continue
        total = len(tokens)
        # Count term frequencies for this document
        term_counts: dict[str, int] = {}
        for token in tokens:
            if token in vocab_index:
                term_counts[token] = term_counts.get(token, 0) + 1

        for term, count in term_counts.items():
            col = vocab_index[term]
            tf = count / total
            idf = math.log(n_docs / (df[term] + 1)) + 1
            matrix[doc_idx, col] = tf * idf

    # L2-normalize each row
    row_norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    # Avoid division by zero for empty documents
    row_norms[row_norms == 0] = 1.0
    matrix = matrix / row_norms

    return matrix, vocabulary
