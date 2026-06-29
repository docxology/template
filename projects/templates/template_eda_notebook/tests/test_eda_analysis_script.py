"""Smoke test for the thin EDA analysis script (no mocks; real files)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _PROJECT_ROOT / "scripts" / "eda_analysis.py"


def _load_script_module():
    """Import the script as a module so its run_eda() can be called directly."""
    if str(_PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(_PROJECT_ROOT))
    spec = importlib.util.spec_from_file_location("eda_analysis_under_test", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestEdaAnalysisScript:
    """run_eda writes the expected artifacts under a temp project root."""

    def test_writes_figures_and_summary(self, tmp_path):
        module = _load_script_module()
        written = module.run_eda(project_root=tmp_path)
        # Three figures + one summary CSV.
        assert len(written) == 4
        for path in written:
            assert path.exists()
            assert path.stat().st_size > 0

    def test_summary_csv_has_header_and_three_rows(self, tmp_path):
        module = _load_script_module()
        module.run_eda(project_root=tmp_path)
        summary = tmp_path / "output" / "data" / "summary_statistics.csv"
        lines = summary.read_text(encoding="utf-8").strip().splitlines()
        assert lines[0] == "column,count,mean,std,minimum,median,maximum"
        # One row per numeric column.
        assert len(lines) == 4

    def test_figures_are_pngs(self, tmp_path):
        module = _load_script_module()
        module.run_eda(project_root=tmp_path)
        figures_dir = tmp_path / "output" / "figures"
        names = sorted(p.name for p in figures_dir.glob("*.png"))
        assert names == [
            "correlation_heatmap.png",
            "group_counts.png",
            "height_histogram.png",
        ]
