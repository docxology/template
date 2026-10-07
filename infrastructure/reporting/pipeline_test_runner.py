"""Test orchestration module.

Thin facade over :mod:`infrastructure.core.pytest_orchestration` and
:mod:`infrastructure.reporting.suite_runner` for Stage 01 test execution.
"""

from __future__ import annotations

import os
import tempfile
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from infrastructure.core.config.queries import get_testing_config
from infrastructure.core.files.coverage_cleanup import clean_coverage_files
from infrastructure.core.files.project_lock import project_output_lock
from infrastructure.core.logging.utils import get_logger, log_header, log_substep, log_success
from infrastructure.core.testing.pytest_orchestration import (
    DEFAULT_TEST_PROFILE,
    INFRASTRUCTURE_TEST_SCOPES,
    InfrastructureTestScope,
    TestSuiteResults,
    TestProfileName,
    apply_coverage_datafile,
    build_profile_marker_expression,
    build_project_pytest_command,
    build_pythonpath,
    discovery_preflight_enabled,
    enforce_project_suite_guards,
    log_discovered_tests,
    parse_test_discovery_timeout,
    prepend_uv_to_path,
    project_declared_coverage_floor,
    project_declared_test_command,
    resolve_test_profile,
    resolve_project_cov_config,
    resolve_infrastructure_test_paths,
    validate_coverage_parallel,
    resolve_xdist_args,
)
from infrastructure.core.testing.project_test_runtime import (
    ProjectTestRuntimeError,
    admit_project_test_runtime,
    build_audited_project_test_command,
    project_test_deadline,
    remaining_test_budget,
)
from infrastructure.core.runtime.python_binding import analysis_runtime_binding
from infrastructure.core.pipeline.outcomes import RunResult, StageOutcome, StageStatus
from infrastructure.project.discovery import resolve_project_root
from infrastructure.reporting.report_generator import generate_test_report, save_test_report_to_files
from infrastructure.reporting.pipeline_test_reporting import (
    report_infra_only_results,
    report_results,
)
from infrastructure.reporting.project_verifier import ProjectVerifierError, run_declared_project_verifier
from infrastructure.reporting.suite_runner import (
    DEFAULT_SINGLE_PROJECT_TEST_TIMEOUT_SECONDS,
    DEFAULT_TEST_SUITE_TIMEOUT_SECONDS,
    TestSuiteConfig,
    run_test_suite,
)

logger = get_logger(__name__)


def _build_infrastructure_suite_config(
    *,
    cmd: list[str],
    env: dict[str, str],
    repo_root: Path,
    coverage_json_paths: list[Path],
    coverage_threshold: float,
    quiet: bool,
    scope: InfrastructureTestScope,
) -> TestSuiteConfig:
    """Build the infrastructure Stage-01 execution contract."""
    return TestSuiteConfig(
        label="Infrastructure",
        cmd=cmd,
        env=env,
        repo_root=repo_root,
        coverage_json_paths=coverage_json_paths,
        coverage_threshold=coverage_threshold,
        max_failures_env_var="MAX_INFRA_TEST_FAILURES",
        max_failures_config_key="max_infra_test_failures",
        quiet=quiet,
        spinner_label=f"Running infrastructure tests ({scope})",
        streaming_subprocess=True,
        coverage_cleanup_scope_dir=None,
        coverage_cleanup_recursive=False,
    )


def _build_generic_project_suite_config(
    *,
    project_name: str,
    project_root: Path,
    repo_root: Path,
    cmd: list[str],
    env: dict[str, str],
    coverage_threshold: float,
    quiet: bool,
) -> TestSuiteConfig:
    """Build the generic single-project Stage-01 execution contract.

    Generic pytest and an explicitly declared project verifier share the same
    single-project timeout capacity.  The larger budget only prevents the
    runner from terminating an otherwise valid long suite prematurely; it is
    not evidence that the suite completed or passed.
    """
    return TestSuiteConfig(
        label="Project",
        cmd=cmd,
        env=env,
        repo_root=project_root,
        coverage_json_paths=[
            project_root / "coverage_project.json",
            project_root / "coverage.json",
            project_root / "htmlcov" / "coverage.json",
        ],
        coverage_threshold=coverage_threshold,
        max_failures_env_var="MAX_PROJECT_TEST_FAILURES",
        max_failures_config_key="max_project_test_failures",
        quiet=quiet,
        spinner_label=f"Running project tests for '{project_name}'",
        streaming_subprocess=True,
        timeout_seconds=DEFAULT_SINGLE_PROJECT_TEST_TIMEOUT_SECONDS,
        total_timeout_seconds=DEFAULT_SINGLE_PROJECT_TEST_TIMEOUT_SECONDS,
        coverage_cleanup_scope_dir=project_root,
        coverage_cleanup_recursive=True,
    )


def run_infrastructure_tests(
    repo_root: Path,
    project_name: str = "project",
    quiet: bool = True,
    include_slow: bool = False,
    include_ollama_tests: bool = False,
    include_bench: bool = False,
    strict: bool = True,
    scope: InfrastructureTestScope = "full",
    parallel: str | int | None = None,
    *,
    profile: TestProfileName = DEFAULT_TEST_PROFILE,
    include_long_running: bool = False,
) -> tuple[int, TestSuiteResults]:
    """Execute infrastructure test suite with coverage.

    *parallel* opts the run into pytest-xdist (``"auto"`` or an integer worker
    count); ``None`` falls back to ``PYTEST_XDIST_WORKERS`` then serial.
    """
    if scope not in INFRASTRUCTURE_TEST_SCOPES:
        raise ValueError(f"Unknown infrastructure test scope: {scope}")
    if scope == "full":
        validate_coverage_parallel(parallel)
    start_time = time.time()
    project_root = resolve_project_root(repo_root, project_name)

    testing_config = get_testing_config(repo_root)
    full_scope = scope == "full"
    infra_threshold = testing_config.infra_coverage_threshold if full_scope else 0

    if full_scope:
        log_substep(f"Running infrastructure tests ({infra_threshold}% coverage threshold)...", logger)
    else:
        log_substep("Running pipeline-smoke infrastructure tests (no coverage gate)...", logger)
    if not include_ollama_tests:
        log_substep("(Skipping LLM integration tests - run separately with: pytest -m requires_ollama)", logger)
    logger.info("Infrastructure test scope: %s", scope)
    logger.info("Test path(s): %s", ", ".join(resolve_infrastructure_test_paths(repo_root, scope)))
    if full_scope:
        logger.info("Coverage target: infrastructure (%s%% minimum)", infra_threshold)
    else:
        logger.info("Coverage target: N/A for pipeline-smoke scope")

    selection = resolve_test_profile(
        profile,
        include_slow=include_slow,
        include_long_running=include_long_running,
        include_ollama_tests=include_ollama_tests,
        include_bench=include_bench,
    )
    try:
        deadline = project_test_deadline(DEFAULT_TEST_SUITE_TIMEOUT_SECONDS)
        selected, runtime = admit_project_test_runtime(repo_root, deadline=deadline)
    except ProjectTestRuntimeError as exc:
        logger.error("Infrastructure test prepared runtime refused: %s", exc)
        return exc.exit_code, cast(
            TestSuiteResults, {"exit_code": exc.exit_code, "original_exit_code": exc.original_exit_code}
        )
    cmd: list[str] = []
    cmd.extend(resolve_infrastructure_test_paths(repo_root, scope))
    if full_scope:
        cmd.append("--cov=infrastructure")
    infra_marker = build_profile_marker_expression(selection)
    if infra_marker:
        cmd.extend(["-m", infra_marker])
    cmd.extend(resolve_xdist_args(parallel))

    env = os.environ.copy()
    env.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "matplotlib"))
    coverage_json_paths: list[Path] = []
    if full_scope:
        apply_coverage_datafile(cmd, env, ".coverage.infra")
        coverage_json_paths = [
            repo_root / "coverage_infra.json",
            repo_root / "coverage.json",
            repo_root / "htmlcov" / "coverage.json",
        ]
        cmd.extend(
            [
                "--cov-report=term-missing",
                "--cov-report=html",
                "--cov-report=json:coverage_infra.json",
                f"--cov-fail-under={infra_threshold}",
            ]
        )
    cmd.append("--tb=short")
    if quiet:
        cmd.extend(["-q"])

    env["PYTHONPATH"] = build_pythonpath(repo_root, project_root)
    prepend_uv_to_path(env)

    try:
        cmd = list(
            build_audited_project_test_command(repo_root, selected, tuple(cmd), module="pytest", deadline=deadline)
        )
    except ProjectTestRuntimeError as exc:
        logger.error("Infrastructure provider-root discovery refused: %s", exc)
        return exc.exit_code, cast(
            TestSuiteResults, {"exit_code": exc.exit_code, "original_exit_code": exc.original_exit_code}
        )

    # Admission and command construction precede mutation of existing evidence.
    # Root-only cleanup preserves concurrently running lifecycle projects.
    clean_coverage_files(repo_root, recursive=False)

    if discovery_preflight_enabled(env=env):
        log_discovered_tests(
            cmd,
            repo_root,
            env,
            f"infrastructure ({scope})",
            timeout_seconds=parse_test_discovery_timeout(scope),
        )

    test_results: dict[str, Any] = {}
    try:
        config = _build_infrastructure_suite_config(
            cmd=cmd,
            env=env,
            repo_root=repo_root,
            coverage_json_paths=coverage_json_paths,
            coverage_threshold=infra_threshold,
            quiet=quiet,
            scope=scope,
        )
        capacity = remaining_test_budget(deadline)
        config.timeout_seconds = capacity
        config.total_timeout_seconds = capacity
        exit_code, test_results = run_test_suite(config)
        test_results.setdefault("original_exit_code", exit_code)
        exit_code = _test_child_exit_code(exit_code, test_results)
        if strict and test_results.get("failed", 0) > 0 and exit_code not in (2, 75, 124, 130):
            exit_code = 1
        try:
            unchanged_runtime = analysis_runtime_binding(repo_root, interpreter=selected) == runtime["binding"]
        except (OSError, ValueError) as exc:
            logger.error("Infrastructure prepared runtime custody refused after child: %s", exc)
            unchanged_runtime = False
        if not unchanged_runtime and exit_code == 0:
            exit_code = 75
        test_results["selected_runtime"] = runtime
        if exit_code == 0:
            remaining_test_budget(deadline)
        test_results["exit_code"] = exit_code
        duration = time.time() - start_time
        logger.info("Infrastructure test suite completed in %.1fs", duration)
        if exit_code == 0:
            log_success("Infrastructure tests passed", logger)
        return exit_code, cast(TestSuiteResults, test_results)
    except (OSError, RuntimeError, ValueError) as exc:
        duration = time.time() - start_time
        logger.error("Failed to run infrastructure tests after %.1fs: %s", duration, exc, exc_info=True)
        code = getattr(exc, "exit_code", 1)
        test_results.setdefault("original_exit_code", getattr(exc, "original_exit_code", None))
        test_results.setdefault("diagnostic", str(exc))
        test_results["exit_code"] = code
        return code, cast(TestSuiteResults, test_results)


def run_project_tests(
    repo_root: Path,
    project_name: str = "project",
    quiet: bool = True,
    include_slow: bool = False,
    include_long_running: bool = False,
    include_bench: bool = False,
    strict: bool = True,
    include_ollama_tests: bool = False,
    parallel: str | int | None = None,
    *,
    profile: TestProfileName = DEFAULT_TEST_PROFILE,
) -> tuple[int, TestSuiteResults]:
    """Execute the project test suite under the per-project output lock.

    The lock serializes this run against any concurrent pipeline/test run on the
    same project so a Stage-1 Clean cannot delete ``output/`` while these gate
    tests read it. It is cross-process re-entrant: when invoked as the pipeline's
    test stage (a subprocess of a run that already holds the lock) the
    acquisition is a no-op, so it never deadlocks against the parent pipeline.
    """
    with project_output_lock(resolve_project_root(repo_root, project_name)):
        return _run_project_tests_impl(
            repo_root,
            project_name,
            quiet=quiet,
            profile=profile,
            include_slow=include_slow,
            include_long_running=include_long_running,
            include_bench=include_bench,
            strict=strict,
            include_ollama_tests=include_ollama_tests,
            parallel=parallel,
        )


def _run_project_tests_impl(
    repo_root: Path,
    project_name: str = "project",
    quiet: bool = True,
    include_slow: bool = False,
    include_long_running: bool = False,
    include_bench: bool = False,
    strict: bool = True,
    include_ollama_tests: bool = False,
    parallel: str | int | None = None,
    *,
    profile: TestProfileName = DEFAULT_TEST_PROFILE,
) -> tuple[int, TestSuiteResults]:
    """Execute project test suite with coverage (assumes the output lock is held)."""
    start_time = time.time()
    deadline = project_test_deadline(DEFAULT_SINGLE_PROJECT_TEST_TIMEOUT_SECONDS)
    project_root = resolve_project_root(repo_root, project_name)

    testing_config = get_testing_config(repo_root)
    declared_floor = project_declared_coverage_floor(project_root)
    project_threshold = declared_floor if declared_floor is not None else testing_config.project_coverage_threshold

    log_substep(f"Running project tests for '{project_name}' ({project_threshold}% coverage threshold)...", logger)
    logger.info("Test path: %s", project_root / "tests")
    logger.info("Coverage target: %s (%s%% minimum)", project_root / "src", project_threshold)

    try:
        declared_command = project_declared_test_command(project_root)
    except ValueError as exc:
        logger.error("Invalid declared project verifier for '%s': %s", project_name, exc)
        return 2, cast(TestSuiteResults, {"exit_code": 2, "original_exit_code": None})
    if declared_command is not None:
        log_substep(
            "Using the project's explicit structured Stage-01 verifier "
            "(the generic pytest profile flags do not rewrite its declared argv).",
            logger,
        )
        try:
            exit_code, declared_results = run_declared_project_verifier(
                repo_root,
                project_root,
                project_name,
                declared_command,
                coverage_floor=project_threshold,
                timeout_seconds=remaining_test_budget(deadline),
            )
            exit_code, guarded_results = enforce_project_suite_guards(
                exit_code,
                cast(dict[str, Any], declared_results),
                project_name=project_name,
                project_root=project_root,
                project_threshold=project_threshold,
                strict=strict,
            )
            duration = time.time() - start_time
            logger.info("Declared project verifier completed in %.1fs", duration)
            if exit_code == 0:
                log_success("Project verifier passed", logger)
            return exit_code, cast(TestSuiteResults, guarded_results)
        except (OSError, ProjectVerifierError, ProjectTestRuntimeError, ValueError) as exc:
            duration = time.time() - start_time
            logger.error(
                "Declared project verifier failed after %.1fs: %s",
                duration,
                exc,
                exc_info=True,
            )
            code = getattr(exc, "exit_code", 1)
            return code, cast(
                TestSuiteResults,
                {
                    "exit_code": code,
                    "original_exit_code": getattr(exc, "original_exit_code", None),
                },
            )

    try:
        _selected, runtime = admit_project_test_runtime(project_root, deadline=deadline)
    except ProjectTestRuntimeError as exc:
        logger.error("Project test runtime unavailable: %s", exc)
        return exc.exit_code, cast(
            TestSuiteResults,
            {
                "exit_code": exc.exit_code,
                "original_exit_code": exc.original_exit_code,
            },
        )

    try:
        cmd = build_project_pytest_command(
            project_root,
            [
                str(project_root / "tests"),
                f"--cov={project_root / 'src'}",
            ],
            interpreter=_selected,
            deadline=deadline,
        )
    except ProjectTestRuntimeError as exc:
        logger.error("Project provider-root discovery refused: %s", exc)
        return exc.exit_code, cast(
            TestSuiteResults, {"exit_code": exc.exit_code, "original_exit_code": exc.original_exit_code}
        )
    project_cov_config = resolve_project_cov_config(project_root)
    if project_cov_config is not None:
        cmd.append(f"--cov-config={project_cov_config}")

    env = os.environ.copy()
    env.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "matplotlib"))
    env["PYTHONPATH"] = build_pythonpath(
        repo_root,
        project_root,
        prepend=[str(project_root)],
        existing_pythonpath=env.get("PYTHONPATH"),
    )
    env.pop("COVERAGE_PROCESS_START", None)

    apply_coverage_datafile(cmd, env, str(project_root / ".coverage.project"))
    cmd.extend(
        [
            "--cov-report=term-missing",
            f"--cov-report=html:{project_root / 'htmlcov'}",
            f"--cov-report=json:{project_root / 'coverage_project.json'}",
            f"--cov-fail-under={project_threshold}",
            "--tb=short",
        ]
    )
    # Opt-in live LLM tests (``@pytest.mark.requires_ollama``) are excluded from
    # the default project gate, matching both the infrastructure runner and the
    # multi-project CI path (``--all-projects --public-projects``). They require a
    # live Ollama daemon plus the ``llm`` dependency group and are run separately
    # with ``--include-ollama-tests`` / ``pytest -m requires_ollama``.
    selection = resolve_test_profile(
        profile,
        include_slow=include_slow,
        include_long_running=include_long_running,
        include_ollama_tests=include_ollama_tests,
        include_bench=include_bench,
    )
    project_marker = build_profile_marker_expression(selection)
    if project_marker:
        cmd.extend(["-m", project_marker])
    cmd.extend(resolve_xdist_args(parallel))
    if quiet:
        cmd.extend(["-q"])
    prepend_uv_to_path(env)

    # Both the runtime and all invocation options have been admitted. A missing
    # interpreter or invalid verifier declaration must retain prior evidence.
    clean_coverage_files(repo_root, scope_dir=project_root)

    # Large private projects can legitimately expose tens of thousands of
    # parametrized tests. Use the full-suite discovery budget here; the former
    # 30-second default produced a misleading warning even when collection
    # completed successfully moments later.
    if discovery_preflight_enabled(env=env):
        log_discovered_tests(
            cmd,
            repo_root,
            env,
            f"project '{project_name}'",
            timeout_seconds=parse_test_discovery_timeout("full"),
        )

    test_results: dict[str, Any] = {}
    try:
        config = _build_generic_project_suite_config(
            project_name=project_name,
            project_root=project_root,
            repo_root=repo_root,
            cmd=cmd,
            env=env,
            coverage_threshold=project_threshold,
            quiet=quiet,
        )
        capacity = remaining_test_budget(deadline)
        config.timeout_seconds = capacity
        config.total_timeout_seconds = capacity
        exit_code, test_results = run_test_suite(config)
        test_results.setdefault("original_exit_code", exit_code)
        exit_code = _test_child_exit_code(exit_code, test_results)
        if strict and test_results.get("failed", 0) > 0 and exit_code not in (2, 75, 124, 130):
            exit_code = 1
        exit_code, test_results = enforce_project_suite_guards(
            exit_code,
            test_results,
            project_name=project_name,
            project_root=project_root,
            project_threshold=project_threshold,
            strict=strict,
        )
        try:
            unchanged_runtime = analysis_runtime_binding(project_root, interpreter=_selected) == runtime["binding"]
        except (OSError, ValueError) as exc:
            logger.error("Selected prepared test runtime custody refused after child: %s", exc)
            unchanged_runtime = False
        if not unchanged_runtime and exit_code == 0:
            exit_code = 75
        if exit_code == 0:
            remaining_test_budget(deadline)
        test_results["selected_runtime"] = runtime
        test_results["exit_code"] = exit_code
        duration = time.time() - start_time
        logger.info("Project test suite completed in %.1fs", duration)
        if exit_code == 0:
            log_success("Project tests passed", logger)
        return exit_code, cast(TestSuiteResults, test_results)
    except (OSError, RuntimeError, ValueError) as exc:
        duration = time.time() - start_time
        logger.error("Failed to run project tests after %.1fs: %s", duration, exc, exc_info=True)
        code = getattr(exc, "exit_code", 1)
        test_results.setdefault("original_exit_code", getattr(exc, "original_exit_code", None))
        test_results.setdefault("diagnostic", str(exc))
        test_results["exit_code"] = code
        return code, cast(TestSuiteResults, test_results)


def execute_test_pipeline(
    project_name: str,
    repo_root: Path,
    run_infra: bool,
    run_project: bool,
    quiet: bool,
    include_slow: bool,
    include_long_running: bool,
    include_ollama_tests: bool,
    strict: bool,
    infra_scope: InfrastructureTestScope = "full",
    parallel: str | int | None = None,
    *,
    profile: TestProfileName = DEFAULT_TEST_PROFILE,
    include_bench: bool = False,
) -> int:
    """Run full test orchestration.

    *parallel* opts both the infrastructure and project suites into
    pytest-xdist (``"auto"`` or an integer worker count); ``None`` falls back
    to ``PYTEST_XDIST_WORKERS`` then serial.
    """
    infra_exit = 0
    infra_results = cast(TestSuiteResults, {})
    project_exit = 0
    project_results = cast(TestSuiteResults, {})
    total_phases = int(run_infra) + int(run_project)

    if run_infra:
        phase_title = "Infrastructure Tests" if run_project else "Infrastructure Tests (Only)"
        log_header(f"Phase 1/{total_phases}: {phase_title}", logger)
        infra_exit, infra_results = run_infrastructure_tests(
            repo_root,
            project_name,
            quiet,
            profile=profile,
            include_slow=include_slow,
            include_long_running=include_long_running,
            include_ollama_tests=include_ollama_tests,
            include_bench=include_bench,
            strict=strict,
            scope=infra_scope,
            parallel=parallel,
        )

    project_blocked = run_project and run_infra and infra_exit != 0
    if project_blocked:
        logger.error("Project tests blocked by unsuccessful shared infrastructure verification")
        project_exit = 75
        project_results = cast(
            TestSuiteResults,
            {"exit_code": 75, "original_exit_code": None, "diagnostic": "Shared infrastructure verification failed"},
        )

    if run_project and not project_blocked:
        phase_num = 2 if run_infra else 1
        phase_title = f"Project Tests ({project_name})" if run_infra else f"Project Tests ({project_name}) (Only)"
        log_header(f"Phase {phase_num}/{total_phases}: {phase_title}", logger)
        project_exit, project_results = run_project_tests(
            repo_root,
            project_name,
            quiet,
            profile=profile,
            include_slow=include_slow,
            include_long_running=include_long_running,
            include_bench=include_bench,
            strict=strict,
            include_ollama_tests=include_ollama_tests,
            parallel=parallel,
        )

    selected_suites = tuple(
        (key, code, results)
        for selected, key, code, results in (
            (run_infra, "infra_tests", infra_exit, infra_results),
            (run_project, "project_tests", project_exit, project_results),
        )
        if selected
    )
    # Exit 2 belongs to admission before any suite execution. Once a child has
    # run, the common executed-run precedence describes aggregate completion.
    if any(code == 2 and results.get("original_exit_code") is None for _, code, results in selected_suites) and not any(
        results.get("original_exit_code") is not None for _, _, results in selected_suites
    ):
        return 2

    if run_project:
        report = generate_test_report(
            infra_results,
            project_results,
            repo_root,
            include_coverage_details=not project_blocked,
            include_infrastructure_coverage=run_infra,
            project_root=resolve_project_root(repo_root, project_name),
        )
        output_dir = resolve_project_root(repo_root, project_name) / "output" / "reports"
        save_test_report_to_files(report, output_dir)
        report_results(infra_exit, project_exit, infra_results, project_results, report, project_name)
    elif run_infra:
        report_infra_only_results(infra_exit, infra_results)

    if not selected_suites:
        return 0
    outcomes = tuple(_test_suite_outcome(key, code, results) for key, code, results in selected_suites)
    return RunResult(tuple(key for key, _, _ in selected_suites), outcomes).exit_code


def _test_suite_outcome(key: str, code: int, results: TestSuiteResults) -> StageOutcome:
    """Retain actual child evidence under the shared executed-run exit policy."""
    states = {
        0: StageStatus.SUCCEEDED,
        75: StageStatus.BLOCKED,
        124: StageStatus.TIMED_OUT,
        130: StageStatus.INTERRUPTED,
    }
    original = results.get("original_exit_code")
    return StageOutcome(
        key, states.get(code, StageStatus.FAILED), child_exit_code=original, diagnostic=results.get("diagnostic", "")
    )


def _test_child_exit_code(code: int, results: Mapping[str, Any]) -> int:
    """Configured failure tolerance cannot authorize a successful test stage."""
    original = cast(int | None, results.get("original_exit_code"))
    if original is not None and original != 0:
        return original if original in (75, 124, 130) else 1
    return code if code in (0, 75, 124, 130) else 1
