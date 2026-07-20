"""Real-file tests for the repository health benchmark manifest."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from infrastructure.core.health import GATE_NAMES
from infrastructure.core.health_benchmark import (
    HealthBenchmarkError,
    HealthRunSummary,
    build_health_benchmark_manifest,
    load_health_report,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_DIGEST = "d" * 64


def _write_report(
    path: Path,
    *,
    wall_ms: float,
    workers: int,
    commit: str = "abc123",
    spec_digest: str = TEST_DIGEST,
    passed: bool = True,
    clean_checkout: bool = True,
    gates: tuple[str, ...] = GATE_NAMES,
) -> None:
    results = [{"name": name, "passed": passed, "elapsed_ms": 10.0, "output": ""} for name in gates]
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "passed": passed,
                "workers": workers,
                "repo_commit": commit,
                "clean_checkout": clean_checkout,
                "gate_spec_sha256": spec_digest,
                "total_elapsed_ms": float(len(gates) * 10),
                "wall_elapsed_ms": wall_ms,
                "results": results,
            }
        ),
        encoding="utf-8",
    )


def test_caller_supplied_reports_never_receive_publication_acceptance(tmp_path: Path) -> None:
    serial_path = tmp_path / "serial.json"
    parallel_path = tmp_path / "parallel.json"
    _write_report(serial_path, wall_ms=100_000, workers=1)
    _write_report(parallel_path, wall_ms=60_000, workers=4)

    manifest = build_health_benchmark_manifest(
        load_health_report(serial_path),
        load_health_report(parallel_path),
        benchmarked_commit="abc123",
        expected_gate_spec_sha256=TEST_DIGEST,
        current_checkout_clean=True,
        python_version="3.12.0",
        platform_name="test-platform",
    )

    assert manifest.acceptance_passed is False
    assert manifest.evidence_owned is False
    assert manifest.improvement_percent == 40.0
    assert manifest.all_gates_executed is True
    assert manifest.gate_registry == GATE_NAMES


@pytest.mark.parametrize(
    ("clean_checkout", "parallel_wall", "parallel_gates"),
    [
        (False, 60_000, GATE_NAMES),
        (True, 80_000, GATE_NAMES),
        (True, 60_000, GATE_NAMES[:-1]),
    ],
)
def test_manifest_fails_closed_on_unaccepted_evidence(
    clean_checkout: bool,
    parallel_wall: float,
    parallel_gates: tuple[str, ...],
) -> None:
    serial = HealthRunSummary(1, True, 100_000, 200_000, GATE_NAMES, 1, "abc123", True, TEST_DIGEST)
    parallel = HealthRunSummary(4, True, parallel_wall, 200_000, parallel_gates, 1, "abc123", True, TEST_DIGEST)

    manifest = build_health_benchmark_manifest(
        serial,
        parallel,
        benchmarked_commit="abc123",
        expected_gate_spec_sha256=TEST_DIGEST,
        current_checkout_clean=clean_checkout,
    )

    assert manifest.acceptance_passed is False


def test_load_report_rejects_inconsistent_aggregate(tmp_path: Path) -> None:
    report_path = tmp_path / "invalid.json"
    _write_report(report_path, wall_ms=1_000, workers=1)
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    payload["results"][0]["passed"] = False
    report_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(HealthBenchmarkError, match="aggregate status"):
        load_health_report(report_path)


def test_manifest_rejects_report_from_another_commit() -> None:
    serial = HealthRunSummary(1, True, 100_000, 200_000, GATE_NAMES, 1, "abc123", True, TEST_DIGEST)
    parallel = HealthRunSummary(4, True, 60_000, 200_000, GATE_NAMES, 1, "other", True, TEST_DIGEST)

    manifest = build_health_benchmark_manifest(
        serial,
        parallel,
        benchmarked_commit="abc123",
        expected_gate_spec_sha256=TEST_DIGEST,
        current_checkout_clean=True,
    )

    assert manifest.provenance_matches is False
    assert manifest.acceptance_passed is False


def test_cli_refuses_dirty_checkout_before_running_health(tmp_path: Path) -> None:
    checkout = tmp_path / "dirty-checkout"
    checkout.mkdir()
    (checkout / "README.md").write_text("benchmark fixture\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=checkout, check=True, timeout=30)
    subprocess.run(["git", "add", "README.md"], cwd=checkout, check=True, timeout=30)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Template Tests",
            "-c",
            "user.email=template-tests@example.test",
            "commit",
            "-qm",
            "fixture baseline",
        ],
        cwd=checkout,
        check=True,
        timeout=30,
    )
    (checkout / "dirty.txt").write_text("uncommitted\n", encoding="utf-8")
    output_path = tmp_path / "manifest.json"
    process = subprocess.run(  # noqa: S603 - real thin entrypoint contract.
        [
            sys.executable,
            "scripts/maintenance/benchmark_health.py",
            "--repo-root",
            str(checkout),
            "--output",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert process.returncode == 2
    assert "requires a clean checkout" in process.stderr
    assert not output_path.exists()


def test_cli_rejects_caller_supplied_report_flags(tmp_path: Path) -> None:
    process = subprocess.run(  # noqa: S603 - real thin entrypoint contract.
        [
            sys.executable,
            "scripts/maintenance/benchmark_health.py",
            "--serial-report",
            str(tmp_path / "serial.json"),
            "--output",
            str(tmp_path / "manifest.json"),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert process.returncode == 2
    assert "unrecognized arguments: --serial-report" in process.stderr
