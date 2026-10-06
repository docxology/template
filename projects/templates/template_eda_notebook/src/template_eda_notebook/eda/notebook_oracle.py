"""Independent NumPy/Pandas oracle for observations from a real notebook kernel.

This reference deliberately does not import the EDA implementation or its schema:
the fixture contract and numerical definitions remain an independent check.
"""

from __future__ import annotations

import math
from itertools import combinations
from typing import Any

import numpy as np
import pandas as pd


FEATURES = ("height_cm", "weight_kg", "resting_hr_bpm")


def _frame_payload(frame: pd.DataFrame) -> dict[str, Any]:
    return {"columns": list(frame.columns), "index": list(frame.index), "data": frame.values.tolist()}


def reference_observations(raw: pd.DataFrame) -> dict[str, Any]:
    """Compute the walkthrough reference without calling its implementation."""
    source = raw.copy()
    for column in FEATURES:
        source[column] = pd.to_numeric(source[column], errors="coerce")
    clean = source.dropna(subset=list(FEATURES)).reset_index(drop=True)
    values = clean[list(FEATURES)].to_numpy(dtype=float)
    summaries = []
    for index, column in enumerate(FEATURES):
        vector = values[:, index]
        summaries.append(
            {
                "column": column,
                "count": len(vector),
                "mean": float(np.mean(vector)),
                "std": float(np.std(vector, ddof=1)),
                "minimum": float(np.min(vector)),
                "median": float(np.median(vector)),
                "maximum": float(np.max(vector)),
            }
        )
    labels = sorted(clean["group"].unique().tolist())
    means = pd.DataFrame(
        [values[clean["group"].to_numpy() == label].mean(axis=0) for label in labels],
        index=labels,
        columns=list(FEATURES),
    )
    matrix = np.corrcoef(values, rowvar=False)
    pairs = [(FEATURES[a], FEATURES[b], float(matrix[a, b])) for a, b in combinations(range(len(FEATURES)), 2)]
    pairs.sort(key=lambda row: abs(row[2]), reverse=True)
    counts, edges = np.histogram(values[:, 0], bins=10)
    normalized = pd.DataFrame(
        (values - values.mean(axis=0)) / values.std(axis=0, ddof=1),
        columns=list(FEATURES),
    )
    return {
        "report": {"rows_in": len(raw), "rows_out": len(clean), "dropped": len(raw) - len(clean)},
        "missing": {column: int(source[column].isna().sum()) for column in source.columns},
        "clean": _frame_payload(clean),
        "summaries": summaries,
        "means": _frame_payload(means),
        "matrix": {"columns": list(FEATURES), "index": list(FEATURES), "data": matrix.tolist()},
        "pairs": [list(pair) for pair in pairs],
        "histogram": {"column": FEATURES[0], "counts": counts.tolist(), "edges": edges.tolist()},
        "heatmap": {"labels": list(FEATURES), "values": matrix.tolist()},
        "groups": {"labels": labels, "counts": [int((clean["group"] == label).sum()) for label in labels]},
        "normalized": _frame_payload(normalized),
    }


def _differences(expected: Any, actual: Any, path: str) -> list[str]:
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or expected.keys() != actual.keys():
            return [f"{path}: observation keys differ"]
        return [issue for key in expected for issue in _differences(expected[key], actual[key], f"{path}.{key}")]
    if isinstance(expected, list):
        if not isinstance(actual, list) or len(expected) != len(actual):
            return [f"{path}: observation dimensions differ"]
        return [issue for i, value in enumerate(expected) for issue in _differences(value, actual[i], f"{path}[{i}]")]
    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        # A non-finite value never establishes agreement with the finite fixture.
        if isinstance(actual, (int, float)) and not isinstance(actual, bool):
            if math.isfinite(actual) and math.isclose(expected, actual, rel_tol=1e-12, abs_tol=1e-12):
                return []
    elif expected == actual:
        return []
    return [f"{path}: expected {expected!r}, observed {actual!r}"]


def verify_observations(observations: dict[str, Any], raw: pd.DataFrame) -> tuple[str, ...]:
    """Return numerical/shape disagreements with the independent fixture oracle."""
    return tuple(_differences(reference_observations(raw), observations, "notebook"))


__all__ = ["reference_observations", "verify_observations"]
