"""Correlation analysis for the EDA exemplar.

Wraps ``pandas`` Pearson correlation with a small helper that ranks the
strongest off-diagonal feature pairs — the single most useful artifact a first
EDA pass produces.
"""

from __future__ import annotations

import pandas as pd

from .dataset import DatasetSchema, numeric_columns


def correlation_matrix(
    frame: pd.DataFrame,
    schema: DatasetSchema | None = None,
) -> pd.DataFrame:
    """Return the Pearson correlation matrix of the numeric columns.

    Args:
        frame: Dataset to analyze (should be cleaned of NaNs first).
        schema: Optional schema; defaults to :class:`DatasetSchema`.

    Returns:
        A square DataFrame of pairwise correlations, columns/rows in schema
        order.
    """
    schema = schema or DatasetSchema()
    cols = numeric_columns(frame, schema)
    return frame[cols].corr(method="pearson")


def strongest_pairs(
    matrix: pd.DataFrame,
    top_n: int = 3,
) -> list[tuple[str, str, float]]:
    """Return the ``top_n`` most strongly correlated distinct column pairs.

    Ranking is by absolute correlation; the sign is preserved in the returned
    value. Each unordered pair appears once.

    Args:
        matrix: A square correlation matrix (e.g. from :func:`correlation_matrix`).
        top_n: Maximum number of pairs to return.

    Returns:
        A list of ``(column_a, column_b, correlation)`` tuples, descending by
        absolute correlation.

    Raises:
        ValueError: If ``top_n`` is negative.
    """
    if top_n < 0:
        raise ValueError("top_n must be non-negative")
    columns = list(matrix.columns)
    pairs: list[tuple[str, str, float]] = []
    for i, col_a in enumerate(columns):
        for col_b in columns[i + 1 :]:
            pairs.append((col_a, col_b, float(matrix.loc[col_a, col_b])))
    pairs.sort(key=lambda item: abs(item[2]), reverse=True)
    return pairs[:top_n]
