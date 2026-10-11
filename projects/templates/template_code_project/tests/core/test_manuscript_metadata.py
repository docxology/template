"""Real Source census/call capture, without constructing native ownership."""

from __future__ import annotations

import os
from pathlib import Path

from template_code_project.core.manuscript_variables import _build_timestamp, _count_output_artifacts


def test_actual_census_keeps_registered_basename_and_ordinary_counts(tmp_path: Path) -> None:
    figures = tmp_path / "output/figures"
    figures.mkdir(parents=True)
    (figures / "convergence_plot.png").write_bytes(b"image DATA")
    (figures / "stability_analysis.png").mkdir()
    (figures / "downstream-render.png").write_bytes(b"not Stage02")
    data = tmp_path / "output/data"
    data.mkdir()
    (data / "optimization_results.csv").write_bytes(b"CSV DATA")
    (data / "manuscript_metadata.json").write_bytes(b"not a counted analysis name")
    observed: dict = {}
    ordinary = _count_output_artifacts(tmp_path)
    assert (
        _count_output_artifacts(tmp_path, observation=observed) == ordinary == {"figures": 1, "data": 1, "reports": 0}
    )
    assert sum(len(row["records"]) for row in observed["artifact_census"]) == 16
    rows = {entry["path"]: entry for row in observed["artifact_census"] for entry in row["records"]}
    assert rows["output/figures/convergence_plot.png"]["kind"] == "regular"
    assert rows["output/figures/stability_analysis.png"]["kind"] == "directory"
    assert rows["output/reports/stability_analysis.json"]["kind"] == "absent"
    assert "output/data/manuscript_metadata.json" not in rows


def test_actual_type_capture_retains_symlink_rather_than_regular_alias(tmp_path: Path) -> None:
    figures = tmp_path / "output/figures"
    figures.mkdir(parents=True)
    target = figures / "target.png"
    target.write_bytes(b"DATA")
    (figures / "convergence_plot.png").symlink_to(target)
    observed: dict = {}
    assert _count_output_artifacts(tmp_path, observation=observed) == _count_output_artifacts(tmp_path)
    entry = next(
        row for row in observed["artifact_census"][0]["records"] if row["path"].endswith("convergence_plot.png")
    )
    assert entry["kind"] == "symlink" and entry["is_file"] is True


def test_actual_timestamp_capture_preserves_source_epoch_and_formatter() -> None:
    previous = os.environ.get("SOURCE_DATE_EPOCH")
    try:
        os.environ["SOURCE_DATE_EPOCH"] = " 0 "
        observed: dict = {}
        assert _build_timestamp(observation=observed) == _build_timestamp() == "1970-01-01T00:00:00Z"
        assert observed["timestamp"]["source_date_epoch"] == " 0 "
        assert observed["timestamp"]["returned_utc"] == "1970-01-01T00:00:00Z"
        assert observed["timestamp"]["before_utc"] <= observed["timestamp"]["after_utc"]
    finally:
        if previous is None:
            os.environ.pop("SOURCE_DATE_EPOCH", None)
        else:
            os.environ["SOURCE_DATE_EPOCH"] = previous
