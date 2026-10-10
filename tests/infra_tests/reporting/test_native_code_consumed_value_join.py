"""Real byte/domain DATA controls; no genuine Original/Current is fabricated."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import pytest

from infrastructure.rendering.manuscript_hydration_replay import require_shared_hydration
from infrastructure.reporting.native_code_consumed_value_join import (
    KEY,
    _binding,
    _registered_origin,
    _scalar_config,
    _selected_occurrences,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

CONFIG = b"""experiment:
  step_sizes: [0.5, 1.0]
  quadratic_A: [[1.0]]
  quadratic_b: [1.0]
  initial_point: 0.0
  max_iterations: 20
  tolerance: 0.000001
  convergence_tolerance: 0.000001
  stability_starting_points: [0.0]
  stability_step_sizes: [0.5]
  benchmark_dimensions: [1]
"""


def test_selected_scalar_configuration_preserves_source_model_and_refuses_missing_grid() -> None:
    config = _scalar_config(CONFIG)
    assert config.step_sizes == (0.5, 1.0)
    assert config.coefficient == config.linear == 1.0
    assert config.max_iterations == 20
    with pytest.raises(ValueError, match="complete declared scalar"):
        _scalar_config(CONFIG.replace(b"  step_sizes: [0.5, 1.0]\n", b""))
    with pytest.raises(ValueError, match="scalar configuration"):
        _scalar_config(CONFIG.replace(b"quadratic_A: [[1.0]]", b"quadratic_A: [[1.0, 0.0], [0.0, 1.0]]"))


def _held_occurrences(root: Path) -> tuple[SnapshotReader, dict[str, Any]]:
    project = root / "projects/templates/template_code_project"
    source = project / "manuscript/03_results.md"
    consumed = project / "output/manuscript/03_results.md"
    source.parent.mkdir(parents=True)
    consumed.parent.mkdir(parents=True)
    source.write_bytes(b"Value {{RESULT_MIN_ITERATIONS}} twice {{RESULT_MIN_ITERATIONS}}; {{STABILITY_SCORE}}.\r\n")
    values = {KEY: "1", "STABILITY_SCORE": "1"}
    output = b"Value 1 twice 1; 1.\n"
    consumed.write_bytes(output)
    reader = SnapshotReader(root)
    authored = reader.read(source.relative_to(root).as_posix())
    held = reader.read(consumed.relative_to(root).as_posix())
    graph = {
        "ordered_inputs": [
            {
                "source": _binding(authored),
                "consumed": _binding(held),
                "transformation": "shared-uppercase-token-hydration",
                "hydration": require_shared_hydration(authored.content, values, held.content).data(),
            }
        ]
    }
    return reader, graph


def test_selected_key_retains_every_authored_occurrence_and_other_equal_value_residual(tmp_path: Path) -> None:
    reader, graph = _held_occurrences(tmp_path)
    selected, residuals = _selected_occurrences(graph, reader, deadline=time.monotonic() + 30)
    assert [row["ordinal"] for row in selected] == [1, 2]
    assert [row["output_start_byte"] for row in selected] == [6, 14]
    assert len(residuals) == 1 and residuals[0].endswith(":3:STABILITY_SCORE")
    assert reader.unchanged()


def test_changed_output_interval_fails_the_exact_held_payload_hash(tmp_path: Path) -> None:
    reader, graph = _held_occurrences(tmp_path)
    graph["ordered_inputs"][0]["hydration"]["occurrences"][0]["output_start_byte"] = 5
    with pytest.raises(ValueError, match="final payload interval"):
        _selected_occurrences(graph, reader, deadline=time.monotonic() + 30)


def test_missing_completed_write_retains_conditional_origin_residual(tmp_path: Path) -> None:
    project = tmp_path / "projects/templates/template_code_project"
    paths = []
    for name, content in (
        ("manuscript/config.yaml", CONFIG),
        ("output/data/optimization_results.csv", b"csv data"),
        ("output/data/manuscript_variables.json", b"{}"),
    ):
        path = project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        paths.append(path.relative_to(tmp_path).as_posix())
    reader = SnapshotReader(tmp_path)
    config, csv, variables = (reader.read(name) for name in paths)
    origin, residuals = _registered_origin(
        {"ordered_stages": []}, config, csv, variables, deadline=time.monotonic() + 30
    )
    assert origin is None
    assert residuals == ["consumed-value-missing-completed-analysis-write-or-hydration-stage:" + KEY]
