"""Notebook/source binding and exact fixture-statistic regression controls."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from template_eda_notebook.eda.cleaning import clean_dataset
from template_eda_notebook.eda.dataset import load_dataset
from template_eda_notebook.eda.notebook_binding import validate_binding
from template_eda_notebook.eda.statistics import summary_statistics


PROJECT = Path(__file__).resolve().parents[1]


def test_checked_in_notebook_binding_receipt_is_current():
    receipt = json.loads((PROJECT / "data" / "notebook_binding.json").read_text(encoding="utf-8"))
    assert validate_binding(receipt, PROJECT) == ()


@pytest.mark.parametrize("changed_source", [False, True], ids=["current", "stale-source"])
def test_refresh_notebook_binding_script_runs_from_project_root(tmp_path, changed_source):
    canonical_receipt = PROJECT / "data" / "notebook_binding.json"
    canonical_before = canonical_receipt.read_bytes()
    root = tmp_path / "project"
    for name in ("src", "data", "notebooks", "scripts"):
        shutil.copytree(PROJECT / name, root / name, ignore=shutil.ignore_patterns("__pycache__"))
    receipt_path = root / "data" / "notebook_binding.json"
    before = receipt_path.read_bytes()
    admitted = json.loads(before)
    assert validate_binding(admitted, root) == ()
    canonical_sources = {row["path"]: (PROJECT / row["path"]).read_bytes() for row in admitted["sources"]}
    if changed_source:
        source = root / "src/template_eda_notebook/eda/statistics.py"
        source.write_bytes(source.read_bytes() + b"\n# Controlled source edit in the disposable producer workspace.\n")
        assert validate_binding(admitted, root) == ("source digest drift",)

    result = subprocess.run(
        [sys.executable, "scripts/refresh_notebook_binding.py"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        # 30s is too tight under heavy fleet/CI load: cold imports (pandas) plus
        # the notebook digest walk can exceed it while the script itself is fine.
        timeout=120,
    )

    assert result.returncode == 0, result.stderr
    assert str(receipt_path) in result.stdout
    refreshed = receipt_path.read_bytes()
    assert (refreshed != before) is changed_source
    assert validate_binding(json.loads(refreshed), root) == ()
    assert canonical_receipt.read_bytes() == canonical_before
    assert all((PROJECT / relative).read_bytes() == raw for relative, raw in canonical_sources.items())


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
