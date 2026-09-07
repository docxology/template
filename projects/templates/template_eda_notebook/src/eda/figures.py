"""Figure-data preparers for the EDA exemplar.

These functions compute *plot-ready* data structures (bin edges, counts, matrix
values) but never import matplotlib. Rendering happens in the thin scripts under
``scripts/`` — keeping plotting out of ``src/`` is the thin-orchestrator
contract and makes every preparer trivially testable without a display backend.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace

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


@dataclass(frozen=True)
class EdaFigureSpec:
    """Provenance metadata for one generated EDA figure."""

    label: str
    filename: str
    caption: str
    generated_by: str
    alt_text: str


FIGURE_REGISTRY_SCHEMA = "template-eda-notebook-figure-registry-v1"
CORRELATION_COLOR_LIMITS = (-1.0, 1.0)
EDA_FIGURE_SPECS: tuple[EdaFigureSpec, ...] = (
    EdaFigureSpec(
        label="fig:height_histogram",
        filename="height_histogram.png",
        caption="Height distribution computed from complete-case histogram bins.",
        generated_by="scripts.eda_analysis.run_eda",
        alt_text=(
            "Histogram whose bars encode complete-case counts by height bin; missing observations are excluded "
            "and the display does not imply a fitted distribution."
        ),
    ),
    EdaFigureSpec(
        label="fig:group_counts",
        filename="group_counts.png",
        caption="Complete-case row counts for each sorted study group.",
        generated_by="scripts.eda_analysis.run_eda",
        alt_text=(
            "Bar chart whose heights encode complete-case row counts for sorted study groups; counts describe "
            "sample composition, not group effects."
        ),
    ),
    EdaFigureSpec(
        label="fig:correlation_heatmap",
        filename="correlation_heatmap.png",
        caption="Pearson feature-correlation matrix rendered on a fixed minus-one-to-one scale.",
        generated_by="scripts.eda_analysis.run_eda",
        alt_text=(
            "Pearson feature-correlation matrix encoded on a fixed minus-one-to-one diverging color scale; "
            "associations are descriptive and do not establish causation."
        ),
    ),
)
_FIGURE_SPEC_BY_LABEL = {spec.label: spec for spec in EDA_FIGURE_SPECS}


def eda_figure_spec(label: str) -> EdaFigureSpec:
    """Return the canonical EDA figure specification for ``label``."""
    try:
        return _FIGURE_SPEC_BY_LABEL[label]
    except KeyError as exc:
        raise KeyError(f"unknown EDA figure label: {label!r}") from exc


def eda_figure_specs_for_data(
    histogram: HistogramFigureData,
    heatmap: CorrelationFigureData,
    groups: GroupCountFigureData,
) -> tuple[EdaFigureSpec, ...]:
    """Bind figure alternate text to the plot-ready data rendered in one run.

    The immutable specifications above carry only encoding and interpretation
    boundaries. This builder injects run-specific values from the same three
    objects the thin analysis script passes to matplotlib, preventing a copied
    exemplar or changed input dataset from retaining stale fixture numbers.

    Args:
        histogram: Histogram bin edges and counts used for the height chart.
        heatmap: Labels and Pearson values used for the correlation heatmap.
        groups: Labels and counts used for the group-count chart.

    Returns:
        A complete specification tuple with data-derived alternate text.
    """
    alt_by_label = {
        "fig:height_histogram": _histogram_alt_text(histogram),
        "fig:correlation_heatmap": _correlation_alt_text(heatmap),
        "fig:group_counts": _group_count_alt_text(groups),
    }
    return tuple(replace(spec, alt_text=alt_by_label[spec.label]) for spec in EDA_FIGURE_SPECS)


def _histogram_alt_text(data: HistogramFigureData) -> str:
    if len(data.edges) != len(data.counts) + 1:
        raise ValueError(f"histogram edge/count mismatch: {len(data.edges)} edges for {len(data.counts)} counts")
    if not data.counts:
        return f"Empty histogram for {data.column}: no bins were supplied. No distribution can be described."

    observations = sum(data.counts)
    lower, upper = data.edges[0], data.edges[-1]
    if observations == 0:
        return (
            f"{len(data.counts)}-bin histogram for {data.column} from {_format_number(lower)} to "
            f"{_format_number(upper)} with every bar at zero because no non-missing observations were "
            "available; no distribution can be inferred."
        )

    peak = max(data.counts)
    peak_bins = [
        f"{_format_number(data.edges[index])} to {_format_number(data.edges[index + 1])}"
        for index, count in enumerate(data.counts)
        if count == peak
    ]
    peak_description = ", ".join(peak_bins)
    return (
        f"{len(data.counts)}-bin histogram of {observations} non-missing {data.column} observations from "
        f"{_format_number(lower)} to {_format_number(upper)}. The tallest bar count is {peak} in "
        f"{peak_description}. Bars encode counts; missing values are excluded and no fitted distribution "
        "is implied."
    )


def _correlation_alt_text(data: CorrelationFigureData) -> str:
    size = len(data.labels)
    if len(data.values) != size or any(len(row) != size for row in data.values):
        shape = [len(row) for row in data.values]
        raise ValueError(f"correlation matrix shape does not match {size} labels: row lengths {shape}")
    if size == 0:
        return (
            "Empty Pearson correlation heatmap: no numeric features were available, so no associations "
            "can be described."
        )

    pairs: list[str] = []
    for row in range(size):
        for column in range(row + 1, size):
            value = data.values[row][column]
            rendered = _format_number(value) if math.isfinite(value) else "undefined"
            pairs.append(f"{data.labels[row]} with {data.labels[column]}: {rendered}")

    diagonal = [data.values[index][index] for index in range(size)]
    if all(math.isfinite(value) and math.isclose(value, 1.0, abs_tol=1e-12) for value in diagonal):
        diagonal_description = "The diagonal is 1.00."
    else:
        values = [_format_number(value) if math.isfinite(value) else "undefined" for value in diagonal]
        diagonal_description = f"Diagonal values are {', '.join(values)}."

    if pairs:
        pair_description = "Off-diagonal pairs are " + "; ".join(pairs) + "."
    else:
        pair_description = "There are no off-diagonal feature pairs."
    return (
        f"{size}-by-{size} Pearson correlation heatmap for {', '.join(data.labels)} on a fixed "
        f"minus-one-to-one diverging scale. {diagonal_description} {pair_description} Correlations are "
        "descriptive and do not establish causation."
    )


def _group_count_alt_text(data: GroupCountFigureData) -> str:
    if len(data.labels) != len(data.counts):
        raise ValueError(f"group label/count mismatch: {len(data.labels)} labels for {len(data.counts)} counts")
    if not data.labels:
        return (
            "Empty group-count bar chart: no complete-case rows or group labels were available; no group "
            "comparison can be made."
        )

    bars = "; ".join(f"{label}: {count}" for label, count in zip(data.labels, data.counts))
    largest = max(data.counts)
    smallest = min(data.counts)
    largest_labels = [label for label, count in zip(data.labels, data.counts) if count == largest]
    smallest_labels = [label for label, count in zip(data.labels, data.counts) if count == smallest]
    return (
        f"{len(data.labels)} bars encode complete-case row counts: {bars}. Largest count {largest} occurs "
        f"for {', '.join(largest_labels)}; smallest count {smallest} occurs for {', '.join(smallest_labels)}. "
        "These counts describe sample composition, not group effects."
    )


def _format_number(value: float) -> str:
    """Format a plotted numeric value compactly without hiding non-finite data."""
    if not math.isfinite(value):
        return "undefined"
    if math.isclose(value, 0.0, abs_tol=5e-13):
        value = 0.0
    return f"{value:.2f}"


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
