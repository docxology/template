"""Run the deterministic public-exemplar test readiness matrix."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from contextlib import ExitStack
from dataclasses import asdict, dataclass
from pathlib import Path

from infrastructure.core.project_test_matrix import ProjectTestTask, run_project_test_matrix
from infrastructure.core.pytest_orchestration import (
    TestProfileName,
    parse_project_workers,
    resolve_test_profile,
)
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

PUBLIC_READINESS_SCHEMA = "template-public-readiness-v2"
PUBLIC_READINESS_PYTHON = "3.12"
DEFAULT_TIMEOUT_SECONDS = 1200
PUBLIC_READINESS_STATUSES = frozenset({"pass", "fail", "skip"})
_OUTPUT_TAIL_LIMIT = 4000


@dataclass(frozen=True)
class PublicReadinessResult:
    """Result for one public exemplar test subprocess."""

    project: str
    status: str
    returncode: int | None
    duration_seconds: float
    command: tuple[str, ...]
    output_tail: str = ""


@dataclass(frozen=True)
class PublicReadinessReport:
    """Machine-readable aggregate for the public readiness matrix."""

    results: tuple[PublicReadinessResult, ...]
    expected_projects: tuple[str, ...]
    profile: TestProfileName = "release"
    project_workers: int = 1

    @property
    def counts(self) -> dict[str, int]:
        """Return stable status counts."""
        counts = {"pass": 0, "fail": 0, "skip": 0}
        for result in self.results:
            counts[result.status] = counts.get(result.status, 0) + 1
        return dict(sorted(counts.items()))

    @property
    def missing_projects(self) -> tuple[str, ...]:
        """Return expected public projects absent from this checkout."""
        return tuple(result.project for result in self.results if result.returncode is None)

    def exit_code(self, *, allow_skips: bool = False) -> int:
        """Return zero only when the roster is complete and all results pass."""
        if self.missing_projects:
            return 1
        if any(result.status not in PUBLIC_READINESS_STATUSES for result in self.results):
            return 1
        if any(result.status == "fail" for result in self.results):
            return 1
        if not allow_skips and any(result.status == "skip" for result in self.results):
            return 1
        return 0

    def to_dict(self) -> dict[str, object]:
        """Serialize the report for CI and local tooling."""
        return {
            "schema_version": PUBLIC_READINESS_SCHEMA,
            "python_version": PUBLIC_READINESS_PYTHON,
            "expected_projects": list(self.expected_projects),
            "profile": self.profile,
            "project_workers": self.project_workers,
            "counts": self.counts,
            "missing_projects": list(self.missing_projects),
            "results": [asdict(result) for result in self.results],
        }


def run_public_readiness(
    repo_root: Path,
    *,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    include_ollama_tests: bool = False,
    profile: TestProfileName = "release",
    project_workers: str | int | None = None,
) -> PublicReadinessReport:
    """Run one isolated project-test subprocess for every public exemplar.

    The readiness lane defaults to the deterministic ``release`` profile,
    retaining the historical slow-test coverage while excluding long-running
    and live-service tests. ``project_workers`` controls only the outer
    project matrix; nested pytest-xdist is not introduced by this gate.
    """
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    resolved_profile = resolve_test_profile(profile, include_ollama_tests=include_ollama_tests)
    workers = parse_project_workers(project_workers)
    root = repo_root.resolve()
    expected = tuple(sorted(PUBLIC_PROJECT_NAMES))
    # The public roster is already qualified under ``projects/templates``;
    # inspect those exact paths so JSON mode is not polluted by discovery
    # diagnostics when a checkout is incomplete.
    projects_root = root / "projects"
    templates_root = projects_root / "templates"
    real_public_scope = all(not path.is_symlink() for path in (projects_root, templates_root))
    present = {
        project
        for project in expected
        if real_public_scope and (project_dir := root / "projects" / project).is_dir() and not project_dir.is_symlink()
    }
    results: list[PublicReadinessResult] = []

    with ExitStack() as stack:
        tasks: list[ProjectTestTask] = []
        commands: dict[str, tuple[str, ...]] = {}
        for index, project in enumerate(expected):
            if project not in present:
                continue
            safe_name = project.replace("/", "_")
            command: tuple[str, ...] = (
                sys.executable,
                str(root / "scripts" / "pipeline" / "stage_01_test.py"),
                "--project",
                project,
                "--project-only",
                "--profile",
                resolved_profile.name,
            )
            if include_ollama_tests:
                command += ("--include-ollama-tests",)
            temp_dir = stack.enter_context(
                tempfile.TemporaryDirectory(prefix=f"template-public-readiness-{safe_name}-")
            )
            env = os.environ.copy()
            # Keep coverage scratch space outside the checkout. The project
            # subprocesses already write canonical reports under each exemplar;
            # this lane should not additionally pollute the repository root.
            env["COVERAGE_FILE"] = str(Path(temp_dir) / ".coverage")
            # Pin the interpreter used by nested ``uv run`` project commands
            # so readiness evidence remains reproducible across macOS hosts.
            env["UV_PYTHON"] = PUBLIC_READINESS_PYTHON
            commands[project] = command
            tasks.append(
                ProjectTestTask(
                    index=index,
                    project_name=project,
                    command=command,
                    cwd=root,
                    env=env,
                    timeout_seconds=timeout_seconds,
                    capture_output=True,
                )
            )

        matrix_results = {result.project_name: result for result in run_project_test_matrix(tasks, workers=workers)}
        for project in expected:
            if project not in present:
                results.append(
                    PublicReadinessResult(
                        project=project,
                        status="fail",
                        returncode=None,
                        duration_seconds=0.0,
                        command=(),
                        output_tail="Public project is missing from the checkout.",
                    )
                )
                continue
            result = matrix_results[project]
            returncode = result.returncode
            status = "pass" if returncode == 0 else "skip" if returncode == 2 else "fail"
            output = result.output_tail or result.detail
            results.append(
                PublicReadinessResult(
                    project=project,
                    status=status,
                    returncode=returncode,
                    duration_seconds=result.duration_seconds,
                    command=commands[project],
                    output_tail=output[-_OUTPUT_TAIL_LIMIT:],
                )
            )

    return PublicReadinessReport(tuple(results), expected, profile=resolved_profile.name, project_workers=workers)


def format_public_readiness(report: PublicReadinessReport) -> str:
    """Format a compact human-readable readiness summary."""
    lines = [
        (
            f"Public readiness: {len(report.results)} expected exemplar(s) "
            f"[{report.profile}, workers={report.project_workers}]"
        ),
        *(f"{result.status.upper():4} {result.project} ({result.duration_seconds:.1f}s)" for result in report.results),
        f"Counts: {json.dumps(report.counts, sort_keys=True)}",
    ]
    return "\n".join(lines)


__all__ = [
    "DEFAULT_TIMEOUT_SECONDS",
    "PUBLIC_READINESS_PYTHON",
    "PUBLIC_READINESS_SCHEMA",
    "PUBLIC_READINESS_STATUSES",
    "PublicReadinessReport",
    "PublicReadinessResult",
    "format_public_readiness",
    "run_public_readiness",
]
