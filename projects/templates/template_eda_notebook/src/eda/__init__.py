"""Exploratory data analysis (EDA) primitives for the notebook exemplar.

This subpackage holds the *tested* EDA logic that the walkthrough notebook
(`notebooks/eda_walkthrough.ipynb`) and the thin analysis scripts call. It is
deliberately self-contained: it imports only ``numpy`` / ``pandas`` and never
imports ``infrastructure.*`` or any sibling project, so the library stays
forkable and obeys the no-cross-project-import drift rule.

The public surface is re-exported from ``src.__init__`` so callers can write
``from src import load_dataset`` regardless of internal module layout.
"""

from __future__ import annotations

from .cleaning import CleaningReport, clean_dataset, normalize_numeric
from .correlation import correlation_matrix, strongest_pairs
from .dataset import DatasetSchema, default_dataset_path, load_dataset, numeric_columns
from .figures import (
    CorrelationFigureData,
    GroupCountFigureData,
    HistogramFigureData,
    correlation_heatmap_data,
    group_count_data,
    histogram_data,
)
from .statistics import ColumnSummary, group_means, summary_statistics

__all__ = [
    # dataset
    "DatasetSchema",
    "load_dataset",
    "default_dataset_path",
    "numeric_columns",
    # cleaning
    "CleaningReport",
    "clean_dataset",
    "normalize_numeric",
    # statistics
    "ColumnSummary",
    "summary_statistics",
    "group_means",
    # correlation
    "correlation_matrix",
    "strongest_pairs",
    # figure-data preparers
    "HistogramFigureData",
    "CorrelationFigureData",
    "GroupCountFigureData",
    "histogram_data",
    "correlation_heatmap_data",
    "group_count_data",
]
