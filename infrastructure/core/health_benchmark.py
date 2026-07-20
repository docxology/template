"""Run and validate the serial-versus-parallel repository health benchmark.

The authoritative CLI owns both health executions.  File-loading and comparison
helpers remain available for diagnostics, but caller-supplied reports can never
produce an accepted publication manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from infrastructure.core.health import GATE_NAMES, build_gate_specs, gate_spec_sha256

__all__ = [
    "HealthBenchmarkError",
    "HealthBenchmarkManifest",
    "HealthRunSummary",
    "build_health_benchmark_manifest",
    "load_health_report",
    "main",
    "run_health_benchmark",
]


class HealthBenchmarkError(ValueError):
    """Raised when benchmark evidence is incomplete or incomparable."""


@dataclass(frozen=True)
class HealthRunSummary:
    """Comparable evidence extracted from one health JSON report."""

    workers: int
    passed: bool
    wall_elapsed_ms: float
    total_elapsed_ms: float
    gates: tuple[str, ...]
    schema_version: int
    repo_commit: str
    clean_checkout: bool
    gate_spec_sha256: str
    report_sha256: str = ""


@dataclass(frozen=True)
class HealthBenchmarkManifest:
    """Decision record for the clean-checkout health latency criterion."""

    schema_version: int
    benchmarked_commit: str
    clean_checkout: bool
    python_version: str
    platform: str
    minimum_improvement_percent: float
    improvement_percent: float
    gate_registry: tuple[str, ...]
    serial: HealthRunSummary
    parallel: HealthRunSummary
    serial_argv: tuple[str, ...]
    parallel_argv: tuple[str, ...]
    evidence_owned: bool
    gate_sets_match: bool
    all_gates_executed: bool
    all_gates_passed: bool
    provenance_matches: bool
    acceptance_passed: bool


def _require_number(payload: Mapping[str, Any], field: str) -> float:
    value = payload.get(field)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise HealthBenchmarkError(f"health report field {field!r} must be numeric")
    if value < 0:
        raise HealthBenchmarkError(f"health report field {field!r} must be non-negative")
    return float(value)


def _parse_health_report(raw: str, *, source: str) -> HealthRunSummary:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HealthBenchmarkError(f"cannot load health report {source}: {exc}") from exc
    if not isinstance(payload, dict):
        raise HealthBenchmarkError(f"health report {source} must contain a JSON object")
    passed = payload.get("passed")
    results = payload.get("results")
    schema_version = payload.get("schema_version")
    workers = payload.get("workers")
    repo_commit = payload.get("repo_commit")
    clean_checkout = payload.get("clean_checkout")
    spec_digest = payload.get("gate_spec_sha256")
    if schema_version != 1:
        raise HealthBenchmarkError("health report schema_version must equal 1")
    if isinstance(workers, bool) or not isinstance(workers, int) or workers < 1:
        raise HealthBenchmarkError("health report field 'workers' must be a positive integer")
    if not isinstance(repo_commit, str) or not repo_commit.strip():
        raise HealthBenchmarkError("health report field 'repo_commit' must be non-empty")
    if not isinstance(clean_checkout, bool):
        raise HealthBenchmarkError("health report field 'clean_checkout' must be boolean")
    if not isinstance(spec_digest, str) or len(spec_digest) != 64:
        raise HealthBenchmarkError("health report field 'gate_spec_sha256' must be a SHA-256 digest")
    if not isinstance(passed, bool):
        raise HealthBenchmarkError("health report field 'passed' must be boolean")
    if not isinstance(results, list) or not results:
        raise HealthBenchmarkError("health report field 'results' must be a non-empty list")

    gates: list[str] = []
    gate_passes: list[bool] = []
    for index, result in enumerate(results):
        if not isinstance(result, dict):
            raise HealthBenchmarkError(f"health result {index} must be an object")
        name = result.get("name")
        result_passed = result.get("passed")
        if not isinstance(name, str) or not name:
            raise HealthBenchmarkError(f"health result {index} has an invalid name")
        if not isinstance(result_passed, bool):
            raise HealthBenchmarkError(f"health result {index} has an invalid passed value")
        gates.append(name)
        gate_passes.append(result_passed)
    if len(gates) != len(set(gates)):
        raise HealthBenchmarkError("health report contains duplicate gate names")
    if passed != all(gate_passes):
        raise HealthBenchmarkError("health report aggregate status disagrees with gate results")

    return HealthRunSummary(
        workers=workers,
        passed=passed,
        wall_elapsed_ms=_require_number(payload, "wall_elapsed_ms"),
        total_elapsed_ms=_require_number(payload, "total_elapsed_ms"),
        gates=tuple(gates),
        schema_version=schema_version,
        repo_commit=repo_commit,
        clean_checkout=clean_checkout,
        gate_spec_sha256=spec_digest,
        report_sha256=hashlib.sha256(raw.encode("utf-8")).hexdigest(),
    )


def load_health_report(path: Path) -> HealthRunSummary:
    """Load one report for diagnostics; it is not authoritative benchmark evidence."""

    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise HealthBenchmarkError(f"cannot load health report {path}: {exc}") from exc
    return _parse_health_report(raw, source=str(path))


def _build_manifest(
    serial: HealthRunSummary,
    parallel: HealthRunSummary,
    *,
    benchmarked_commit: str,
    expected_gate_spec_sha256: str,
    current_checkout_clean: bool,
    minimum_improvement_percent: float,
    python_version: str | None,
    platform_name: str | None,
    serial_argv: tuple[str, ...],
    parallel_argv: tuple[str, ...],
    evidence_owned: bool,
) -> HealthBenchmarkManifest:
    if serial.workers != 1:
        raise HealthBenchmarkError("serial evidence must use exactly one worker")
    if parallel.workers <= 1:
        raise HealthBenchmarkError("parallel evidence must use more than one worker")
    if serial.wall_elapsed_ms <= 0:
        raise HealthBenchmarkError("serial wall time must be greater than zero")
    if minimum_improvement_percent < 0 or minimum_improvement_percent >= 100:
        raise HealthBenchmarkError("minimum improvement must be in the range [0, 100)")
    if not benchmarked_commit.strip():
        raise HealthBenchmarkError("benchmarked commit must not be empty")
    if len(expected_gate_spec_sha256) != 64:
        raise HealthBenchmarkError("expected gate spec must be a SHA-256 digest")

    canonical_gates = tuple(GATE_NAMES)
    gate_sets_match = serial.gates == parallel.gates
    all_gates_executed = gate_sets_match and serial.gates == canonical_gates
    all_gates_passed = serial.passed and parallel.passed
    provenance_matches = (
        serial.repo_commit == parallel.repo_commit == benchmarked_commit
        and serial.gate_spec_sha256 == parallel.gate_spec_sha256 == expected_gate_spec_sha256
        and serial.clean_checkout
        and parallel.clean_checkout
        and bool(serial.report_sha256)
        and bool(parallel.report_sha256)
    )
    clean_checkout = current_checkout_clean and serial.clean_checkout and parallel.clean_checkout
    improvement = ((serial.wall_elapsed_ms - parallel.wall_elapsed_ms) / serial.wall_elapsed_ms) * 100.0
    acceptance_passed = (
        evidence_owned
        and clean_checkout
        and gate_sets_match
        and all_gates_executed
        and all_gates_passed
        and provenance_matches
        and improvement >= minimum_improvement_percent
    )
    return HealthBenchmarkManifest(
        schema_version=2,
        benchmarked_commit=benchmarked_commit,
        clean_checkout=clean_checkout,
        python_version=python_version or platform.python_version(),
        platform=platform_name or platform.platform(),
        minimum_improvement_percent=minimum_improvement_percent,
        improvement_percent=round(improvement, 2),
        gate_registry=canonical_gates,
        serial=serial,
        parallel=parallel,
        serial_argv=serial_argv,
        parallel_argv=parallel_argv,
        evidence_owned=evidence_owned,
        gate_sets_match=gate_sets_match,
        all_gates_executed=all_gates_executed,
        all_gates_passed=all_gates_passed,
        provenance_matches=provenance_matches,
        acceptance_passed=acceptance_passed,
    )


def build_health_benchmark_manifest(
    serial: HealthRunSummary,
    parallel: HealthRunSummary,
    *,
    benchmarked_commit: str,
    expected_gate_spec_sha256: str,
    current_checkout_clean: bool,
    minimum_improvement_percent: float = 25.0,
    python_version: str | None = None,
    platform_name: str | None = None,
) -> HealthBenchmarkManifest:
    """Compare caller-supplied reports without granting publication acceptance."""

    return _build_manifest(
        serial,
        parallel,
        benchmarked_commit=benchmarked_commit,
        expected_gate_spec_sha256=expected_gate_spec_sha256,
        current_checkout_clean=current_checkout_clean,
        minimum_improvement_percent=minimum_improvement_percent,
        python_version=python_version,
        platform_name=platform_name,
        serial_argv=(),
        parallel_argv=(),
        evidence_owned=False,
    )


def _git_output(repo_root: Path, *args: str) -> str:
    process = subprocess.run(  # noqa: S603 - fixed git executable and argv.
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if process.returncode != 0:
        detail = (process.stderr or process.stdout).strip()
        raise HealthBenchmarkError(f"git {' '.join(args)} failed: {detail}")
    return process.stdout.strip()


def _run_health(repo_root: Path, *, workers: int, timeout_seconds: float) -> tuple[HealthRunSummary, tuple[str, ...]]:
    argv = (
        sys.executable,
        "-m",
        "infrastructure.core.health",
        "--repo-root",
        str(repo_root),
        "--workers",
        str(workers),
        "--json",
        "--quiet",
    )
    try:
        process = subprocess.run(  # noqa: S603 - interpreter and fixed module/flags only.
            argv,
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise HealthBenchmarkError(f"health run with {workers} worker(s) timed out") from exc
    if process.returncode not in {0, 1}:
        detail = (process.stderr or process.stdout).strip()
        raise HealthBenchmarkError(f"health run with {workers} worker(s) could not execute: {detail}")
    return _parse_health_report(process.stdout, source=f"owned {workers}-worker execution"), argv


def run_health_benchmark(
    repo_root: Path,
    *,
    parallel_workers: int = 4,
    minimum_improvement_percent: float = 25.0,
    timeout_seconds: float = 3600.0,
) -> HealthBenchmarkManifest:
    """Own both health executions and return their fail-closed manifest."""

    root = repo_root.resolve()
    if parallel_workers <= 1:
        raise HealthBenchmarkError("parallel worker count must be greater than one")
    status_before = _git_output(root, "status", "--porcelain", "--untracked-files=normal")
    if status_before:
        raise HealthBenchmarkError("health benchmark requires a clean checkout before execution")
    commit_before = _git_output(root, "rev-parse", "HEAD")
    expected_digest = gate_spec_sha256(build_gate_specs(root))
    serial, serial_argv = _run_health(root, workers=1, timeout_seconds=timeout_seconds)
    parallel, parallel_argv = _run_health(root, workers=parallel_workers, timeout_seconds=timeout_seconds)
    status_after = _git_output(root, "status", "--porcelain", "--untracked-files=normal")
    commit_after = _git_output(root, "rev-parse", "HEAD")
    checkout_unchanged = not status_after and commit_before == commit_after
    return _build_manifest(
        serial,
        parallel,
        benchmarked_commit=commit_before,
        expected_gate_spec_sha256=expected_digest,
        current_checkout_clean=checkout_unchanged,
        minimum_improvement_percent=minimum_improvement_percent,
        python_version=None,
        platform_name=None,
        serial_argv=serial_argv,
        parallel_argv=parallel_argv,
        evidence_owned=True,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--minimum-improvement", type=float, default=25.0)
    parser.add_argument("--parallel-workers", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=3600.0)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the benchmark, write its manifest, and enforce acceptance."""

    args = _build_parser().parse_args(argv)
    try:
        manifest = run_health_benchmark(
            args.repo_root,
            parallel_workers=args.parallel_workers,
            minimum_improvement_percent=args.minimum_improvement,
            timeout_seconds=args.timeout,
        )
    except HealthBenchmarkError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(asdict(manifest), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"Health benchmark: {manifest.improvement_percent:.2f}% improvement; "
        f"acceptance={'PASS' if manifest.acceptance_passed else 'FAIL'}"
    )
    return 0 if manifest.acceptance_passed else 1


if __name__ == "__main__":  # pragma: no cover - exercised through the script entrypoint.
    raise SystemExit(main())
