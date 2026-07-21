"""Canonical pytest subprocess orchestration shared by pipeline and CI runners.

``pipeline_test_runner`` (Stage 01) and ``test_runner.run_per_project_pytest``
(multi-project union gate) both delegate marker expressions, discovery logging,
coverage datafile policy, and project-floor resolution to this module.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Literal, Mapping, TypedDict

from infrastructure.core.coverage_policy import check_cov_datafile_support
from infrastructure.core.logging.utils import get_logger, log_substep, log_success
from infrastructure.core.pytest_marker_exprs import build_pytest_marker_expression
from infrastructure.core.project_pyproject import (
    project_declared_coverage_floor,
    project_declares_dev_extra,
    resolve_project_cov_config,
)
from infrastructure.core.runtime.environment import get_python_command, resolve_test_python

logger = get_logger(__name__)

InfrastructureTestScope = Literal["full", "pipeline-smoke"]
TestProfileName = Literal["quick", "release", "exhaustive"]
XdistWorkers = Literal["auto"] | int

INFRASTRUCTURE_TEST_SCOPES: tuple[InfrastructureTestScope, ...] = ("full", "pipeline-smoke")
TEST_PROFILE_NAMES: tuple[TestProfileName, ...] = ("quick", "release", "exhaustive")
DEFAULT_TEST_PROFILE: TestProfileName = "quick"

TEST_RUNNER_BASE_DEPS: tuple[str, ...] = (
    "pytest",
    "pytest-cov",
    "pytest-timeout",
    "pytest-xdist",
    "pytest-benchmark",
)

# Environment variable that opts a local test run into pytest-xdist parallelism
# when no explicit ``parallel`` argument is threaded through. Mirrors the
# opt-in ``MULTI_PROJECT_MAX_WORKERS`` convention used by the cross-project
# parallel runner (``infrastructure.core.pipeline.multi_project_parallel``).
ENV_XDIST_WORKERS: str = "PYTEST_XDIST_WORKERS"
XDIST_DISTRIBUTION: str = "worksteal"

# Values that mean "run serially" regardless of source (arg or env).
_XDIST_SERIAL_TOKENS: frozenset[str] = frozenset({"", "0", "1", "none", "serial", "off"})

PIPELINE_SMOKE_INFRA_TEST_PATHS = (
    Path("tests/infra_tests/git_hook_smoke"),
    Path("tests/infra_tests/core/test_pipeline.py"),
    Path("tests/infra_tests/core/test_pipeline_types.py"),
    Path("tests/infra_tests/core/test_pipeline_control_extensions.py"),
    Path("tests/infra_tests/core/test_pytest_orchestration.py"),
    Path("tests/infra_tests/project/test_domain_profile.py"),
    Path("tests/infra_tests/validation/test_evidence_registry.py"),
    Path("tests/infra_tests/benchmark/test_template_benchmark_harness.py"),
    Path("tests/infra_tests/test_documentation_index_invariants.py"),
)

DISCOVERY_PATTERNS: tuple[str, ...] = (
    r"(\d+)\s+tests?\s+collected",
    r"collected\s+(\d+)\s+items?",
    r"found\s+(\d+)\s+tests?",
    r"(\d+)\s+tests?\s+found",
    r"=+\s+(\d+)\s+tests?\s+collected",
)


@dataclass(frozen=True)
class TestProfileSpec:
    """Typed reusable test-profile semantics shared across runners."""

    name: TestProfileName
    include_slow: bool
    include_long_running: bool
    include_ollama_tests: bool
    include_bench: bool


@dataclass(frozen=True)
class XdistWorkerConfig:
    """Validated per-project pytest-xdist request."""

    workers: XdistWorkers
    source: Literal["argument", "environment"]
    raw_value: str | int


TEST_PROFILE_REGISTRY: dict[TestProfileName, TestProfileSpec] = {
    "quick": TestProfileSpec(
        name="quick",
        include_slow=False,
        include_long_running=False,
        include_ollama_tests=False,
        include_bench=False,
    ),
    "release": TestProfileSpec(
        name="release",
        include_slow=True,
        include_long_running=False,
        include_ollama_tests=False,
        include_bench=False,
    ),
    "exhaustive": TestProfileSpec(
        name="exhaustive",
        include_slow=True,
        include_long_running=True,
        # Live services remain explicit opt-in even for exhaustive runs.
        include_ollama_tests=False,
        include_bench=False,
    ),
}


def test_runner_dependency_specs() -> tuple[str, ...]:
    """Return ``uv --with`` specs for project-level pytest subprocesses.

    Pin the complete runner toolchain to the workspace versions. A project
    subprocess must not silently resolve a newer pytest/plugin combination
    than the orchestrator's tested environment: pytest 9.1's temporary-path
    behavior, for example, can invalidate long-running project fixtures even
    when the same suite passes under the workspace version. The multi-project
    runner also appends every project's traces into one coverage SQLite
    database, so coverage is pinned to the workspace version for a compatible
    data format.
    """
    deps: list[str] = []
    for package in (*TEST_RUNNER_BASE_DEPS, "coverage"):
        try:
            deps.append(f"{package}=={version(package)}")
        except PackageNotFoundError:
            if package == "coverage":
                logger.warning("coverage package not found; project test subprocesses will not pin coverage")
            else:
                deps.append(package)
    return tuple(deps)


class TestSuiteResults(TypedDict, total=False):
    """Structured result dict returned by infrastructure/project test runners."""

    passed: int
    failed: int
    skipped: int
    total: int
    warnings: int
    exit_code: int
    discovery_count: int
    collection_errors: int
    execution_phases: dict[str, float]
    test_categories: dict[str, int]
    coverage_percent: float
    failed_tests: list[dict[str, str]]


def resolve_test_profile(
    profile: TestProfileName = DEFAULT_TEST_PROFILE,
    *,
    include_slow: bool = False,
    include_long_running: bool = False,
    include_ollama_tests: bool = False,
    include_bench: bool = False,
) -> TestProfileSpec:
    """Resolve profile semantics plus additive legacy include-flags."""
    if not isinstance(profile, str) or profile not in TEST_PROFILE_NAMES:
        choices = ", ".join(TEST_PROFILE_NAMES)
        raise ValueError(f"Unknown test profile {profile!r}; choose one of: {choices}")
    base = TEST_PROFILE_REGISTRY[profile]
    return TestProfileSpec(
        name=base.name,
        include_slow=base.include_slow or include_slow,
        include_long_running=base.include_long_running or include_long_running,
        include_ollama_tests=base.include_ollama_tests or include_ollama_tests,
        include_bench=base.include_bench or include_bench,
    )


def build_profile_marker_expression(profile: TestProfileSpec) -> str | None:
    """Build the canonical pytest marker expression for a resolved profile."""
    return build_pytest_marker_expression(
        skip_requires_ollama=not profile.include_ollama_tests,
        skip_slow=not profile.include_slow,
        skip_bench=not profile.include_bench,
        skip_long_running=not profile.include_long_running,
    )


def parse_project_workers(project_workers: str | int | None = None) -> int:
    """Return the bounded outer project-matrix worker count."""
    if project_workers is None:
        return 1
    if isinstance(project_workers, bool):
        raise ValueError("Invalid --project-workers value: use 'serial' or a positive integer")
    if isinstance(project_workers, int):
        if project_workers < 1:
            raise ValueError(f"Invalid --project-workers value {project_workers!r}: use 'serial' or a positive integer")
        return project_workers

    value = str(project_workers).strip().lower()
    if value == "serial":
        return 1
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(
            f"Invalid --project-workers value {project_workers!r}: use 'serial' or a positive integer"
        ) from exc
    if parsed < 1:
        raise ValueError(f"Invalid --project-workers value {project_workers!r}: use 'serial' or a positive integer")
    return parsed


def resolve_xdist_worker_config(
    parallel: str | int | None = None,
    *,
    env: Mapping[str, str] | None = None,
    strict: bool = False,
) -> XdistWorkerConfig | None:
    """Return validated pytest-xdist worker config, or ``None`` for serial."""
    source: Literal["argument", "environment"] = "argument"
    raw: str | int | None = parallel
    if raw is None:
        source = "environment"
        source_env = os.environ if env is None else env
        raw = source_env.get(ENV_XDIST_WORKERS)
    if raw is None:
        return None
    if isinstance(raw, bool):
        message = (
            f"Invalid pytest-xdist worker value {raw!r} from "
            f"{'--parallel' if source == 'argument' else ENV_XDIST_WORKERS}: "
            "use 'auto', 'serial', or a positive integer"
        )
        if strict:
            raise ValueError(message)
        logger.warning("%s; running tests serially", message)
        return None

    value = str(raw).strip().lower()
    if value in _XDIST_SERIAL_TOKENS:
        return None
    if value == "auto":
        return XdistWorkerConfig(workers="auto", source=source, raw_value=raw)

    try:
        workers = int(value)
    except ValueError:
        message = (
            f"Invalid pytest-xdist worker value {raw!r} from "
            f"{'--parallel' if source == 'argument' else ENV_XDIST_WORKERS}: "
            "use 'auto', 'serial', or a positive integer"
        )
        if strict:
            raise ValueError(message)
        logger.warning("%s; running tests serially", message)
        return None
    if workers <= 1:
        return None
    return XdistWorkerConfig(workers=workers, source=source, raw_value=raw)


def validate_project_matrix_concurrency(
    project_workers: str | int | None,
    parallel: str | int | None,
    *,
    env: Mapping[str, str] | None = None,
    strict_parallel: bool = False,
) -> int:
    """Reject nested outer-project concurrency plus inner per-project xdist."""
    outer_workers = parse_project_workers(project_workers)
    xdist_config = resolve_xdist_worker_config(parallel, env=env, strict=strict_parallel)
    if outer_workers > 1 and xdist_config is not None:
        inner_control = "--parallel"
        if xdist_config.source == "environment":
            inner_control = ENV_XDIST_WORKERS
        raise ValueError(
            "Nested test concurrency is not supported: "
            f"--project-workers={outer_workers} cannot be combined with "
            f"{inner_control}={xdist_config.raw_value!r}. "
            "Use either outer project concurrency or per-project pytest-xdist, not both."
        )
    return outer_workers


def resolve_xdist_args(
    parallel: str | int | None = None,
    *,
    env: Mapping[str, str] | None = None,
    strict: bool = False,
) -> list[str]:
    """Return safe pytest-xdist argv for requested parallelism, or ``[]``.

    Parallelism is **opt-in**: the default is serial. This preserves the
    load-contention safety the repo already documents (CLAUDE.md Testing
    section) — real LaTeX/subprocess tests carry wall-clock timeouts that
    ``-n auto`` can trip nondeterministically on a busy dev machine.

    Resolution order:
        1. An explicit *parallel* argument, when not ``None``.
        2. Otherwise the ``PYTEST_XDIST_WORKERS`` environment variable.

    Accepted values (from either source):
        * ``"auto"`` → xdist with one worker per detected core.
        * a positive integer > 1 → xdist with that fixed worker count.
        * ``None``/``""``/``"0"``/``"1"``/``"serial"``/``"off"`` or anything
          unparseable → ``[]`` (serial). A single worker is pure xdist
          overhead, so it collapses to serial rather than spawning one worker.
    """
    config = resolve_xdist_worker_config(parallel, env=env, strict=strict)
    if config is None:
        return []
    return [
        "-n",
        str(config.workers),
        "--dist",
        XDIST_DISTRIBUTION,
        "--benchmark-disable",
    ]


def resolve_infrastructure_test_paths(repo_root: Path, scope: InfrastructureTestScope) -> list[str]:
    """Return pytest path arguments for an infrastructure test scope."""
    if scope == "full":
        return [
            str(repo_root / "tests" / "infra_tests"),
            str(repo_root / "tests" / "integration"),
            "--ignore=" + str(repo_root / "tests" / "integration" / "test_module_interoperability.py"),
        ]
    if scope == "pipeline-smoke":
        # Fail closed: a manifest entry pointing at a moved/renamed path must
        # error here, not silently collect 0 tests and pass a vacuous gate.
        missing = [str(path) for path in PIPELINE_SMOKE_INFRA_TEST_PATHS if not (repo_root / path).exists()]
        if missing:
            raise FileNotFoundError(
                "pipeline-smoke manifest references missing test paths "
                f"(update PIPELINE_SMOKE_INFRA_TEST_PATHS): {missing}"
            )
        return [str(repo_root / relative_path) for relative_path in PIPELINE_SMOKE_INFRA_TEST_PATHS]
    raise ValueError(f"Unknown infrastructure test scope: {scope}")


def parse_test_discovery_timeout(scope: InfrastructureTestScope) -> float:
    """Resolve the collection timeout for pytest discovery logging."""
    raw_timeout = os.environ.get("TEST_DISCOVERY_TIMEOUT_SEC")
    if raw_timeout:
        try:
            timeout = float(raw_timeout)
        except ValueError:
            logger.warning("Ignoring invalid TEST_DISCOVERY_TIMEOUT_SEC=%r", raw_timeout)
        else:
            if timeout > 0:
                return timeout
            logger.warning("Ignoring non-positive TEST_DISCOVERY_TIMEOUT_SEC=%r", raw_timeout)
    return 120.0 if scope == "full" else 30.0


def parse_discovery_count(combined_output: str) -> int | None:
    """Extract a collected-test count from pytest --collect-only output."""
    for pattern in DISCOVERY_PATTERNS:
        match = re.search(pattern, combined_output, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                continue
    return None


def log_discovered_tests(
    cmd: list[str],
    repo_root: Path,
    env: dict[str, str],
    label: str,
    *,
    timeout_seconds: float = 30.0,
) -> None:
    """Run pytest serially with ``--collect-only`` and log its test count.

    Pytest-xdist may schedule collected items even in collection-only mode.
    Discovery is only a pre-flight count, so carrying the execution command's
    ``-n``/``--dist`` options into it can duplicate or even start a large suite
    before the real test run.  A final ``-n 0`` overrides command-line and
    project-level ``addopts`` parallelism; ``--no-cov`` avoids instrumenting a
    throwaway collection pass.
    """
    discovery_cmd = [*cmd, "--collect-only", "-n", "0", "--no-cov"]
    log_substep(f"Discovering {label} tests...", logger)
    try:
        result = subprocess.run(  # nosec B603
            discovery_cmd,
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        combined = result.stdout + "\n" + result.stderr
        test_count = parse_discovery_count(combined)
        if test_count is not None:
            log_success(f"Discovered {test_count} {label} tests", logger)
        else:
            logger.warning("Could not parse test count from %s test discovery", label)
    except (subprocess.TimeoutExpired, subprocess.SubprocessError) as exc:
        logger.warning("Test discovery failed for %s: %s", label, exc)


def build_pythonpath(
    repo_root: Path,
    project_root: Path,
    *,
    prepend: list[str] | None = None,
    existing_pythonpath: str | None = None,
) -> str:
    """Build PYTHONPATH for a pytest subprocess."""
    parts: list[str] = list(prepend or [])
    parts.extend([str(repo_root), str(repo_root / "infrastructure")])
    project_src = project_root / "src"
    if project_src.exists():
        parts.append(str(project_src))
    if existing_pythonpath:
        parts.append(existing_pythonpath)
    return os.pathsep.join(parts)


def prepend_uv_to_path(env: dict[str, str]) -> None:
    """Ensure ``uv`` is on PATH when available."""
    uv_path = shutil.which("uv")
    if uv_path:
        env["PATH"] = f"{os.path.dirname(uv_path)}:{env.get('PATH', '')}"


def apply_coverage_datafile(
    cmd: list[str],
    env: dict[str, str],
    datafile_name: str,
    *,
    supported: bool | None = None,
) -> None:
    """Pin coverage output to ``datafile_name`` via CLI flag or COVERAGE_FILE."""
    if supported is None:
        supported = check_cov_datafile_support()
    if supported:
        cmd.append(f"--cov-datafile={datafile_name}")
    else:
        env["COVERAGE_FILE"] = datafile_name


def resolve_coverage_file(coverage_file: str) -> str:
    """Return COVERAGE_FILE value, honouring the environment when set."""
    env_value = os.environ.get("COVERAGE_FILE")
    if env_value:
        return env_value
    return coverage_file


def make_coverage_subprocess_env(coverage_file_value: str, repo_root: Path) -> dict[str, str]:
    """Build subprocess env with COVERAGE_FILE pinned and repo root on PYTHONPATH."""
    env = os.environ.copy()
    env["COVERAGE_FILE"] = coverage_file_value
    existing_pp = env.get("PYTHONPATH", "")
    pp_parts = [str(repo_root)]
    if existing_pp:
        pp_parts.append(existing_pp)
    env["PYTHONPATH"] = os.pathsep.join(pp_parts)
    return env


def resolve_project_test_python(project_root: Path, cmd: list[str]) -> list[str]:
    """Use project venv python when it can import pytest; otherwise workspace interpreter."""
    try:
        probe = subprocess.run(  # nosec B603
            [*cmd, "-c", "import pytest"],
            capture_output=True,
            check=False,
            timeout=30,
        )
        if probe.returncode == 0:
            return cmd
        logger.warning(
            "Resolved interpreter %s cannot import pytest (project venv "
            "%s/.venv is missing test deps — run `uv sync`). Falling back "
            "to the workspace interpreter %s so the project suite actually runs.",
            cmd,
            project_root,
            get_python_command(),
        )
    except (OSError, subprocess.SubprocessError) as probe_err:
        logger.warning("pytest-availability probe failed (%s); using %s", probe_err, get_python_command())
    return get_python_command()


def normalize_pytest_args_for_project(project_root: Path, pytest_args: list[str]) -> list[str]:
    """Rewrite absolute paths under *project_root* to project-relative form for ``uv run --directory``."""
    root = project_root.resolve()
    normalized: list[str] = []
    for arg in pytest_args:
        if not arg.startswith("-"):
            candidate = Path(arg)
            if candidate.is_absolute():
                try:
                    normalized.append(str(candidate.resolve().relative_to(root)))
                    continue
                except ValueError:
                    pass
        normalized.append(arg)
    return normalized


def build_project_pytest_command(
    project_root: Path,
    pytest_args: list[str],
    *,
    inject_runner_dependencies: bool = True,
) -> list[str]:
    """Return argv for a project pytest suite using project-local deps when declared.

    Projects with ``pyproject.toml`` run via ``uv run --directory`` so pinned
    dependencies (for example ``scikit-learn``) resolve from the project tree
    instead of the workspace interpreter.

    Test-runner packages (pytest plus coverage, timeout, xdist, and benchmark
    plugins) are
    By default, test-runner packages are injected via ``--with`` so they are
    always available in the project's ephemeral env even when the project's own
    ``pyproject.toml`` does not declare them. Collection-only callers that use a
    declared project test environment may set ``inject_runner_dependencies`` to
    ``False`` to avoid resolving a redundant overlay; interpreter resolution and
    the relocation-safe ``python -m pytest`` invocation remain shared.
    """
    pyproject = project_root / "pyproject.toml"
    uv_path = shutil.which("uv")
    if pyproject.is_file() and uv_path:
        resolved_root = project_root.resolve()
        cmd: list[str] = [uv_path, "run", "--directory", str(resolved_root)]
        # Inject test-runner deps so they are always available regardless of
        # what the project itself declares (thin projects declare only runtime
        # deps; pytest/cov/timeout stay in the workspace dev group).
        if inject_runner_dependencies:
            for dependency_spec in test_runner_dependency_specs():
                cmd.extend(["--with", dependency_spec])
        if project_declares_dev_extra(resolved_root):
            cmd.extend(["--extra", "dev"])
        cmd.extend(
            [
                "python",
                "-m",
                "pytest",
                *normalize_pytest_args_for_project(resolved_root, pytest_args),
            ]
        )
        return cmd
    interpreter = resolve_project_test_python(project_root, resolve_test_python(project_root / ".venv"))
    return interpreter + ["-m", "pytest", *pytest_args]


def build_union_pytest_command(
    repo_root: Path,
    project_root: Path,
    tests_dir: Path,
    *,
    is_first: bool,
    marker_expr: str | None,
    timeout: int,
    parallel: str | int | None = None,
    fail_under: int | None = None,
) -> list[str]:
    """Build argv for one project in a multi-project combined-coverage run.

    When *parallel* (or the ``PYTEST_XDIST_WORKERS`` env var) requests it, the
    per-project pytest invocation is parallelized with pytest-xdist. pytest-cov
    combines per-worker coverage data before that project's isolated datafile
    is written. The runner combines those files only after all project floors
    have been evaluated.
    """
    resolved_root = project_root.resolve()
    src_dir = resolved_root / "src"
    # Use the ABSOLUTE resolved path so that --cov resolves correctly even
    # when pytest runs under ``uv run --directory <project>`` which sets the
    # subprocess CWD to the project directory — making a repo-relative path
    # (e.g. ``projects/templates/.../src``) resolve to the wrong location and
    # collect 0% coverage.
    if src_dir.is_dir():
        cov_target = str(src_dir)
    else:
        cov_target = str(resolved_root)

    pytest_args: list[str] = [
        str(tests_dir),
        f"--cov={cov_target}",
        "--cov-branch",
        "--cov-report=term-missing",
        f"--timeout={timeout}",
        "--durations=10",
    ]
    if marker_expr:
        pytest_args.extend(["-m", marker_expr])
    if fail_under is not None:
        pytest_args.append(f"--cov-fail-under={fail_under}")
    if not is_first:
        pytest_args.append("--cov-append")
    pytest_args.extend(resolve_xdist_args(parallel))
    return build_project_pytest_command(resolved_root, pytest_args)


def project_has_test_files(project_root: Path) -> bool:
    """Return True when ``tests/`` contains discoverable test modules."""
    tests_dir = project_root / "tests"
    if not tests_dir.is_dir():
        return False
    return any(tests_dir.rglob("test_*.py")) or any(tests_dir.rglob("*_test.py"))


def enforce_project_suite_guards(
    exit_code: int,
    test_results: dict[str, Any],
    *,
    project_name: str,
    project_root: Path,
    project_threshold: float,
    strict: bool,
) -> tuple[int, dict[str, Any]]:
    """Apply zero-collected guard for project runs.

    Coverage thresholds are enforced by pytest ``--cov-fail-under`` on the
    command line; this guard only catches silent zero-collection failures.
    """
    del project_threshold  # retained for call-site stability; pytest owns coverage gates
    ran_count = test_results.get("total", 0) or test_results.get("passed", 0)
    if strict and project_has_test_files(project_root) and ran_count == 0:
        tests_dir = project_root / "tests"
        logger.error(
            "Project '%s' has test files under %s but the run collected/ran "
            "0 tests — refusing to score this as PASSED. The project "
            "interpreter is likely missing pytest/pytest-cov (run `uv sync`).",
            project_name,
            tests_dir,
        )
        exit_code = 1
        test_results["exit_code"] = 1

    return exit_code, test_results


__all__ = [
    "DEFAULT_TEST_PROFILE",
    "DISCOVERY_PATTERNS",
    "ENV_XDIST_WORKERS",
    "INFRASTRUCTURE_TEST_SCOPES",
    "InfrastructureTestScope",
    "PIPELINE_SMOKE_INFRA_TEST_PATHS",
    "TEST_PROFILE_NAMES",
    "TEST_PROFILE_REGISTRY",
    "TestProfileName",
    "TestProfileSpec",
    "TestSuiteResults",
    "XDIST_DISTRIBUTION",
    "XdistWorkerConfig",
    "build_profile_marker_expression",
    "build_project_pytest_command",
    "build_union_pytest_command",
    "build_pythonpath",
    "enforce_project_suite_guards",
    "log_discovered_tests",
    "make_coverage_subprocess_env",
    "parse_discovery_count",
    "parse_project_workers",
    "parse_test_discovery_timeout",
    "prepend_uv_to_path",
    "project_declared_coverage_floor",
    "project_has_test_files",
    "resolve_coverage_file",
    "resolve_test_profile",
    "resolve_project_cov_config",
    "resolve_infrastructure_test_paths",
    "resolve_project_test_python",
    "resolve_xdist_args",
    "resolve_xdist_worker_config",
    "test_runner_dependency_specs",
    "validate_project_matrix_concurrency",
]
