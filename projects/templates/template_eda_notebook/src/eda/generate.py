"""Deterministic synthetic dataset generation for the EDA exemplar.

This module produces a *sibling* of the shipped fixture
(``data/measurements.csv``) with the same documented contract — 120 rows,
three groups, mild group structure in height, positive height--weight
correlation, and a handful of blank numeric cells — rather than a byte-exact
clone. The original fixture's exact random draw order is not recoverable, so
the generator reproduces the fixture's *family* (schema, size, missingness
pattern, correlation sign structure, and broad statistics) from a fixed seed,
which is what a forked project needs to regenerate a deterministic dataset.

Like the rest of ``src/eda``, this module is pure: it returns a DataFrame and
performs no file I/O and no plotting.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

DEFAULT_N_ROWS = 120
DEFAULT_SEED = 42

GROUPS = ("alpha", "beta", "gamma")

# Mild between-group structure in height (means within ~2 cm), matching the
# "close but not equal" group structure described in manuscript 03_results.
_GROUP_HEIGHT_MEANS = {"alpha": 169.5, "beta": 171.2, "gamma": 170.2}
_HEIGHT_SD = 9.5

# weight = mean + slope * (height - mean_height) + noise, chosen so the
# generated family shows the shipped fixture's r ≈ +0.72 / std ≈ 8.7.
_WEIGHT_MEAN = 72.1
_WEIGHT_HEIGHT_SLOPE = 0.667
_WEIGHT_NOISE_SD = 6.06

# resting_hr = mean - anti_slope * (height - mean_height) + noise, giving the
# shipped fixture's small negative correlations (r ≈ −0.12 with height,
# r ≈ −0.08 with weight).
_RESTING_MEAN = 64.2
_RESTING_HEIGHT_ANTI_SLOPE = 0.064
_RESTING_NOISE_SD = 5.1

# Missing-cell counts per numeric column, mirroring the shipped fixture
# (1 height, 2 weight, 1 resting → 4 incomplete rows).
_MISSING_PER_COLUMN = {"height_cm": 1, "weight_kg": 2, "resting_hr_bpm": 1}


def generate_measurements(
    n_rows: int = DEFAULT_N_ROWS,
    seed: int = DEFAULT_SEED,
) -> pd.DataFrame:
    """Return a deterministic synthetic dataset matching the shipped contract.

    Parameters
    ----------
    n_rows:
        Number of subject rows. The shipped fixture uses 120.
    seed:
        NumPy ``default_rng`` seed. The same seed always reproduces the same
        frame on the same NumPy version.

    Returns
    -------
    pd.DataFrame
        Columns ``subject_id``, ``group``, ``height_cm``, ``weight_kg``,
        ``resting_hr_bpm`` with the same schema, size, missingness pattern,
        and correlation sign structure as ``data/measurements.csv``.
    """
    rng = np.random.default_rng(seed)
    group_labels = rng.choice(list(GROUPS), size=n_rows)

    heights = np.array([rng.normal(_GROUP_HEIGHT_MEANS[group], _HEIGHT_SD) for group in group_labels])
    mean_height = heights.mean() if n_rows else 0.0
    weights = (
        _WEIGHT_MEAN + _WEIGHT_HEIGHT_SLOPE * (heights - mean_height) + rng.normal(0.0, _WEIGHT_NOISE_SD, size=n_rows)
    )
    resting = (
        _RESTING_MEAN
        - _RESTING_HEIGHT_ANTI_SLOPE * (heights - mean_height)
        + rng.normal(0.0, _RESTING_NOISE_SD, size=n_rows)
    )

    frame = pd.DataFrame(
        {
            "subject_id": [f"S{i:03d}" for i in range(n_rows)],
            "group": group_labels,
            "height_cm": heights,
            "weight_kg": weights,
            "resting_hr_bpm": resting,
        }
    )
    frame["subject_id"] = frame["subject_id"].astype("string")
    frame["group"] = frame["group"].astype("string")

    for column, missing_count in _MISSING_PER_COLUMN.items():
        if n_rows == 0:
            continue
        positions = rng.choice(n_rows, size=missing_count, replace=False)
        frame.loc[positions, column] = np.nan

    return frame
