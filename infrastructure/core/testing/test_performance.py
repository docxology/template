"""Owned serial-versus-parallel evidence for the canonical test lanes."""

from __future__ import annotations

import argparse
import json
import platform
import re
import subprocess  # nosec B404 - fixed repository entrypoint and argv
import tempfile
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from time import monotonic
from typing import Literal, Sequence
from uuid import uuid4
import os
import math

from infrastructure.core.testing.pytest_observations import DIRECTORY_ENV, NONCE_ENV, ROOT_ENV, read_execution_receipts

from infrastructure.core.testing.pytest_orchestration import resolve_project_matrix_workers

TestBenchmarkTarget = Literal["pipeline-smoke", "infrastructure", "public-projects"]
TEST_BENCHMARK_SCHEMA = "template-test-performance-v2"
_ABSOLUTE_PATH_RE = re.compile(r"(?<![\w])(?:/(?:[^/\s]+/)*[^/\s]+|[A-Za-z]:\\(?:[^\\\s]+\\)*[^\\\s]+)")


class TestBenchmarkError(ValueError):
    """Raised when a test-performance evidence run cannot be accepted."""


@dataclass(frozen=True)
class TestRunSummary:
    """Comparable result from one owned test subprocess."""

    target: TestBenchmarkTarget
    profile: str
    selection: tuple[str, ...]
    axis: str
    workers: int
    returncode: int
    wall_elapsed_seconds: float
    repo_commit: str
    output_tail: str = ""
    outcomes: tuple[str, ...] = ()
    cache_state: str = "cold-workspace"


@dataclass(frozen=True)
class TestPerformanceManifest:
    """Fail-closed serial/parallel test-lane performance evidence."""

    schema_version: str
    target: TestBenchmarkTarget
    benchmarked_commit: str
    python_version: str
    platform: str
    minimum_improvement_percent: float
    improvement_percent: float
    serial: TestRunSummary
    parallel: TestRunSummary
    serial_argv: tuple[str, ...]
    parallel_argv: tuple[str, ...]
    selection_matches: bool
    provenance_matches: bool
    clean_checkout: bool
    both_runs_passed: bool
    acceptance_passed: bool
    additional_runs: tuple[TestRunSummary, ...]
    cold_and_warm_verified: bool

    def to_dict(self) -> dict[str, object]:
        """Serialize the manifest with stable nested dataclass fields."""
        payload = asdict(self)
        # Subprocess output is useful while diagnosing a local run, but it can
        # contain checkout paths, temporary directories, or tool-specific
        # environment details.  Keep those diagnostics in memory only; a
        # committed receipt is a public provenance artifact.
        for lane in ("serial", "parallel"):
            lane_payload = payload.get(lane)
            if isinstance(lane_payload, dict):
                lane_payload.pop("output_tail", None)
        for extra in payload.get("additional_runs", ()):
            extra.pop("output_tail", None)
        for argv_key in ("serial_argv", "parallel_argv"):
            argv = payload.get(argv_key)
            if isinstance(argv, (list, tuple)):
                payload[argv_key] = [_redact_argv_value(value) for value in argv]
        return payload


def _redact_output_tail(output: str, repo_root: Path) -> str:
    """Return bounded diagnostics without leaking absolute checkout paths."""
    redacted = output.replace(str(repo_root.resolve()), "<checkout>")
    redacted = _ABSOLUTE_PATH_RE.sub("<absolute-path>", redacted)
    return redacted[-4000:]


def _redact_argv_value(value: object) -> object:
    """Redact absolute paths while retaining public command shape."""
    if not isinstance(value, str):
        return value
    return _ABSOLUTE_PATH_RE.sub("<absolute-path>", value)


def build_test_command(
    repo_root: Path,
    *,
    target: TestBenchmarkTarget,
    profile: str,
    serial: bool,
    parallel_workers: int,
) -> tuple[str, ...]:
    """Build one canonical Stage 01 command for a benchmark lane."""
    del repo_root  # The command is intentionally portable across disposable worktrees.
    if parallel_workers <= 1:
        raise TestBenchmarkError("parallel_workers must be greater than one")
    command: list[str] = [
        sys.executable,
        str(Path("scripts") / "pipeline" / "stage_01_test.py"),
        "--profile",
        profile,
    ]
    if target in {"pipeline-smoke", "infrastructure"}:
        command.extend(
            (
                "--infra-only",
                "--infra-scope",
                "pipeline-smoke" if target == "pipeline-smoke" else "full",
                "--parallel",
                "serial" if serial else str(parallel_workers),
            )
        )
    elif target == "public-projects":
        command.extend(("--project-only", "--all-projects", "--public-projects", "--project-workers"))
        command.append("serial" if serial else str(parallel_workers))
    else:  # pragma: no cover - Literal protects callers; defensive CLI boundary.
        raise TestBenchmarkError(f"unsupported benchmark target: {target}")
    return tuple(command)


def _git_output(repo_root: Path, *args: str) -> str:
    process = subprocess.run(  # noqa: S603 - fixed git executable and argv
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if process.returncode != 0:
        detail = (process.stderr or process.stdout).strip()
        raise TestBenchmarkError(f"git {' '.join(args)} failed: {detail}")
    return process.stdout.strip()


def _run_git_command(repo_root: Path, *args: str) -> None:
    """Run a fixed git maintenance command and fail with actionable context."""
    process = subprocess.run(  # noqa: S603 - fixed git executable and argv
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    if process.returncode != 0:
        detail = (process.stderr or process.stdout).strip()
        raise TestBenchmarkError(f"git {' '.join(args)} failed: {detail}")


def _run_test_command(
    repo_root: Path,
    command: tuple[str, ...],
    *,
    target: TestBenchmarkTarget,
    profile: str,
    serial: bool,
    workers: int,
    commit: str,
    timeout_seconds: float,
    cache_state: str = "cold-workspace",
) -> TestRunSummary:
    nonce = uuid4().hex
    receipt_directory = repo_root.parent / (repo_root.name + "-receipts-" + nonce)
    environment = {**os.environ, DIRECTORY_ENV: str(receipt_directory), NONCE_ENV: nonce, ROOT_ENV: str(repo_root)}
    environment["PYTEST_ADDOPTS"] = (
        environment.get("PYTEST_ADDOPTS", "") + " -p infrastructure.core.testing.pytest_receipt"
    )
    started = monotonic()
    try:
        process = subprocess.run(  # noqa: S603 - fixed repository command
            command,
            cwd=repo_root,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise TestBenchmarkError(f"test benchmark timed out: {' '.join(command)}") from exc
    elapsed = monotonic() - started
    output = f"{process.stdout}\n{process.stderr}".strip()
    try:
        selected, outcomes = read_execution_receipts(receipt_directory, nonce)
    except (ValueError, OSError) as exc:
        raise TestBenchmarkError("test benchmark lacks original complete pytest observations") from exc
    return TestRunSummary(
        target=target,
        profile=profile,
        selection=selected,
        axis="serial" if serial else "parallel",
        workers=1 if serial else workers,
        returncode=process.returncode,
        wall_elapsed_seconds=round(elapsed, 3),
        repo_commit=commit,
        output_tail=_redact_output_tail(output, repo_root),
        outcomes=outcomes,
        cache_state=cache_state,
    )


def build_test_performance_manifest(
    serial: TestRunSummary,
    parallel: TestRunSummary,
    *,
    benchmarked_commit: str,
    serial_argv: tuple[str, ...],
    parallel_argv: tuple[str, ...],
    minimum_improvement_percent: float = 30.0,
    current_checkout_clean: bool = True,
    additional_runs: Sequence[TestRunSummary] = (),
) -> TestPerformanceManifest:
    """Compare owned run summaries and compute a fail-closed acceptance result."""
    if serial.axis != "serial" or serial.workers != 1:
        raise TestBenchmarkError("serial evidence must use one serial worker")
    if parallel.axis != "parallel" or parallel.workers <= 1:
        raise TestBenchmarkError("parallel evidence must use more than one worker")
    if serial.wall_elapsed_seconds <= 0 or parallel.wall_elapsed_seconds <= 0:
        raise TestBenchmarkError("test benchmark wall times must be positive")
    if not math.isfinite(minimum_improvement_percent) or not 0 <= minimum_improvement_percent < 100:
        raise TestBenchmarkError("minimum improvement must be in the range [0, 100)")
    observations = (serial, parallel, *additional_runs)
    if any(not math.isfinite(row.wall_elapsed_seconds) or row.wall_elapsed_seconds <= 0 for row in observations):
        raise TestBenchmarkError("test benchmark wall times must be finite and positive")
    if any(
        (row.axis == "serial" and row.workers != 1) or (row.axis == "parallel" and row.workers <= 1)
        for row in observations
    ):
        raise TestBenchmarkError("test benchmark axes differ from actual worker declarations")
    by_state = {(row.cache_state, row.axis): row for row in observations}
    expected_axes = {(state, axis) for state in ("cold-workspace", "warm-workspace") for axis in ("serial", "parallel")}
    cold_and_warm = len(observations) == 4 and set(by_state) == expected_axes
    improvements = [(serial.wall_elapsed_seconds - parallel.wall_elapsed_seconds) / serial.wall_elapsed_seconds * 100.0]
    if cold_and_warm:
        for state in ("cold-workspace", "warm-workspace"):
            before, after = by_state[state, "serial"], by_state[state, "parallel"]
            if before.wall_elapsed_seconds <= 0 or after.wall_elapsed_seconds <= 0:
                raise TestBenchmarkError("test benchmark wall times must be positive")
            improvements.append(
                (before.wall_elapsed_seconds - after.wall_elapsed_seconds) / before.wall_elapsed_seconds * 100.0
            )
    improvement = min(improvements)
    selection_matches = (
        serial.target == parallel.target
        and serial.profile == parallel.profile
        and all(row.target == serial.target and row.profile == serial.profile for row in observations)
        and all(row.workers == parallel.workers for row in observations if row.axis == "parallel")
        and bool(serial.selection)
        and bool(serial.outcomes)
        and all(row.selection == serial.selection and row.outcomes == serial.outcomes for row in observations)
        and len(serial.selection) == len(serial.outcomes)
    )
    provenance_matches = (
        all(row.repo_commit == benchmarked_commit for row in observations)
        and serial.target == parallel.target
        and current_checkout_clean
    )
    both_runs_passed = all(row.returncode == 0 for row in observations)
    return TestPerformanceManifest(
        schema_version=TEST_BENCHMARK_SCHEMA,
        target=serial.target,
        benchmarked_commit=benchmarked_commit,
        python_version=platform.python_version(),
        platform=platform.platform(),
        minimum_improvement_percent=minimum_improvement_percent,
        improvement_percent=round(improvement, 2),
        serial=serial,
        parallel=parallel,
        serial_argv=serial_argv,
        parallel_argv=parallel_argv,
        selection_matches=selection_matches,
        provenance_matches=provenance_matches,
        clean_checkout=current_checkout_clean,
        both_runs_passed=both_runs_passed,
        additional_runs=tuple(additional_runs),
        cold_and_warm_verified=cold_and_warm,
        acceptance_passed=(
            current_checkout_clean
            and cold_and_warm
            and selection_matches
            and provenance_matches
            and both_runs_passed
            and improvement >= minimum_improvement_percent
        ),
    )


def _check_warmup(warmup: TestRunSummary, measured: TestRunSummary) -> None:
    if warmup.returncode != 0 or any(
        getattr(warmup, field) != getattr(measured, field)
        for field in ("selection", "outcomes", "axis", "workers", "target", "profile", "repo_commit")
    ):
        raise TestBenchmarkError("warmup failed or differs from its measured execution")


def run_test_benchmark(
    repo_root: Path,
    *,
    target: TestBenchmarkTarget = "pipeline-smoke",
    profile: str = "quick",
    parallel_workers: int | None = None,
    minimum_improvement_percent: float = 30.0,
    timeout_seconds: float = 3600.0,
) -> TestPerformanceManifest:
    """Own both test executions and return their provenance-bound manifest."""
    root = repo_root.resolve()
    if timeout_seconds <= 0:
        raise TestBenchmarkError("timeout_seconds must be positive")
    workers = parallel_workers or resolve_project_matrix_workers()
    if workers <= 1:
        raise TestBenchmarkError("parallel worker count must be greater than one")
    status_before = _git_output(root, "status", "--porcelain", "--untracked-files=normal")
    if status_before:
        raise TestBenchmarkError("test benchmark requires a clean checkout before execution")
    commit_before = _git_output(root, "rev-parse", "HEAD")
    observations: list[TestRunSummary] = []
    commands: dict[str, tuple[str, ...]] = {}
    # Independent worktrees prevent the serial run warming the parallel run.
    # Reverse the axis order for warm observations; each warm run gets its own
    # same-command untimed prewarm. "Cold" describes workspace state, not OS caches.
    with tempfile.TemporaryDirectory(prefix="template-test-benchmark-") as temp_dir:
        for ordinal, (state, serial_axis) in enumerate(
            (("cold-workspace", True), ("cold-workspace", False), ("warm-workspace", False), ("warm-workspace", True))
        ):
            benchmark_root = Path(temp_dir) / f"checkout-{ordinal}"
            _run_git_command(root, "worktree", "add", "--detach", "--quiet", str(benchmark_root), commit_before)
            try:
                command = build_test_command(
                    benchmark_root, target=target, profile=profile, serial=serial_axis, parallel_workers=workers
                )
                commands["serial" if serial_axis else "parallel"] = command
                warmup = None
                if state == "warm-workspace":
                    warmup = _run_test_command(
                        benchmark_root,
                        command,
                        target=target,
                        profile=profile,
                        serial=serial_axis,
                        workers=workers,
                        commit=commit_before,
                        timeout_seconds=timeout_seconds,
                        cache_state="untimed-warmup",
                    )
                    if warmup.returncode != 0:
                        raise TestBenchmarkError("warmup controller failed after pytest execution")
                    if _git_output(benchmark_root, "status", "--porcelain", "--untracked-files=no"):
                        raise TestBenchmarkError("warmup changed tracked benchmark inputs")
                observations.append(
                    _run_test_command(
                        benchmark_root,
                        command,
                        target=target,
                        profile=profile,
                        serial=serial_axis,
                        workers=workers,
                        commit=commit_before,
                        timeout_seconds=timeout_seconds,
                        cache_state=state,
                    )
                )
                if warmup is not None:
                    _check_warmup(warmup, observations[-1])
                if _git_output(benchmark_root, "status", "--porcelain", "--untracked-files=no"):
                    raise TestBenchmarkError("test run changed tracked benchmark inputs")
            finally:
                _run_git_command(root, "worktree", "remove", "--force", str(benchmark_root))

    status_after = _git_output(root, "status", "--porcelain", "--untracked-files=normal")
    commit_after = _git_output(root, "rev-parse", "HEAD")
    checkout_unchanged = status_after == status_before and commit_after == commit_before
    if not checkout_unchanged:
        raise TestBenchmarkError("checkout changed during test benchmark")
    return build_test_performance_manifest(
        observations[0],
        observations[1],
        benchmarked_commit=commit_before,
        serial_argv=commands["serial"],
        parallel_argv=commands["parallel"],
        minimum_improvement_percent=minimum_improvement_percent,
        current_checkout_clean=checkout_unchanged,
        additional_runs=observations[2:],
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--target",
        choices=("pipeline-smoke", "infrastructure", "public-projects"),
        default="pipeline-smoke",
    )
    parser.add_argument("--profile", choices=("quick", "release", "exhaustive"), default="quick")
    parser.add_argument("--parallel-workers", type=int, default=None)
    parser.add_argument("--minimum-improvement", type=float, default=30.0)
    parser.add_argument("--timeout", type=float, default=3600.0)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the owned benchmark and write JSON evidence."""
    args = _build_parser().parse_args(argv)
    try:
        manifest = run_test_benchmark(
            args.repo_root,
            target=args.target,
            profile=args.profile,
            parallel_workers=args.parallel_workers,
            minimum_improvement_percent=args.minimum_improvement,
            timeout_seconds=args.timeout,
        )
    except TestBenchmarkError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest.to_dict(), indent=2, sort_keys=True))
    return 0 if manifest.acceptance_passed else 1


__all__ = [
    "TEST_BENCHMARK_SCHEMA",
    "TestBenchmarkError",
    "TestPerformanceManifest",
    "TestRunSummary",
    "_redact_output_tail",
    "build_test_command",
    "build_test_performance_manifest",
    "main",
    "run_test_benchmark",
]
