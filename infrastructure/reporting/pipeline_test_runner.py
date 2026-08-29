"""Test orchestration module.

Thin facade over :mod:`infrastructure.core.pytest_orchestration` and
:mod:`infrastructure.reporting.suite_runner` for Stage 01 test execution.
"""

from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path
from typing import Any, cast

from infrastructure.core.config.queries import get_testing_config
from infrastructure.core.files.coverage_cleanup import clean_coverage_files
from infrastructure.core.files.project_lock import project_output_lock
from infrastructure.core.logging.utils import get_logger, log_header, log_substep, log_success
from infrastructure.core.pytest_orchestration import (
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
from infrastructure.core.runtime.environment import resolve_test_python
from infrastructure.project.discovery import resolve_project_root
from infrastructure.reporting.coverage_reporter import generate_test_report, save_test_report_to_files
from infrastructure.reporting.pipeline_test_reporting import (
    report_infra_only_results,
    report_results,
)
from infrastructure.reporting.project_verifier import ProjectVerifierError, run_declared_project_verifier
from infrastructure.reporting.suite_runner import (
    DEFAULT_SINGLE_PROJECT_TEST_TIMEOUT_SECONDS,
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
        repo_root=repo_root,
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

    # Infrastructure coverage belongs to the repository root. Do not recurse
    # into lifecycle sidecars or active private projects that may be running
    # their own isolated test producer in the same checkout.
    clean_coverage_files(repo_root, recursive=False)

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
    cmd = resolve_test_python(repo_root / ".venv")
    cmd += ["-m", "pytest"]
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

    if discovery_preflight_enabled(env=env):
        log_discovered_tests(
            cmd,
            repo_root,
            env,
            f"infrastructure ({scope})",
            timeout_seconds=parse_test_discovery_timeout(scope),
        )

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
        exit_code, test_results = run_test_suite(config)
        if strict and test_results.get("failed", 0) > 0:
            exit_code = 1
        duration = time.time() - start_time
        logger.info("Infrastructure test suite completed in %.1fs", duration)
        if exit_code == 0:
            log_success("Infrastructure tests passed", logger)
        return exit_code, cast(TestSuiteResults, test_results)
    except (OSError, RuntimeError, ValueError) as exc:
        duration = time.time() - start_time
        logger.error("Failed to run infrastructure tests after %.1fs: %s", duration, exc, exc_info=True)
        return 1, cast(TestSuiteResults, {})


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
    project_root = resolve_project_root(repo_root, project_name)

    clean_coverage_files(repo_root, scope_dir=project_root)

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
        return 1, cast(TestSuiteResults, {})
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
        except (OSError, ProjectVerifierError, ValueError) as exc:
            duration = time.time() - start_time
            logger.error(
                "Declared project verifier failed after %.1fs: %s",
                duration,
                exc,
                exc_info=True,
            )
            return 1, cast(TestSuiteResults, {})

    cmd = build_project_pytest_command(
        project_root,
        [
            str(project_root / "tests"),
            f"--cov={project_root / 'src'}",
        ],
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
        exit_code, test_results = run_test_suite(config)
        if strict and test_results.get("failed", 0) > 0:
            exit_code = 1
        exit_code, test_results = enforce_project_suite_guards(
            exit_code,
            test_results,
            project_name=project_name,
            project_root=project_root,
            project_threshold=project_threshold,
            strict=strict,
        )
        duration = time.time() - start_time
        logger.info("Project test suite completed in %.1fs", duration)
        if exit_code == 0:
            log_success("Project tests passed", logger)
        return exit_code, cast(TestSuiteResults, test_results)
    except (OSError, RuntimeError, ValueError) as exc:
        duration = time.time() - start_time
        logger.error("Failed to run project tests after %.1fs: %s", duration, exc, exc_info=True)
        return 1, cast(TestSuiteResults, {})


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

    if run_project:
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

    if run_project:
        report = generate_test_report(
            infra_results,
            project_results,
            repo_root,
            include_coverage_details=True,
            include_infrastructure_coverage=run_infra,
            project_root=resolve_project_root(repo_root, project_name),
        )
        output_dir = resolve_project_root(repo_root, project_name) / "output" / "reports"
        save_test_report_to_files(report, output_dir)
        report_results(infra_exit, project_exit, infra_results, project_results, report, project_name)
    elif run_infra:
        report_infra_only_results(infra_exit, infra_results)

    if run_project and run_infra:
        return 1 if (infra_exit != 0 or project_exit != 0) else 0
    if run_project:
        return project_exit
    if run_infra:
        return infra_exit
    return 0
