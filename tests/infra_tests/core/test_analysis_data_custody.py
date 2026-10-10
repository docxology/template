"""Genuine confined filesystem refusal and retained original data controls."""

import time
from pathlib import Path

import pytest

from infrastructure.core.analysis_data_custody import capture_analysis_data, require_analysis_data
from infrastructure.core.pipeline.artifacts._inventory import iter_bounded_tree_paths


def test_complete_data_membership_and_original_bytes_survive_a_later_value_change(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "data").mkdir(parents=True)
    (project / "output/data").mkdir(parents=True)
    input_path = project / "data/input.csv"
    generated = project / "output/data/measurement.json"
    input_path.write_bytes(b"length,unit\n-2.5,mm\n")
    generated.write_bytes(b'{"length":-2.5,"unit":"mm"}')
    deadline = time.monotonic() + 30
    old = capture_analysis_data(project, run_id="real-run", stage_key="analysis:scripts/measure.py", deadline=deadline)
    assert {row["path"] for row in old["records"]} == {"data/input.csv", "output/data/measurement.json"}
    original = next(row for row in old["records"] if row["path"] == "output/data/measurement.json")
    generated.write_bytes(b'{"length":2.5,"unit":"cm"}')
    with pytest.raises(ValueError, match="differs from the complete"):
        require_analysis_data(
            old, project, run_id="real-run", stage_key="analysis:scripts/measure.py", deadline=deadline
        )
    assert (project / original["retained_path"]).read_bytes() == b'{"length":-2.5,"unit":"mm"}'


def test_actual_extra_data_member_cannot_be_omitted_from_the_source_selector(tmp_path: Path) -> None:
    (tmp_path / "data").mkdir()
    (tmp_path / "data/a.csv").write_bytes(b"a\n1\n")
    deadline = time.monotonic() + 30
    old = capture_analysis_data(tmp_path, run_id="real-run", stage_key="actual-stage", deadline=deadline)
    (tmp_path / "data/b.csv").write_bytes(b"b\n2\n")
    with pytest.raises(ValueError, match="differs from the complete"):
        require_analysis_data(old, tmp_path, run_id="real-run", stage_key="actual-stage", deadline=deadline)


def test_source_data_symlink_and_corrupted_retained_original_are_refused(tmp_path: Path) -> None:
    (tmp_path / "data").mkdir()
    source = tmp_path / "data/input.csv"
    source.write_bytes(b"a\n1\n")
    deadline = time.monotonic() + 30
    old = capture_analysis_data(tmp_path, run_id="real-run", stage_key="actual-stage", deadline=deadline)
    (tmp_path / old["records"][0]["retained_path"]).write_bytes(b"forged")
    with pytest.raises(ValueError, match="retained analysis original body changed"):
        capture_analysis_data(tmp_path, run_id="real-run", stage_key="actual-stage", deadline=deadline)
    source.unlink()
    source.symlink_to(tmp_path / "output")
    with pytest.raises(ValueError, match="link"):
        capture_analysis_data(tmp_path, run_id="other-run", stage_key="actual-stage", deadline=deadline)


def test_real_discovery_ceiling_refuses_before_yielding_an_extra_member(tmp_path: Path) -> None:
    for index in range(4):
        (tmp_path / str(index)).write_text("body")
    paths = iter_bounded_tree_paths(tmp_path, max_paths=2)
    assert next(paths).is_file() and next(paths).is_file()
    with pytest.raises(ValueError, match="path ceiling"):
        next(paths)
