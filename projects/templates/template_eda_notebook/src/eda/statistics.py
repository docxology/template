"""Summary statistics for the EDA exemplar.

Computes per-column descriptive statistics and per-group means using real
``pandas`` aggregation — no approximations and no hidden state.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .dataset import DatasetSchema, numeric_columns


@dataclass(frozen=True)
class ColumnSummary:
    """Descriptive statistics for one numeric column.

    Attributes:
        column: Column name.
        count: Number of non-missing observations.
        mean: Arithmetic mean.
        std: Sample standard deviation (ddof=1).
        minimum: Smallest observed value.
        median: 50th percentile.
        maximum: Largest observed value.
    """

    column: str
    count: int
    mean: float
    std: float
    minimum: float
    median: float
    maximum: float


def summary_statistics(
    frame: pd.DataFrame,
    schema: DatasetSchema | None = None,
) -> list[ColumnSummary]:
    """Return descriptive statistics for each numeric column.

    Args:
        frame: Dataset to summarize.
        schema: Optional schema; defaults to :class:`DatasetSchema`.

    Returns:
        One :class:`ColumnSummary` per numeric column, in schema order.
    """
    schema = schema or DatasetSchema()
    summaries: list[ColumnSummary] = []
    for column in numeric_columns(frame, schema):
        series = frame[column].dropna()
        summaries.append(
            ColumnSummary(
                column=column,
                count=int(series.count()),
                mean=float(series.mean()),
                std=float(series.std(ddof=1)),
                minimum=float(series.min()),
                median=float(series.median()),
                maximum=float(series.max()),
            )
        )
    return summaries


def group_means(
    frame: pd.DataFrame,
    schema: DatasetSchema | None = None,
) -> pd.DataFrame:
    """Return the mean of each numeric column grouped by the categorical column.

    Args:
        frame: Dataset containing the grouping column.
        schema: Optional schema; defaults to :class:`DatasetSchema`.

    Returns:
        A DataFrame indexed by group value with one column per numeric feature,
        sorted by group name for deterministic output.

    Raises:
        KeyError: If the grouping column is absent from ``frame``.
    """
    schema = schema or DatasetSchema()
    if schema.group_column not in frame.columns:
        raise KeyError(f"group column {schema.group_column!r} not in frame")
    cols = numeric_columns(frame, schema)
    grouped = frame.groupby(schema.group_column)[cols].mean()
    return grouped.sort_index()
