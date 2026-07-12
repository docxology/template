"""Tests for parameter sweep CSV I/O."""

from __future__ import annotations

from pathlib import Path

import pytest

from analytical.sweep_io import read_parameter_sweep, summarize_sweep_file, summarize_sweep_rows


def test_read_parameter_sweep_parses_fixture(tmp_path: Path) -> None:
    csv_path = tmp_path / "parameter_sweep.csv"
    csv_path.write_text(
        "lambda,closed_form_mi,empirical_mi\n0.0,0.1,0.11\n0.5,0.2,0.19\n",
        encoding="utf-8",
    )
    rows = read_parameter_sweep(csv_path)
    assert rows == [
        {"lambda": 0.0, "closed_form_mi": 0.1, "empirical_mi": 0.11},
        {"lambda": 0.5, "closed_form_mi": 0.2, "empirical_mi": 0.19},
    ]


def test_read_parameter_sweep_returns_empty_list_for_missing_file(tmp_path: Path) -> None:
    """A missing CSV should return an empty list, not raise."""
    rows = read_parameter_sweep(tmp_path / "nonexistent.csv")
    assert rows == []


def test_summarize_sweep_rows_computes_residuals() -> None:
    rows = [
        {"lambda": 0.0, "closed_form_mi": 0.1, "empirical_mi": 0.11},
        {"lambda": 0.5, "closed_form_mi": 0.2, "empirical_mi": 0.19},
    ]
    summary = summarize_sweep_rows(rows)
    assert summary["grid_points"] == 2
    assert summary["max_residual"] == pytest.approx(0.01)
    assert summary["argmax_lambda"] == 0.5


def test_summarize_sweep_rows_empty_returns_zero_defaults() -> None:
    """An empty rows list should return a zeroed-out summary without raising."""
    summary = summarize_sweep_rows([])
    assert summary["grid_points"] == 0
    assert summary["max_residual"] == 0.0
    assert summary["rmse_mi"] == 0.0
    assert summary["argmax_lambda"] == 0.0


def test_summarize_sweep_file_delegates_to_rows(tmp_path: Path) -> None:
    """summarize_sweep_file must agree with summarize_sweep_rows on the same data."""
    csv_path = tmp_path / "parameter_sweep.csv"
    csv_path.write_text(
        "lambda,closed_form_mi,empirical_mi\n1.0,0.3,0.31\n2.0,0.6,0.59\n",
        encoding="utf-8",
    )
    summary = summarize_sweep_file(csv_path)
    assert summary["grid_points"] == 2
    assert summary["max_residual"] == pytest.approx(0.01)


def test_summarize_sweep_file_missing_path_returns_empty_defaults(tmp_path: Path) -> None:
    """summarize_sweep_file on a missing path must return the empty default dict."""
    summary = summarize_sweep_file(tmp_path / "no_file.csv")
    assert summary["grid_points"] == 0
