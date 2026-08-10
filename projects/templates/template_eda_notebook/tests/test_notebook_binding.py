"""Notebook/source binding and exact fixture-statistic regression controls."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.eda.cleaning import clean_dataset
from src.eda.dataset import load_dataset
from src.eda.notebook_binding import validate_binding
from src.eda.statistics import summary_statistics


PROJECT = Path(__file__).resolve().parents[1]


def test_checked_in_notebook_binding_receipt_is_current():
    receipt = json.loads((PROJECT / "data" / "notebook_binding.json").read_text(encoding="utf-8"))
    assert validate_binding(receipt, PROJECT) == ()


def test_notebook_binding_rejects_changed_cell(tmp_path):
    receipt = json.loads((PROJECT / "data" / "notebook_binding.json").read_text(encoding="utf-8"))
    notebook = PROJECT / receipt["notebook"]["path"]
    notebook_payload = json.loads(notebook.read_text(encoding="utf-8"))
    next(cell for cell in notebook_payload["cells"] if cell["cell_type"] == "code")["source"].append("# changed\n")
    receipt["notebook"]["path"] = "notebook.ipynb"
    (tmp_path / "notebook.ipynb").write_text(json.dumps(notebook_payload), encoding="utf-8")
    for source in receipt["sources"]:
        source_path = PROJECT / source["path"]
        destination = tmp_path / source["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source_path.read_bytes())
    issues = validate_binding(receipt, tmp_path)
    assert "notebook code-cell digest drift" in issues


def test_fixture_statistics_have_exact_source_bound_values():
    cleaned, report = clean_dataset(load_dataset())
    assert (report.rows_in, report.rows_out, report.dropped) == (120, 116, 4)
    summaries = {summary.column: summary for summary in summary_statistics(cleaned)}
    assert summaries["height_cm"].count == 116
    assert summaries["height_cm"].mean == pytest.approx(170.304655, abs=1e-6)
    assert summaries["weight_kg"].std == pytest.approx(8.739035, abs=1e-6)
    assert summaries["resting_hr_bpm"].median == pytest.approx(64.235, abs=1e-6)
