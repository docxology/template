"""Figure-data preparers for the EDA exemplar.

These functions compute *plot-ready* data structures (bin edges, counts, matrix
values) but never import matplotlib. Rendering happens in the thin scripts under
``scripts/`` — keeping plotting out of ``src/`` is the thin-orchestrator
contract and makes every preparer trivially testable without a display backend.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .correlation import correlation_matrix
from .dataset import DatasetSchema


@dataclass(frozen=True)
class HistogramFigureData:
    """Bin counts and edges for a single-column histogram.

    Attributes:
        column: The column the histogram describes.
        counts: Count per bin (length ``len(edges) - 1``).
        edges: Bin edges (length ``bins + 1``).
    """

    column: str
    counts: list[int]
    edges: list[float]


@dataclass(frozen=True)
class CorrelationFigureData:
    """Square matrix values plus axis labels for a correlation heatmap.

    Attributes:
        labels: Column names in row/column order.
        values: Row-major nested list of correlation values.
    """

    labels: list[str]
    values: list[list[float]]


@dataclass(frozen=True)
class GroupCountFigureData:
    """Category labels and row counts for a bar chart.

    Attributes:
        labels: Sorted group labels.
        counts: Row count per group, aligned to ``labels``.
    """

    labels: list[str]
    counts: list[int]


def histogram_data(frame: pd.DataFrame, column: str, bins: int = 10) -> HistogramFigureData:
    """Compute histogram bin counts and edges for one numeric column.

    Args:
        frame: Dataset to read from.
        column: Numeric column to bin.
        bins: Number of histogram bins (must be positive).

    Returns:
        A :class:`HistogramFigureData`.

    Raises:
        ValueError: If ``bins`` is not positive.
        KeyError: If ``column`` is absent.
    """
    if bins <= 0:
        raise ValueError("bins must be positive")
    if column not in frame.columns:
        raise KeyError(f"column {column!r} not in frame")
    values = frame[column].dropna().to_numpy(dtype=float)
    counts, edges = np.histogram(values, bins=bins)
    return HistogramFigureData(
        column=column,
        counts=[int(c) for c in counts],
        edges=[float(e) for e in edges],
    )


def correlation_heatmap_data(
    frame: pd.DataFrame,
    schema: DatasetSchema | None = None,
) -> CorrelationFigureData:
    """Compute heatmap-ready correlation values and labels.

    Args:
        frame: Dataset to analyze.
        schema: Optional schema; defaults to :class:`DatasetSchema`.

    Returns:
        A :class:`CorrelationFigureData`.
    """
    matrix = correlation_matrix(frame, schema)
    labels = list(matrix.columns)
    values = [[float(matrix.loc[r, c]) for c in labels] for r in labels]
    return CorrelationFigureData(labels=labels, values=values)


def group_count_data(
    frame: pd.DataFrame,
    schema: DatasetSchema | None = None,
) -> GroupCountFigureData:
    """Compute per-group row counts for a bar chart.

    Args:
        frame: Dataset containing the grouping column.
        schema: Optional schema; defaults to :class:`DatasetSchema`.

    Returns:
        A :class:`GroupCountFigureData`, sorted by group label.

    Raises:
        KeyError: If the grouping column is absent.
    """
    schema = schema or DatasetSchema()
    if schema.group_column not in frame.columns:
        raise KeyError(f"group column {schema.group_column!r} not in frame")
    counts = frame[schema.group_column].value_counts().sort_index()
    return GroupCountFigureData(
        labels=[str(label) for label in counts.index],
        counts=[int(c) for c in counts.to_numpy()],
    )
