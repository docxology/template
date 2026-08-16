"""Smoke test for the thin EDA analysis script (no mocks; real files)."""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

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


def _current_specs(module):
    cleaned, _ = module.clean_dataset(module.load_dataset())
    return module.eda_figure_specs_for_data(
        module.histogram_data(cleaned, "height_cm", bins=10),
        module.correlation_heatmap_data(cleaned),
        module.group_count_data(cleaned),
    )


class TestEdaAnalysisScript:
    """run_eda writes the expected artifacts under a temp project root."""

    def test_writes_figures_and_summary(self, tmp_path):
        module = _load_script_module()
        written = module.run_eda(project_root=tmp_path)
        # Three figures + one summary CSV + one figure registry.
        assert len(written) == 5
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

    def test_registry_binds_all_manuscript_labels_to_generated_files(self, tmp_path):
        module = _load_script_module()
        written = module.run_eda(project_root=tmp_path)
        registry = tmp_path / "output" / "figures" / "figure_registry.json"
        payload = json.loads(registry.read_text(encoding="utf-8"))

        assert registry in written
        assert {record["label"]: record["filename"] for record in payload["figures"]} == {
            "fig:correlation_heatmap": "correlation_heatmap.png",
            "fig:group_counts": "group_counts.png",
            "fig:height_histogram": "height_histogram.png",
        }
        assert all((registry.parent / record["filename"]).is_file() for record in payload["figures"])
        records = {record["label"]: record for record in payload["figures"]}
        references: set[str] = set()
        for path in (_PROJECT_ROOT / "manuscript").glob("*.md"):
            if path.name in {"AGENTS.md", "README.md"}:
                continue
            references.update(re.findall(r"\{#(fig:[A-Za-z0-9_:-]+)\}", path.read_text(encoding="utf-8")))
        assert references == set(records)
        assert all(records[label]["metadata"]["alt_text"].strip() for label in references)
        expected_alt = {spec.label: spec.alt_text for spec in _current_specs(module)}
        assert {label: records[label]["metadata"]["alt_text"] for label in references} == expected_alt

    def test_incomplete_figure_set_cannot_write_registry(self, tmp_path):
        module = _load_script_module()
        module.run_eda(project_root=tmp_path)
        figures = tmp_path / "output" / "figures"
        bad_registry = tmp_path / "negative" / "figure_registry.json"

        with pytest.raises(ValueError, match="missing generated figure file"):
            module.write_generated_figure_registry(
                bad_registry,
                _current_specs(module),
                [figures / "height_histogram.png", figures / "group_counts.png"],
                schema_version=module.FIGURE_REGISTRY_SCHEMA,
            )

        assert not bad_registry.exists()

    def test_deleted_figure_cannot_regenerate_registry(self, tmp_path):
        module = _load_script_module()
        module.run_eda(project_root=tmp_path)
        figures = tmp_path / "output" / "figures"
        heatmap = figures / "correlation_heatmap.png"
        heatmap.unlink()

        with pytest.raises(ValueError, match="generated figure path.*do not exist"):
            module.write_generated_figure_registry(
                tmp_path / "negative" / "figure_registry.json",
                _current_specs(module),
                [
                    figures / "height_histogram.png",
                    figures / "group_counts.png",
                    heatmap,
                ],
                schema_version=module.FIGURE_REGISTRY_SCHEMA,
            )
