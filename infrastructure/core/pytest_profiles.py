"""Reusable test-profile and worker-policy contracts.

The public orchestration module keeps the command-building surface stable,
while this module owns the policy values and validation rules shared by the
infrastructure runner and the isolated public-project matrix.
"""

from __future__ import annotations

import os
import platform
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from typing import Literal, Mapping

from infrastructure.core.logging.utils import get_logger
from infrastructure.core.pytest_marker_exprs import build_pytest_marker_expression
from infrastructure.core.worker_policy import (
    DEFAULT_PROJECT_MATRIX_MAX_WORKERS,
    ENV_PROJECT_MATRIX_WORKERS,
    ENV_XDIST_WORKERS,
    resolve_bounded_workers,
)

logger = get_logger(__name__)

InfrastructureTestScope = Literal["full", "pipeline-smoke"]
TestProfileName = Literal["quick", "release", "exhaustive"]
XdistWorkers = Literal["auto"] | int

TEST_PROFILE_NAMES: tuple[TestProfileName, ...] = ("quick", "release", "exhaustive")
DEFAULT_TEST_PROFILE: TestProfileName = "quick"
TEST_RUNNER_BASE_DEPS: tuple[str, ...] = (
    "pytest",
    "pytest-cov",
    "pytest-timeout",
    "pytest-xdist",
    "pytest-benchmark",
)
MACOS_COVERAGE_XDIST_MAX_WORKERS = 2
XDIST_DISTRIBUTION = "loadscope"
_XDIST_SERIAL_TOKENS: frozenset[str] = frozenset({"", "0", "1", "none", "serial", "off"})


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
    """Return pinned runner dependencies for isolated project subprocesses."""
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


def resolve_project_matrix_workers(*, env: Mapping[str, str] | None = None) -> int:
    """Resolve the bounded adaptive worker count for public project matrices."""
    return resolve_bounded_workers(
        env_name=ENV_PROJECT_MATRIX_WORKERS,
        env=env,
        default_cap=DEFAULT_PROJECT_MATRIX_MAX_WORKERS,
        cpu_reserve=1,
    )


def parse_project_workers(
    project_workers: str | int | None = None,
    *,
    env: Mapping[str, str] | None = None,
) -> int:
    """Return the bounded outer project-matrix worker count."""
    if project_workers is None:
        return 1
    if isinstance(project_workers, bool):
        raise ValueError("Invalid --project-workers value: use 'auto', 'serial', or a positive integer")
    if isinstance(project_workers, int):
        if project_workers < 1:
            raise ValueError(
                f"Invalid --project-workers value {project_workers!r}: use 'auto', 'serial', or a positive integer"
            )
        return project_workers

    value = str(project_workers).strip().lower()
    if value == "auto":
        return resolve_project_matrix_workers(env=env)
    if value == "serial":
        return 1
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(
            f"Invalid --project-workers value {project_workers!r}: use 'auto', 'serial', or a positive integer"
        ) from exc
    if parsed < 1:
        raise ValueError(
            f"Invalid --project-workers value {project_workers!r}: use 'auto', 'serial', or a positive integer"
        )
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


def validate_coverage_parallel(
    parallel: str | int | None = None,
    *,
    env: Mapping[str, str] | None = None,
    platform_name: str | None = None,
) -> None:
    """Reject known-unsafe high-worker coverage runs on macOS."""
    if (platform_name or platform.system()) != "Darwin":
        return
    config = resolve_xdist_worker_config(parallel, env=env, strict=True)
    if config is None:
        return
    if config.workers == "auto" or config.workers > MACOS_COVERAGE_XDIST_MAX_WORKERS:
        raise ValueError(
            "coverage-bearing pytest-xdist on macOS is limited to "
            f"{MACOS_COVERAGE_XDIST_MAX_WORKERS} workers for scheduler stability; "
            "use --parallel 2 or serial for the full coverage lane"
        )


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
    """Return safe pytest-xdist argv for requested parallelism, or ``[]``."""
    config = resolve_xdist_worker_config(parallel, env=env, strict=strict)
    if config is None:
        return []
    return ["-n", str(config.workers), "--dist", XDIST_DISTRIBUTION, "--benchmark-disable"]


__all__ = [
    "DEFAULT_PROJECT_MATRIX_MAX_WORKERS",
    "DEFAULT_TEST_PROFILE",
    "ENV_PROJECT_MATRIX_WORKERS",
    "ENV_XDIST_WORKERS",
    "MACOS_COVERAGE_XDIST_MAX_WORKERS",
    "TEST_PROFILE_NAMES",
    "TEST_PROFILE_REGISTRY",
    "TEST_RUNNER_BASE_DEPS",
    "TestProfileName",
    "TestProfileSpec",
    "XDIST_DISTRIBUTION",
    "XdistWorkerConfig",
    "build_profile_marker_expression",
    "parse_project_workers",
    "resolve_project_matrix_workers",
    "resolve_test_profile",
    "resolve_xdist_args",
    "resolve_xdist_worker_config",
    "test_runner_dependency_specs",
    "validate_coverage_parallel",
    "validate_project_matrix_concurrency",
]
