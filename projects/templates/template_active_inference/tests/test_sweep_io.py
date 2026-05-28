"""Tests for parameter sweep CSV I/O."""

from __future__ import annotations

from pathlib import Path

import pytest

from analytical.sweep_io import read_parameter_sweep, summarize_sweep_rows


def test_read_parameter_sweep_parses_fixture(tmp_path: Path) -> None:
    csv_path = tmp_path / "parameter_sweep.csv"
    csv_path.write_text(
        "lambda,closed_form_mi,empirical_mi\n"
        "0.0,0.1,0.11\n"
        "0.5,0.2,0.19\n",
        encoding="utf-8",
    )
    rows = read_parameter_sweep(csv_path)
    assert rows == [
        {"lambda": 0.0, "closed_form_mi": 0.1, "empirical_mi": 0.11},
        {"lambda": 0.5, "closed_form_mi": 0.2, "empirical_mi": 0.19},
    ]


def test_summarize_sweep_rows_computes_residuals() -> None:
    rows = [
        {"lambda": 0.0, "closed_form_mi": 0.1, "empirical_mi": 0.11},
        {"lambda": 0.5, "closed_form_mi": 0.2, "empirical_mi": 0.19},
    ]
    summary = summarize_sweep_rows(rows)
    assert summary["grid_points"] == 2
    assert summary["max_residual"] == pytest.approx(0.01)
    assert summary["argmax_lambda"] == 0.5
