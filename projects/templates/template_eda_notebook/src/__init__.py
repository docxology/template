"""Exploratory data analysis (EDA) notebook exemplar — tested library surface.

This project demonstrates the *computational-notebook* research archetype: an
EDA walkthrough notebook (`notebooks/eda_walkthrough.ipynb`) that imports a
small, fully-tested library rather than burying logic in notebook cells. The
notebook is the entry point a researcher reaches for first; the library is what
keeps that exploration reproducible, covered, and reusable.

All EDA logic lives in the ``src.eda`` subpackage and is re-exported here so
callers (notebook cells, thin scripts, tests) can write
``from src import load_dataset, summary_statistics``.
"""

from .eda import (
    CORRELATION_COLOR_LIMITS,
    EDA_FIGURE_SPECS,
    FIGURE_REGISTRY_SCHEMA,
    CleaningReport,
    ColumnSummary,
    CorrelationFigureData,
    DatasetSchema,
    EdaFigureSpec,
    GroupCountFigureData,
    HistogramFigureData,
    clean_dataset,
    correlation_heatmap_data,
    correlation_matrix,
    default_dataset_path,
    eda_figure_spec,
    group_count_data,
    group_means,
    histogram_data,
    load_dataset,
    normalize_numeric,
    numeric_columns,
    strongest_pairs,
    summary_statistics,
)

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
    "EdaFigureSpec",
    "CORRELATION_COLOR_LIMITS",
    "EDA_FIGURE_SPECS",
    "FIGURE_REGISTRY_SCHEMA",
    "histogram_data",
    "correlation_heatmap_data",
    "group_count_data",
    "eda_figure_spec",
]
