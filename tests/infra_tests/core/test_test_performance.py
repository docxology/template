"""Contract tests for owned serial/parallel test-performance evidence."""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.core.test_performance import (
    TestBenchmarkError,
    TestRunSummary,
    build_test_command,
    build_test_performance_manifest,
)


def _summary(
    *,
    axis: str,
    workers: int,
    elapsed: float,
    returncode: int = 0,
    target: str = "pipeline-smoke",
) -> TestRunSummary:
    return TestRunSummary(
        target=target,  # type: ignore[arg-type]
        profile="quick",
        selection=(target, "quick"),
        axis=axis,
        workers=workers,
        returncode=returncode,
        wall_elapsed_seconds=elapsed,
        repo_commit="abc123",
    )


def test_build_test_commands_keep_selection_and_change_only_parallel_axis(tmp_path: Path) -> None:
    serial = build_test_command(
        tmp_path,
        target="pipeline-smoke",
        profile="quick",
        serial=True,
        parallel_workers=4,
    )
    parallel = build_test_command(
        tmp_path,
        target="pipeline-smoke",
        profile="quick",
        serial=False,
        parallel_workers=4,
    )

    assert "--infra-only" in serial
    assert "pipeline-smoke" in serial
    assert serial[-1] == "serial"
    assert parallel[-1] == "4"
    assert serial[:5] == parallel[:5]


def test_manifest_accepts_matching_passing_runs_with_measured_improvement() -> None:
    manifest = build_test_performance_manifest(
        _summary(axis="serial", workers=1, elapsed=100.0, target="pipeline-smoke"),
        _summary(axis="parallel", workers=4, elapsed=70.0),
        benchmarked_commit="abc123",
        serial_argv=("serial",),
        parallel_argv=("4",),
        minimum_improvement_percent=20.0,
    )

    assert manifest.selection_matches is True
    assert manifest.provenance_matches is True
    assert manifest.clean_checkout is True
    assert manifest.improvement_percent == 30.0
    assert manifest.acceptance_passed is True


def test_manifest_fails_closed_on_selection_or_run_failure() -> None:
    manifest = build_test_performance_manifest(
        _summary(axis="serial", workers=1, elapsed=100.0),
        _summary(axis="parallel", workers=4, elapsed=70.0, returncode=1, target="public-projects"),
        benchmarked_commit="abc123",
        serial_argv=("serial",),
        parallel_argv=("4",),
    )

    assert manifest.selection_matches is False
    assert manifest.both_runs_passed is False
    assert manifest.acceptance_passed is False


def test_manifest_fails_closed_when_checkout_changes() -> None:
    manifest = build_test_performance_manifest(
        _summary(axis="serial", workers=1, elapsed=100.0),
        _summary(axis="parallel", workers=4, elapsed=70.0),
        benchmarked_commit="abc123",
        serial_argv=("serial",),
        parallel_argv=("4",),
        current_checkout_clean=False,
    )

    assert manifest.clean_checkout is False
    assert manifest.provenance_matches is False
    assert manifest.acceptance_passed is False


def test_manifest_rejects_invalid_worker_evidence() -> None:
    with pytest.raises(TestBenchmarkError, match="serial evidence"):
        build_test_performance_manifest(
            _summary(axis="parallel", workers=4, elapsed=100.0),
            _summary(axis="parallel", workers=4, elapsed=70.0),
            benchmarked_commit="abc123",
            serial_argv=("serial",),
            parallel_argv=("4",),
        )
