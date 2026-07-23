"""Owned serial-versus-parallel evidence for the canonical test lanes."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess  # nosec B404 - fixed repository entrypoint and argv
import tempfile
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from time import monotonic
from typing import Literal, Sequence

from infrastructure.core.pytest_orchestration import resolve_project_matrix_workers

TestBenchmarkTarget = Literal["pipeline-smoke", "infrastructure", "public-projects"]
TEST_BENCHMARK_SCHEMA = "template-test-performance-v1"


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

    def to_dict(self) -> dict[str, object]:
        """Serialize the manifest with stable nested dataclass fields."""
        return asdict(self)


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
) -> TestRunSummary:
    started = monotonic()
    try:
        process = subprocess.run(  # noqa: S603 - fixed repository command
            command,
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise TestBenchmarkError(f"test benchmark timed out: {' '.join(command)}") from exc
    output = f"{process.stdout}\n{process.stderr}".strip()
    return TestRunSummary(
        target=target,
        profile=profile,
        selection=(target, profile),
        axis="serial" if serial else "parallel",
        workers=1 if serial else workers,
        returncode=process.returncode,
        wall_elapsed_seconds=round(monotonic() - started, 3),
        repo_commit=commit,
        output_tail=output[-4000:],
    )


def build_test_performance_manifest(
    serial: TestRunSummary,
    parallel: TestRunSummary,
    *,
    benchmarked_commit: str,
    serial_argv: tuple[str, ...],
    parallel_argv: tuple[str, ...],
    minimum_improvement_percent: float = 10.0,
    current_checkout_clean: bool = True,
) -> TestPerformanceManifest:
    """Compare owned run summaries and compute a fail-closed acceptance result."""
    if serial.axis != "serial" or serial.workers != 1:
        raise TestBenchmarkError("serial evidence must use one serial worker")
    if parallel.axis != "parallel" or parallel.workers <= 1:
        raise TestBenchmarkError("parallel evidence must use more than one worker")
    if serial.wall_elapsed_seconds <= 0 or parallel.wall_elapsed_seconds <= 0:
        raise TestBenchmarkError("test benchmark wall times must be positive")
    if minimum_improvement_percent < 0 or minimum_improvement_percent >= 100:
        raise TestBenchmarkError("minimum improvement must be in the range [0, 100)")
    improvement = (serial.wall_elapsed_seconds - parallel.wall_elapsed_seconds) / serial.wall_elapsed_seconds * 100.0
    selection_matches = (
        serial.target == parallel.target
        and serial.profile == parallel.profile
        and serial.selection == parallel.selection
    )
    provenance_matches = (
        serial.repo_commit == parallel.repo_commit == benchmarked_commit
        and serial.target == parallel.target
        and current_checkout_clean
    )
    both_runs_passed = serial.returncode == 0 and parallel.returncode == 0
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
        acceptance_passed=(
            current_checkout_clean
            and selection_matches
            and provenance_matches
            and both_runs_passed
            and improvement >= minimum_improvement_percent
        ),
    )


def run_test_benchmark(
    repo_root: Path,
    *,
    target: TestBenchmarkTarget = "pipeline-smoke",
    profile: str = "quick",
    parallel_workers: int | None = None,
    minimum_improvement_percent: float = 10.0,
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
    with tempfile.TemporaryDirectory(prefix="template-test-benchmark-") as temp_dir:
        benchmark_root = Path(temp_dir) / "checkout"
        _run_git_command(root, "worktree", "add", "--detach", "--quiet", str(benchmark_root), commit_before)
        try:
            serial_argv = build_test_command(
                benchmark_root,
                target=target,
                profile=profile,
                serial=True,
                parallel_workers=workers,
            )
            parallel_argv = build_test_command(
                benchmark_root,
                target=target,
                profile=profile,
                serial=False,
                parallel_workers=workers,
            )
            serial = _run_test_command(
                benchmark_root,
                serial_argv,
                target=target,
                profile=profile,
                serial=True,
                workers=workers,
                commit=commit_before,
                timeout_seconds=timeout_seconds,
            )
            parallel = _run_test_command(
                benchmark_root,
                parallel_argv,
                target=target,
                profile=profile,
                serial=False,
                workers=workers,
                commit=commit_before,
                timeout_seconds=timeout_seconds,
            )
        finally:
            _run_git_command(root, "worktree", "remove", "--force", str(benchmark_root))

    status_after = _git_output(root, "status", "--porcelain", "--untracked-files=normal")
    commit_after = _git_output(root, "rev-parse", "HEAD")
    checkout_unchanged = status_after == status_before and commit_after == commit_before
    if not checkout_unchanged:
        raise TestBenchmarkError("checkout changed during test benchmark")
    return build_test_performance_manifest(
        serial,
        parallel,
        benchmarked_commit=commit_before,
        serial_argv=serial_argv,
        parallel_argv=parallel_argv,
        minimum_improvement_percent=minimum_improvement_percent,
        current_checkout_clean=checkout_unchanged,
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
    parser.add_argument("--minimum-improvement", type=float, default=10.0)
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
    "build_test_command",
    "build_test_performance_manifest",
    "run_test_benchmark",
    "main",
]
