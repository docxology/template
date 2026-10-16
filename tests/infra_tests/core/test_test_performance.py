"""Contract tests for owned serial/parallel test-performance evidence."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from infrastructure.core.testing.test_performance import (
    TestBenchmarkError,
    TestRunSummary,
    _redact_output_tail,
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
    cache_state: str = "cold-workspace",
) -> TestRunSummary:
    return TestRunSummary(
        target=target,  # type: ignore[arg-type]
        profile="quick",
        selection=("tests/test_owned.py::test_owned",),
        outcomes=("tests/test_owned.py::test_owned|passed",),
        cache_state=cache_state,
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
        serial_argv=("/Users/mini/.venv/bin/python3", "serial"),
        parallel_argv=("/Users/mini/.venv/bin/python3", "4"),
        minimum_improvement_percent=20.0,
        additional_runs=(
            _summary(axis="parallel", workers=4, elapsed=56.0, cache_state="warm-workspace"),
            _summary(axis="serial", workers=1, elapsed=80.0, cache_state="warm-workspace"),
        ),
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


def test_manifest_receipt_omits_subprocess_output_tails() -> None:
    serial = _summary(axis="serial", workers=1, elapsed=100.0)
    parallel = _summary(axis="parallel", workers=4, elapsed=70.0)
    serial = replace(serial, output_tail="/Users/mini/private-output")
    parallel = replace(parallel, output_tail="/private/var/folders/secret")

    payload = build_test_performance_manifest(
        serial,
        parallel,
        benchmarked_commit="abc123",
        serial_argv=("/Users/mini/.venv/bin/python3", "serial"),
        parallel_argv=("/Users/mini/.venv/bin/python3", "4"),
    ).to_dict()

    serial_payload = payload["serial"]
    parallel_payload = payload["parallel"]
    assert isinstance(serial_payload, dict)
    assert isinstance(parallel_payload, dict)
    assert "output_tail" not in serial_payload
    assert "output_tail" not in parallel_payload
    assert payload["serial_argv"][0] == "<absolute-path>"
    assert payload["parallel_argv"][0] == "<absolute-path>"


def test_output_tail_redaction_removes_absolute_paths(tmp_path: Path) -> None:
    output = f"checkout={tmp_path} temp=/private/var/folders/example/checkout"

    redacted = _redact_output_tail(output, tmp_path)

    assert str(tmp_path) not in redacted
    assert "/private/" not in redacted
    assert "<absolute-path>" in redacted


@pytest.mark.parametrize("fault", ["members", "outcomes", "missing-warm", "duplicate-axis", "workers"])
def test_comparison_requires_exact_cases_outcomes_and_independent_state_axes(fault: str) -> None:
    serial = _summary(axis="serial", workers=1, elapsed=100.0)
    parallel = _summary(axis="parallel", workers=4, elapsed=60.0)
    extras = (
        _summary(axis="parallel", workers=4, elapsed=60.0, cache_state="warm-workspace"),
        _summary(axis="serial", workers=1, elapsed=100.0, cache_state="warm-workspace"),
    )
    if fault == "members":
        parallel = replace(parallel, selection=("tests/test_owned.py::test_different",))
    elif fault == "outcomes":
        parallel = replace(parallel, outcomes=("tests/test_owned.py::test_owned|skipped",))
    elif fault == "missing-warm":
        extras = ()
    elif fault == "workers":
        extras = replace(extras[0], workers=2), extras[1]
    else:
        extras = extras[0], extras[0]
    manifest = build_test_performance_manifest(
        serial,
        parallel,
        benchmarked_commit="abc123",
        serial_argv=("serial",),
        parallel_argv=("4",),
        additional_runs=extras,
    )
    assert not manifest.acceptance_passed


@pytest.mark.parametrize("failed", [False, True])
def test_owned_benchmark_observes_real_pytest_members_and_outcomes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failed: bool
) -> None:
    import sys
    from infrastructure.core.testing.test_performance import _run_test_command

    monkeypatch.setenv("PYTHONPATH", str(Path(__file__).resolve().parents[3]))
    tests = tmp_path / "test_measured.py"
    tests.write_text("def test_actual():\n    assert " + ("False" if failed else "True") + "\n")
    arguments = dict(
        target="pipeline-smoke", profile="quick", serial=True, workers=1, commit="owned-control", timeout_seconds=30
    )
    command = (sys.executable, "-m", "pytest", "-q", "--no-cov", str(tests))
    if failed:
        with pytest.raises(TestBenchmarkError, match="original complete pytest observations"):
            _run_test_command(tmp_path, command, **arguments)
    else:
        observed = _run_test_command(tmp_path, command, **arguments)
        assert observed.selection == ("test_measured.py::test_actual",)
        assert observed.returncode == 0 and len(observed.outcomes) == 1
        assert '"call":"passed"' in observed.outcomes[0]


def test_warmup_refuses_actual_controller_failure_after_passing_pytest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import sys
    from infrastructure.core.testing.test_performance import _check_warmup, _run_test_command

    monkeypatch.setenv("PYTHONPATH", str(Path(__file__).resolve().parents[3]))
    (tmp_path / "test_actual.py").write_text("def test_actual():\n    assert 2 + 2 == 4\n")
    arguments = dict(
        target="pipeline-smoke", profile="quick", serial=True, workers=1, commit="owned", timeout_seconds=30
    )
    program = "import pytest,sys; status=pytest.main(['-q','--no-cov','test_actual.py']); sys.exit(status or int(sys.argv[1]))"
    failed = _run_test_command(tmp_path, (sys.executable, "-c", program, "7"), **arguments)
    measured = _run_test_command(tmp_path, (sys.executable, "-c", program, "0"), **arguments)
    assert failed.returncode == 7 and measured.returncode == 0
    assert failed.selection == measured.selection and failed.outcomes == measured.outcomes
    with pytest.raises(TestBenchmarkError, match="warmup failed"):
        _check_warmup(failed, measured)
    _check_warmup(measured, measured)
    with pytest.raises(TestBenchmarkError, match="differs"):
        _check_warmup(measured, replace(measured, outcomes=("different-outcome",)))
