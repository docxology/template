"""Per-project pytest runner with isolated combined coverage gates.

Two ``projects/<name>/tests/conftest.py`` files cannot live in the same
``pytest`` process: pytest registers conftest plugins by directory-derived
name, so a second conftest with the same basename collides with the first
    # Prevent duplicate module registration when conftest plugins overlap.
``.github/workflows/ci.yml`` was an open-coded bash loop that invoked
``pytest`` once per ``projects/<name>/tests/`` directory, accumulating
coverage in one process per project, then combining those isolated files and
gating the union with ``coverage report --fail-under=<N>`` at the end.

This module lifts that loop into a single Python entry point so CI and
local runs share one implementation:

    from infrastructure.core.test_runner import run_per_project_pytest
    exit_code = run_per_project_pytest(repo_root)

The runner:

* discovers ``projects/<name>/tests/`` directories via
  :func:`infrastructure.project.discovery.discover_projects` (or accepts
  an explicit list),
* skips projects listed in ``skip_projects`` (default: ``("fep_lean",)``,
  which has its own dedicated CI job),
* invokes a real ``pytest`` subprocess **per project** so conftest
  plugins never collide,
* uses ``--cov=projects/<name>/src`` per project and an isolated coverage
  datafile for every subprocess,
* combines those per-project files only after all subprocesses exit, so an
  inherited infrastructure ``COVERAGE_FILE`` cannot contaminate the union,
* runs ``coverage report --fail-under=<fail_under>`` at the end and
  returns ``0`` only when **every** per-project pytest exited cleanly, every
  receipt-bearing lane preserved its project's ``output/`` tree, **and** the
  combined coverage gate passes.

The runner is a thin orchestrator: business logic (fail-under threshold,
skip list, marker expression) is configurable, and all subprocess work
happens through the shared process-group/timeout policy — no mocking.
"""

from dataclasses import dataclass
import hashlib
import io
from pathlib import Path
from time import monotonic
from typing import Sequence

from infrastructure.core.logging.utils import (
    get_logger,
    log_header,
    log_substep,
    log_success,
)
from infrastructure.core.project_test_matrix import ProjectTestTask, run_project_test_matrix
from infrastructure.core.public_matrix_receipt import (
    PublicMatrixLaneResult,
    build_public_matrix_receipt,
    build_public_matrix_cache_key,
    determine_worker_info,
)
from infrastructure.core.subprocess_policy import SubprocessPolicy, run_with_policy
from infrastructure.core.pytest_orchestration import (
    DEFAULT_TEST_PROFILE,
    TestProfileName,
    build_profile_marker_expression,
    build_union_pytest_command,
    make_coverage_subprocess_env,
    project_declared_coverage_floor,
    resolve_test_profile,
    validate_project_matrix_concurrency,
)
from infrastructure.core.runtime._python_env import get_python_command
from infrastructure.core.project_paths import resolve_project_root
from infrastructure.project.discovery import discover_projects
from infrastructure.project.metadata import get_project_metadata

logger = get_logger(__name__)

DEFAULT_SKIP_PROJECTS: tuple[str, ...] = ()
DEFAULT_COVERAGE_FILE: str = ".coverage.project"
DEFAULT_PROJECT_FAIL_UNDER: int = 90
# Combined-union floor for the multi-project run (`--project-only
# --all-projects`). This is deliberately distinct from — and lower than —
# the per-project standalone floor (90%, which exemplar projects meet:
# template_code_project ~100%, template_prose ~94%). The combined number is
# structurally lower because per-project suites only cover their own
# ``src/``; their union denominator spans every project included in the run.
# CI uses the public project scope, while local runs may opt into every
# discovered symlinked project. Maintainer decision (2026-05-15): keep the
# union gate at the measured public-project level rather than confuse it with
# per-project 90% floors, which remain the real quality gate.
DEFAULT_FAIL_UNDER: int = 75
DEFAULT_SUBPROCESS_TIMEOUT_SECONDS: int = 1800
_DEFAULT_MARKER = build_profile_marker_expression(resolve_test_profile(DEFAULT_TEST_PROFILE))
if _DEFAULT_MARKER is None:  # pragma: no cover - defensive
    raise RuntimeError("default pytest marker expression must not be empty")
DEFAULT_MARKER_EXPR: str = _DEFAULT_MARKER
DEFAULT_TIMEOUT: int = 120


@dataclass(frozen=True)
class ProjectPytestSpec:
    """One isolated project test subprocess within the union run."""

    index: int
    project_name: str
    project_root: Path
    tests_dir: Path
    coverage_file: Path
    cmd: list[str]
    env: dict[str, str]


@dataclass(frozen=True)
class ProjectPytestResult:
    """Outcome of one isolated project test subprocess."""

    index: int
    project_name: str
    exit_code: int
    coverage_file: Path
    timed_out: bool = False
    detail: str = ""
    duration_seconds: float = 0.0
    collection_count: int | None = None


def discover_skip_combined_pytest_projects(repo_root: Path) -> tuple[str, ...]:
    """Return project names that opt out of combined multi-project pytest."""
    skipped: list[str] = []
    for info in discover_projects(repo_root):
        flags = get_project_metadata(info.path).get("template_flags", {})
        if flags.get("skip_combined_pytest"):
            skipped.append(info.qualified_name)
    return tuple(sorted(skipped))


def _discover_project_test_dirs(
    repo_root: Path,
    projects: Sequence[str] | None,
    skip_projects: Sequence[str],
) -> tuple[list[tuple[str, Path, Path]], dict[str, str]]:
    """Return ``(project_name, project_root, tests_dir)`` for every runnable project.

    When ``projects`` is ``None`` the list is built from
    :func:`discover_projects`; otherwise the explicit list is resolved via
    :func:`resolve_project_root` so qualified paths such as
    ``templates/template_code_project`` work.
    """
    pairs: list[tuple[str, Path, Path]] = []
    skip_reasons: dict[str, str] = {}
    skip_set = set(skip_projects)

    if projects is None:
        for info in discover_projects(repo_root):
            tests_dir = info.path / "tests"
            qualified_name = info.qualified_name
            if qualified_name in skip_set or info.name in skip_set:
                logger.info("Skipping project '%s' (in skip_projects)", qualified_name)
                skip_reasons[qualified_name] = "configured skip_projects"
                continue
            if not _contains_tests(tests_dir):
                logger.warning("Discovered project '%s' has no runnable test files at %s", qualified_name, tests_dir)
                skip_reasons[qualified_name] = "error: no runnable test files"
                continue
            pairs.append((qualified_name, info.path, tests_dir))
        pairs.sort(key=lambda item: item[0])
    else:
        for name in projects:
            project_root = resolve_project_root(repo_root, name)
            tests_dir = project_root / "tests"
            if name in skip_set or Path(name).name in skip_set:
                logger.info("Skipping project '%s' (in skip_projects)", name)
                skip_reasons[name] = "configured skip_projects"
                continue
            if not _contains_tests(tests_dir):
                logger.error("Requested project '%s' has no runnable test files at %s", name, tests_dir)
                skip_reasons[name] = "error: no runnable test files"
                continue
            pairs.append((name, project_root, tests_dir))

    return pairs, skip_reasons


def _contains_tests(tests_dir: Path) -> bool:
    """Return true only for a real tests directory containing test modules."""
    return tests_dir.is_dir() and any(tests_dir.rglob("test_*.py"))


def _execute_project_pytest_matrix(
    repo_root: Path,
    specs: Sequence[ProjectPytestSpec],
    *,
    project_workers: int,
    subprocess_timeout_seconds: int,
    capture_output: bool = False,
) -> list[ProjectPytestResult]:
    """Run the shared bounded project matrix and adapt its result contract."""
    tasks = tuple(
        ProjectTestTask(
            index=spec.index,
            project_name=spec.project_name,
            command=tuple(spec.cmd),
            cwd=repo_root,
            env=spec.env,
            timeout_seconds=subprocess_timeout_seconds,
            capture_output=capture_output,
        )
        for spec in specs
    )
    results = run_project_test_matrix(tasks, workers=project_workers)
    coverage_by_index = {spec.index: spec.coverage_file for spec in specs}
    return [
        ProjectPytestResult(
            index=result.index,
            project_name=result.project_name,
            exit_code=result.returncode,
            coverage_file=coverage_by_index[result.index],
            timed_out=result.timed_out,
            detail=result.detail,
            duration_seconds=result.duration_seconds,
            collection_count=result.collection_count,
        )
        for result in results
    ]


def _run_combined_coverage_gate(
    repo_root: Path,
    env: dict[str, str],
    fail_under: int,
) -> int:
    """Run ``coverage report --fail-under=<N>`` and return its exit code."""
    log_substep(f"Running combined coverage gate (--fail-under={fail_under})", logger)
    cmd = get_python_command() + ["-m", "coverage", "report", f"--fail-under={fail_under}"]
    try:
        completed = run_with_policy(
            cmd,
            cwd=repo_root,
            env=env,
            policy=SubprocessPolicy(
                policy_id="coverage-gate",
                source_path="infrastructure/core/test_runner.py",
                timeout_seconds=300,
                capture_output=False,
            ),
        )
        return int(completed.returncode)
    except (OSError, ValueError) as exc:
        logger.error("coverage gate invocation failed: %s", exc)
        return 1


def _combine_project_coverage(
    repo_root: Path,
    combined_file: Path,
    project_files: Sequence[Path],
    env: dict[str, str],
) -> int:
    """Combine isolated project coverage files into *combined_file*."""
    existing = [path for path in project_files if path.is_file()]
    if not existing:
        logger.error("No isolated project coverage files were produced")
        return 1
    log_substep(f"Combining {len(existing)} isolated project coverage file(s)", logger)
    cmd = get_python_command() + [
        "-m",
        "coverage",
        "combine",
        f"--data-file={combined_file}",
        *[str(path) for path in existing],
    ]
    combine_env = dict(env)
    combine_env["COVERAGE_FILE"] = str(combined_file)
    try:
        completed = run_with_policy(
            cmd,
            cwd=repo_root,
            env=combine_env,
            policy=SubprocessPolicy(
                policy_id="coverage-combine",
                source_path="infrastructure/core/test_runner.py",
                timeout_seconds=300,
                capture_output=False,
            ),
        )
        return int(completed.returncode)
    except (OSError, ValueError) as exc:
        logger.error("coverage combine invocation failed: %s", exc)
        return 1


def _measure_coverage_percent(coverage_file: Path) -> float | None:
    """Return the total coverage percentage from one isolated coverage file.

    Uses the ``coverage`` Python API so the percentage is measured the same
    way pytest-cov reports it (branches included). Returns ``None`` when the
    file is missing or unreadable.
    """
    if not coverage_file.is_file():
        return None
    import coverage as coverage_module  # local import keeps startup fast

    try:
        cov = coverage_module.Coverage(data_file=str(coverage_file))
        cov.load()
        return float(cov.report(file=io.StringIO()))
    except (OSError, ValueError, coverage_module.CoverageException) as exc:
        logger.warning("Could not measure coverage from %s: %s", coverage_file, exc)
        return None


def _output_tree_digest(project_root: Path) -> str:
    """Return a content digest of the project's ``output/`` tree, or ``""``.

    Used to detect test-generated output churn: the digest is computed before
    and after a project lane, and the lane fails output isolation when they
    differ. Missing output trees digest to ``""`` (no churn possible).
    """
    output_dir = project_root / "output"
    if not output_dir.is_dir():
        return ""
    digest = hashlib.sha256()
    for path in sorted(output_dir.rglob("*")):
        if path.is_file():
            digest.update(path.relative_to(project_root).as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def _resolve_roster_revision(repo_root: Path) -> str:
    """Return the current git commit SHA, or ``"unknown"`` outside a checkout."""
    try:
        completed = run_with_policy(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            env=None,
            policy=SubprocessPolicy(
                policy_id="git-metadata-test-runner",
                source_path="infrastructure/core/test_runner.py",
                timeout_seconds=30,
                capture_output=True,
            ),
        )
    except (OSError, ValueError):
        return "unknown"
    if completed.returncode != 0:
        return "unknown"
    return completed.stdout.strip() or "unknown"


def _write_public_matrix_receipt(
    repo_root: Path,
    receipt_path: str | Path | None,
    *,
    specs: Sequence[ProjectPytestSpec],
    results: Sequence[ProjectPytestResult],
    output_digests_before: dict[str, str],
    profile: str,
    marker_expr: str | None,
    project_workers: str | int | None,
    parallel: str | int | None,
    combined_coverage_percent: float | None,
    combined_floor: int,
    overall_exit: int,
    phase_durations: dict[str, float] | None = None,
    skip_reasons: dict[str, str] | None = None,
) -> int:
    """Finalize output isolation and write a requested public-matrix receipt."""
    if receipt_path is None:
        return overall_exit

    lane_context: list[tuple[ProjectPytestResult, ProjectPytestSpec, float | None]] = []
    for result in results:
        spec = next(s for s in specs if s.index == result.index)
        coverage_percent = _measure_coverage_percent(result.coverage_file)
        lane_context.append((result, spec, coverage_percent))

    output_isolation: dict[int, bool] = {}
    for spec in specs:
        before = output_digests_before[spec.project_name]
        output_isolation[spec.index] = before == _output_tree_digest(spec.project_root)
        if not output_isolation[spec.index]:
            logger.error(
                "Project '%s' changed its output/ tree during the public-matrix run",
                spec.project_name,
            )
            overall_exit = 1

    worker_info = determine_worker_info(project_workers, parallel)
    roster_revision = _resolve_roster_revision(repo_root)
    cache_key = build_public_matrix_cache_key(
        roster_revision=roster_revision,
        profile=profile,
        marker_expression=marker_expr,
        worker_info=worker_info,
        project_names=[spec.project_name for spec in specs] + list((skip_reasons or {}).keys()),
    )
    lanes = []
    for result, spec, coverage_percent in lane_context:
        lanes.append(
            PublicMatrixLaneResult(
                project_name=result.project_name,
                declared_floor=project_declared_coverage_floor(spec.project_root),
                exit_code=result.exit_code,
                timed_out=result.timed_out,
                coverage_percent=coverage_percent,
                output_isolation_ok=output_isolation[spec.index],
                duration_seconds=result.duration_seconds,
                resource_profile=worker_info,
                skip_reason="",
                collection_count=result.collection_count,
                cache_key=cache_key,
            )
        )
    for project_name, reason in sorted((skip_reasons or {}).items()):
        is_error = reason.startswith("error:")
        if is_error:
            overall_exit = overall_exit or 1
        lanes.append(
            PublicMatrixLaneResult(
                project_name=project_name,
                declared_floor=None,
                exit_code=1 if is_error else 0,
                timed_out=False,
                coverage_percent=None,
                output_isolation_ok=True,
                duration_seconds=0.0,
                resource_profile=worker_info,
                skip_reason=reason,
                cache_key=cache_key,
            )
        )
    receipt = build_public_matrix_receipt(
        roster_revision=roster_revision,
        profile=profile,
        marker_expression=marker_expr,
        worker_info=worker_info,
        lanes=lanes,
        combined_coverage_percent=combined_coverage_percent,
        combined_floor=combined_floor,
        overall_exit=overall_exit,
        phase_durations=phase_durations,
        collection_counts={
            result.project_name: result.collection_count
            for result, _, _ in lane_context
            if result.collection_count is not None
        },
        skip_reasons=dict(skip_reasons or {}),
        cache_key=cache_key,
    )
    receipt.write(receipt_path)
    log_substep(f"Public-matrix receipt written: {receipt_path}", logger)
    return overall_exit


def run_per_project_pytest(
    repo_root: Path,
    *,
    projects: Sequence[str] | None = None,
    skip_projects: Sequence[str] | None = None,
    profile: TestProfileName = DEFAULT_TEST_PROFILE,
    include_slow: bool = False,
    include_long_running: bool = False,
    include_ollama_tests: bool = False,
    include_bench: bool = False,
    coverage_file: str = DEFAULT_COVERAGE_FILE,
    fail_under: int = DEFAULT_FAIL_UNDER,
    marker_expr: str | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    project_workers: str | int | None = None,
    subprocess_timeout_seconds: int = DEFAULT_SUBPROCESS_TIMEOUT_SECONDS,
    parallel: str | int | None = None,
    allow_empty: bool = False,
    receipt_path: str | Path | None = None,
) -> int:
    """Run pytest once per project and gate combined coverage.

    Args:
        repo_root: Repository root directory containing ``projects/``.
        projects: Optional explicit project names to run. When ``None`` the
            project list is derived from
            :func:`infrastructure.project.discovery.discover_projects`.
        skip_projects: Project names to skip even if discovered. When ``None``,
            projects with ``[tool.template] skip_combined_pytest = true`` in
            ``pyproject.toml`` are skipped automatically.
        coverage_file: Path to the combined coverage data file. Ambient
            ``COVERAGE_FILE`` is deliberately ignored so an enclosing
            infrastructure coverage run cannot contaminate this union.
            Default: ``".coverage.project"``.
        fail_under: Minimum combined coverage percentage required by the
            final ``coverage report`` gate.
        marker_expr: ``pytest -m`` expression. ``None`` uses
            :data:`DEFAULT_MARKER_EXPR` (the deterministic lane excluding live
            services, timing tests, and benchmark aliases). Pass ``""`` to
            omit ``-m`` (collect all markers).
        timeout: Per-test ``--timeout`` value forwarded to pytest.
        parallel: Opt-in pytest-xdist worker count (``"auto"`` or a positive
            integer). ``None`` falls back to the ``PYTEST_XDIST_WORKERS`` env
            var, and finally to serial. Coverage is unaffected — pytest-cov
            combines per-worker data before each project's ``--cov-append``.
        allow_empty: Explicitly permit a zero-project run. Defaults to false so
            discovery drift and misspelled explicit project names fail closed.
        receipt_path: When set, write a deterministic public-matrix receipt
            (roster revision, profile, per-project floor/exit/timeout/coverage/
            output-isolation) to this path after the run. Written even on
            failure so the evidence is preserved for release review.

    Returns:
        ``0`` only when **every** per-project pytest exited cleanly **and**
        the combined coverage gate passes. ``1`` otherwise.
    """
    log_header("Per-project pytest runner", logger)

    if subprocess_timeout_seconds <= 0:
        raise ValueError("subprocess_timeout_seconds must be positive")

    effective_skip = (
        tuple(skip_projects) if skip_projects is not None else discover_skip_combined_pytest_projects(repo_root)
    )

    outer_workers = validate_project_matrix_concurrency(project_workers, parallel)

    pairs, skip_reasons = _discover_project_test_dirs(repo_root, projects, effective_skip)
    if not pairs:
        message = "No runnable projects with test modules were found."
        empty_reason = "configured empty run" if allow_empty else f"error: {message}"
        skip_reasons = dict(skip_reasons)
        skip_reasons["<no-runnable-projects>"] = empty_reason
        if allow_empty:
            logger.warning("%s Empty runs were explicitly allowed.", message)
        else:
            logger.error("%s", message)
        if receipt_path is not None:
            _write_public_matrix_receipt(
                repo_root,
                receipt_path,
                specs=(),
                results=(),
                output_digests_before={},
                profile=profile,
                marker_expr=marker_expr,
                project_workers=project_workers,
                parallel=parallel,
                combined_coverage_percent=None,
                combined_floor=fail_under,
                overall_exit=0 if allow_empty else 1,
                phase_durations={"project_matrix": 0.0, "coverage_combine": 0.0, "coverage_gate": 0.0},
                skip_reasons=skip_reasons,
            )
        return 0 if allow_empty else 1

    resolved_markers = marker_expr
    if resolved_markers is None:
        resolved_markers = build_profile_marker_expression(
            resolve_test_profile(
                profile,
                include_slow=include_slow,
                include_long_running=include_long_running,
                include_ollama_tests=include_ollama_tests,
                include_bench=include_bench,
            )
        )
    elif resolved_markers == "":
        resolved_markers = None

    # Use the caller's explicit path, never an inherited COVERAGE_FILE. The
    # parent process may itself be running under pytest-cov with
    # ``.coverage.infra``; reusing that file would silently mix suites.
    cf_path = Path(coverage_file)
    if not cf_path.is_absolute():
        cf_path = repo_root / cf_path
    if cf_path.exists():
        try:
            cf_path.unlink()
            logger.debug("Removed stale coverage file: %s", cf_path)
        except OSError as exc:  # pragma: no cover - filesystem oddity
            logger.warning("Could not remove stale coverage file %s: %s", cf_path, exc)

    project_coverage_files: list[Path] = []
    base_env = make_coverage_subprocess_env(str(cf_path), repo_root)

    logger.info("Will run %d project(s):", len(pairs))
    for name, project_root, tests_dir in pairs:
        logger.info("  - %s (%s)", name, tests_dir)
    logger.info("Outer project workers: %d", outer_workers)

    specs: list[ProjectPytestSpec] = []
    for index, (project_name, project_root, tests_dir) in enumerate(pairs):
        safe_name = project_name.replace("/", "_").replace("\\", "_")
        project_coverage_file = cf_path.with_name(f"{cf_path.name}.{index:02d}-{safe_name}")
        if project_coverage_file.exists():
            try:
                project_coverage_file.unlink()
            except OSError as exc:  # pragma: no cover - filesystem oddity
                logger.warning("Could not remove stale project coverage file %s: %s", project_coverage_file, exc)
        project_env = make_coverage_subprocess_env(str(project_coverage_file), repo_root)
        project_env["PYTHONPATH"] = base_env.get("PYTHONPATH", "")
        project_floor = project_declared_coverage_floor(project_root) or DEFAULT_PROJECT_FAIL_UNDER
        cmd = build_union_pytest_command(
            repo_root,
            project_root,
            tests_dir,
            is_first=(index == 0),
            marker_expr=resolved_markers,
            timeout=timeout,
            parallel=parallel,
            fail_under=project_floor,
        )
        specs.append(
            ProjectPytestSpec(
                index=index,
                project_name=project_name,
                project_root=project_root,
                tests_dir=tests_dir,
                coverage_file=project_coverage_file,
                cmd=cmd,
                env=project_env,
            )
        )

    output_digests_before: dict[str, str] = {}
    if receipt_path is not None:
        output_digests_before = {spec.project_name: _output_tree_digest(spec.project_root) for spec in specs}

    matrix_started = monotonic()
    results = _execute_project_pytest_matrix(
        repo_root,
        specs,
        project_workers=outer_workers,
        subprocess_timeout_seconds=subprocess_timeout_seconds,
        capture_output=receipt_path is not None,
    )
    matrix_duration = round(monotonic() - matrix_started, 3)
    overall_exit = 0
    if len(results) != len(specs):
        logger.error("Project test matrix returned %d result(s) for %d project(s)", len(results), len(specs))
        overall_exit = 1

    for result in results:
        project_coverage_files.append(result.coverage_file)
        if result.exit_code == 0:
            log_success(f"Project '{result.project_name}' tests passed", logger)
        elif result.timed_out:
            logger.error("Project '%s' tests timed out (%s)", result.project_name, result.detail)
            overall_exit = 1
        else:
            logger.error("Project '%s' tests failed (exit=%d)", result.project_name, result.exit_code)
            overall_exit = result.exit_code or overall_exit or 1
        if result.exit_code == 0 and not result.coverage_file.is_file():
            logger.error(
                "Project '%s' reported success but did not produce isolated coverage file %s",
                result.project_name,
                result.coverage_file,
            )
            overall_exit = 1

    combine_started = monotonic()
    combine_rc = _combine_project_coverage(repo_root, cf_path, project_coverage_files, base_env)
    combine_duration = round(monotonic() - combine_started, 3)
    if combine_rc != 0:
        overall_exit = overall_exit or combine_rc
    final_env = make_coverage_subprocess_env(str(cf_path), repo_root)
    coverage_started = monotonic()
    cov_rc = _run_combined_coverage_gate(repo_root, final_env, fail_under)
    coverage_duration = round(monotonic() - coverage_started, 3)
    if cov_rc == 0:
        log_success(f"Combined coverage gate passed (>= {fail_under}%)", logger)
    else:
        logger.error("Combined coverage gate failed (exit=%d)", cov_rc)
        overall_exit = overall_exit or cov_rc or 1

    combined_pct: float | None = None
    if cf_path.is_file():
        imported_pct = _measure_coverage_percent(cf_path)
        combined_pct = imported_pct
    overall_exit = _write_public_matrix_receipt(
        repo_root,
        receipt_path,
        specs=specs,
        results=results,
        output_digests_before=output_digests_before,
        profile=profile,
        marker_expr=resolved_markers,
        project_workers=project_workers,
        parallel=parallel,
        combined_coverage_percent=combined_pct,
        combined_floor=fail_under,
        overall_exit=overall_exit,
        phase_durations={
            "project_matrix": matrix_duration,
            "coverage_combine": combine_duration,
            "coverage_gate": coverage_duration,
        },
        skip_reasons=skip_reasons,
    )

    return 0 if overall_exit == 0 else 1


__all__ = [
    "DEFAULT_COVERAGE_FILE",
    "DEFAULT_FAIL_UNDER",
    "DEFAULT_MARKER_EXPR",
    "DEFAULT_PROJECT_FAIL_UNDER",
    "DEFAULT_SKIP_PROJECTS",
    "DEFAULT_SUBPROCESS_TIMEOUT_SECONDS",
    "DEFAULT_TIMEOUT",
    "discover_skip_combined_pytest_projects",
    "run_per_project_pytest",
]
