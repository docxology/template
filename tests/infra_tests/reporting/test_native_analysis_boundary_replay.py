"""Serialized DATA cannot manufacture genuine original native/analysis authority."""

from pathlib import Path

import pytest

from infrastructure.reporting.native_analysis_boundary_replay import replay_native_analysis_boundary_graph
from infrastructure.reporting.native_projection_contracts import ProjectionSourceUnsupported
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def test_serialized_process_and_boundary_digests_cannot_create_original_custody(tmp_path: Path) -> None:
    path = tmp_path / "output/readiness/native.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        '{"scope":"templates/template_code_project","status":"pass",'
        '"analysis_data_graph":{"pid":123,"original_exit_code":0,"fulfilled":true}}'
    )
    reader = SnapshotReader(tmp_path)
    with pytest.raises(ProjectionSourceUnsupported, match="externally admitted"):
        replay_native_analysis_boundary_graph(
            "templates/template_code_project",
            reader.read("output/readiness/native.json"),
            reader,
        )
