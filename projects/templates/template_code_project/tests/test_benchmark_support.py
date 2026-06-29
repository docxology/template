"""Tests for benchmark_support (no mocks; real timing + real infra API)."""

from __future__ import annotations

import json
from pathlib import Path

from src.benchmark_support import (
    DEFAULT_INPUT_SIZES,
    benchmark_payload,
    run_quadratic_benchmark,
    write_benchmark_report,
)

from infrastructure.benchmark import BenchmarkScore, RubricScore


def test_run_benchmark_returns_one_measurement_per_input_size() -> None:
    """The harness times the pure quadratic_function across each fixed size."""
    result = run_quadratic_benchmark()
    sizes = [m.input_size for m in result.measurements]
    assert sizes == list(DEFAULT_INPUT_SIZES)
    # Every measurement is a real, non-negative wall-clock time over real calls.
    for measurement in result.measurements:
        assert measurement.repeats > 0
        assert measurement.best_seconds >= 0.0
        assert measurement.calls == measurement.repeats


def test_rubric_score_is_real_infra_type_and_passes() -> None:
    """Boolean check results are scored through infrastructure.benchmark.score_rubric."""
    result = run_quadratic_benchmark()
    assert isinstance(result.rubric_score, RubricScore)
    assert isinstance(result.benchmark_score, BenchmarkScore)
    # All deterministic checks should pass for the well-behaved quadratic.
    assert result.rubric_score.passed
    assert result.rubric_score.score == result.rubric_score.max_score
    assert result.benchmark_score.passed
    # Rubric dimension names line up with the recorded check results.
    assert set(result.checks) == {d.name for d in result.rubric.dimensions}


def test_payload_has_expected_infra_fields() -> None:
    """benchmark_payload carries the infra-shaped score fields."""
    payload = benchmark_payload(run_quadratic_benchmark())
    assert payload["passed"] is True
    assert payload["rubric"]["name"]
    assert payload["rubric"]["score"] == payload["rubric"]["max_score"]
    assert set(payload["checks"]) == set(payload["rubric"]["dimensions"])
    assert len(payload["measurements"]) == len(DEFAULT_INPUT_SIZES)
    # The markdown table comes from infrastructure.benchmark.scores_to_markdown.
    assert payload["markdown"].startswith("| Project |")
    assert "template_code_project" in payload["markdown"]


def test_payload_is_deterministic_across_runs() -> None:
    """Structural payload (minus timing) is identical run to run."""
    first = benchmark_payload(run_quadratic_benchmark())
    second = benchmark_payload(run_quadratic_benchmark())

    def _strip_timing(payload: dict) -> dict:
        clone = json.loads(json.dumps(payload))
        for measurement in clone["measurements"]:
            measurement.pop("best_seconds", None)
        clone.pop("markdown", None)
        return clone

    assert _strip_timing(first) == _strip_timing(second)
    assert first["checks"] == second["checks"]
    assert first["rubric"] == second["rubric"]


def test_write_benchmark_report_emits_json(tmp_path: Path) -> None:
    """write_benchmark_report writes a JSON report and returns its path."""
    out_path = tmp_path / "benchmark_report.json"
    written = write_benchmark_report(run_quadratic_benchmark(), out_path)
    assert written == out_path
    assert written.is_file()
    loaded = json.loads(written.read_text(encoding="utf-8"))
    assert loaded["passed"] is True
    assert loaded["project"] == "template_code_project"
    assert len(loaded["measurements"]) == len(DEFAULT_INPUT_SIZES)
