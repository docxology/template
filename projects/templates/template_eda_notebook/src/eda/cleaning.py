"""Cleaning and normalization for the EDA exemplar.

Two explicit, side-effect-free transforms:

* :func:`clean_dataset` — drop rows with missing numeric values and report how
  many were removed (no silent imputation; missingness is surfaced, not hidden).
* :func:`normalize_numeric` — z-score standardize numeric columns so features on
  different scales (cm vs kg vs bpm) can be compared and correlated meaningfully.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .dataset import DatasetSchema, numeric_columns


@dataclass(frozen=True)
class CleaningReport:
    """Summary of what :func:`clean_dataset` removed.

    Attributes:
        rows_in: Row count before cleaning.
        rows_out: Row count after dropping incomplete rows.
        dropped: Number of rows removed because of missing numeric values.
    """

    rows_in: int
    rows_out: int
    dropped: int


def clean_dataset(
    frame: pd.DataFrame,
    schema: DatasetSchema | None = None,
) -> tuple[pd.DataFrame, CleaningReport]:
    """Drop rows that are missing any numeric feature value.

    Args:
        frame: Raw dataset (numeric columns may contain ``NaN``).
        schema: Optional schema; defaults to :class:`DatasetSchema`.

    Returns:
        ``(cleaned_frame, report)`` where ``cleaned_frame`` has the index reset
        and ``report`` records how many rows were dropped.
    """
    schema = schema or DatasetSchema()
    cols = numeric_columns(frame, schema)
    rows_in = int(len(frame))
    cleaned = frame.dropna(subset=cols).reset_index(drop=True)
    rows_out = int(len(cleaned))
    return cleaned, CleaningReport(rows_in=rows_in, rows_out=rows_out, dropped=rows_in - rows_out)


def normalize_numeric(
    frame: pd.DataFrame,
    schema: DatasetSchema | None = None,
) -> pd.DataFrame:
    """Z-score standardize numeric columns (mean 0, sample std 1).

    Non-numeric columns pass through unchanged. A constant column (zero
    variance) is left as all-zeros rather than producing ``inf``/``NaN``.

    Args:
        frame: Dataset to normalize (should already be cleaned of NaNs).
        schema: Optional schema; defaults to :class:`DatasetSchema`.

    Returns:
        A new DataFrame; the input is not mutated.
    """
    schema = schema or DatasetSchema()
    cols = numeric_columns(frame, schema)
    out = frame.copy()
    for column in cols:
        series = out[column]
        std = series.std(ddof=1)
        mean = series.mean()
        if std == 0 or pd.isna(std):
            out[column] = series * 0.0
        else:
            out[column] = (series - mean) / std
    return out
