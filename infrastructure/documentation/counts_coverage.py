"""Coverage snapshot measurement and source-tree provenance.

The factsheet renderer imports this module's stable public names so collection
documentation and coverage evidence can evolve independently. Coverage is
always measured in the exemplar's isolated environment; source hashes include
tracked and non-ignored project inputs while excluding generated output and
runtime, build, cache, and environment artifacts.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

from infrastructure.core.execution_boundary import BoundedSubprocessResult
from infrastructure.core.pytest_orchestration import (
    build_profile_marker_expression,
    resolve_test_profile,
)
from infrastructure.core.runtime.environment import get_subprocess_env
from infrastructure.core.subprocess_policy import SubprocessPolicy, run_with_policy
from infrastructure.documentation._coverage_workspace import (
    COVERAGE_SUPPORT_IDENTITY_MODE as COVERAGE_SUPPORT_IDENTITY_MODE,
    _COVERAGE_COPY_EXCLUDED_NAMES as _COVERAGE_COPY_EXCLUDED_NAMES,
    _COVERAGE_COPY_SUPPORT_SPECS as _COVERAGE_COPY_SUPPORT_SPECS,
    _COVERAGE_GIT_ENVIRONMENT_PREFIXES as _COVERAGE_GIT_ENVIRONMENT_PREFIXES,
    _COVERAGE_GIT_ENVIRONMENT_VARIABLES as _COVERAGE_GIT_ENVIRONMENT_VARIABLES,
    _CoverageSupportSpec as _CoverageSupportSpec,
    _confined_disposable_git_path as _confined_disposable_git_path,
    _copy_coverage_support_closure as _copy_coverage_support_closure,
    _coverage_copy_ignore as _coverage_copy_ignore,
    _coverage_git_environment as _coverage_git_environment,
    _coverage_measurement_data_file as _coverage_measurement_data_file,
    _coverage_measurement_workspace_with_policy_factory,
    _coverage_support_identity as _coverage_support_identity,
    _ensure_disposable_support_directory as _ensure_disposable_support_directory,
    _is_coverage_copy_excluded as _is_coverage_copy_excluded,
    _provision_coverage_copy_git_context_with_policy_factory,
    _reject_coverage_copy_symlinks as _reject_coverage_copy_symlinks,
    _run_coverage_git_with_policy_factory,
    _validated_coverage_support_path as _validated_coverage_support_path,
    _validated_public_exemplar_path as _validated_public_exemplar_path,
)

COVERAGE_PROVENANCE_RELATIVE_PATH = Path("docs/_generated/coverage_snapshot.json")
COVERAGE_PROVENANCE_SCHEMA_VERSION = 5
COVERAGE_SOURCE_INVENTORY_MODE = "tracked-and-nonignored-coverage-inputs-v3"
EXEMPLAR_SNAPSHOT_DATE = "2026-08-16"
COVERAGE_MEASUREMENT_TIMEOUT_SECONDS = 1800
_ACTIVE_COVERAGE_PROJECT = "template_active_inference"


@dataclass(frozen=True)
class CoverageMeasurementPolicyOverride:
    """One explicit public-exemplar exception to the bounded default."""

    policy_id: str
    timeout_seconds: int
    strategy_id: str
    uv_run_args: tuple[str, ...]


COVERAGE_MEASUREMENT_POLICY_OVERRIDES: Mapping[str, CoverageMeasurementPolicyOverride] = MappingProxyType(
    {
        "template_active_inference": CoverageMeasurementPolicyOverride(
            policy_id="coverage-measurement-active-inference",
            timeout_seconds=6900,
            strategy_id="state-isolated-chunked-coverage",
            uv_run_args=(
                "--extra",
                "dev",
                "python",
                "scripts/run_full_verification.py",
                "--coverage-only",
                "--profile",
                "release",
            ),
        ),
    }
)


def _coverage_process_policy(policy_id: str, timeout_seconds: float) -> SubprocessPolicy:
    """Return the shared bounded policy for one coverage subprocess."""
    return SubprocessPolicy(
        policy_id=policy_id,
        source_path="infrastructure/documentation/counts_coverage.py",
        timeout_seconds=timeout_seconds,
        capture_output=True,
        credential_free=True,
    )


def _coverage_measurement_process_policy(name: str) -> SubprocessPolicy:
    """Return the named exemplar's bounded coverage-measurement policy."""
    override = COVERAGE_MEASUREMENT_POLICY_OVERRIDES.get(name)
    if override is None:
        return _coverage_process_policy("coverage-measurement", COVERAGE_MEASUREMENT_TIMEOUT_SECONDS)
    return _coverage_process_policy(override.policy_id, override.timeout_seconds)


_COVERAGE_INPUT_EXCLUDED_PARTS = frozenset(
    {
        ".benchmarks",
        ".cache",
        ".direnv",
        ".env",
        ".git",
        ".hypothesis",
        ".ipynb_checkpoints",
        ".lake",
        ".pytest_cache",
        ".mypy_cache",
        ".next",
        ".nox",
        ".pipeline",
        ".pnpm-store",
        ".ruff_cache",
        ".coverage",
        ".tox",
        ".venv",
        "__pycache__",
        "_build",
        "build",
        "dist",
        "env",
        "env.bak",
        "ENV",
        "htmlcov",
        "node_modules",
        "output",
        "rendered",
        "venv",
        "venv.bak",
    }
)
_COVERAGE_INPUT_EXCLUDED_SUFFIXES = (".egg-info",)
_COVERAGE_INPUT_EXCLUDED_FILE_SUFFIXES = frozenset({".pyc", ".pyo"})


@dataclass(frozen=True)
class ExemplarSnapshot:
    """One measured coverage row; collection count is always derived live."""

    name: str
    coverage_pct: str


EXEMPLAR_SNAPSHOT: tuple[ExemplarSnapshot, ...] = (
    ExemplarSnapshot("template_active_inference", "91.89 %"),
    ExemplarSnapshot("template_advanced_literature_review", "91.96 %"),
    ExemplarSnapshot("template_autopoiesis", "97.03 %"),
    ExemplarSnapshot("template_autoresearch_project", "96.33 %"),
    ExemplarSnapshot("template_autoscientists", "97.16 %"),
    ExemplarSnapshot("template_code_project", "95.85 %"),
    ExemplarSnapshot("template_data_descriptor", "96.13 %"),
    ExemplarSnapshot("template_eda_notebook", "90.03 %"),
    ExemplarSnapshot("template_formal", "94.50 %"),
    ExemplarSnapshot("template_gold_refinement", "92.19 %"),
    ExemplarSnapshot("template_literature_meta_analysis", "95.92 %"),
    ExemplarSnapshot("template_madlib", "99.11 %"),
    ExemplarSnapshot("template_methods_paper", "99.00 %"),
    ExemplarSnapshot("template_newspaper", "99.25 %"),
    ExemplarSnapshot("template_pitch_deck", "97.27 %"),
    ExemplarSnapshot("template_pools_rules_tools", "94.72 %"),
    ExemplarSnapshot("template_prose_project", "95.87 %"),
    ExemplarSnapshot("template_redacted_report", "97.03 %"),
    ExemplarSnapshot("template_registered_report", "94.35 %"),
    ExemplarSnapshot("template_search_project", "96.28 %"),
    ExemplarSnapshot("template_sia", "94.39 %"),
    ExemplarSnapshot("template_storybook", "93.91 %"),
    ExemplarSnapshot("template_template", "97.53 %"),
    ExemplarSnapshot("template_textbook", "96.08 %"),
)


def _coverage_measurement_command(
    project_dir: Path,
    *,
    environment_project_dir: Path | None = None,
) -> list[str]:
    """Build the bounded release-profile pytest command for one exemplar."""
    environment_project = project_dir if environment_project_dir is None else environment_project_dir
    override = COVERAGE_MEASUREMENT_POLICY_OVERRIDES.get(environment_project.name)
    if override is not None:
        command = ["uv", "run", "--locked"]
        if environment_project != project_dir:
            command.extend(["--project", str(environment_project)])
        command.extend(["--directory", str(project_dir), *override.uv_run_args])
        return command

    profile = resolve_test_profile("release")
    marker_expression = build_profile_marker_expression(profile)
    command = [
        "uv",
        "run",
        "--directory",
        str(project_dir),
        "pytest",
        "tests/",
        "--cov=src",
        "--cov-report=",
        "-q",
    ]
    if marker_expression:
        command.extend(["-m", marker_expression])
    return command


def _coverage_report_command(
    project_dir: Path,
    *,
    environment_project_dir: Path | None = None,
) -> list[str]:
    """Build the coverage-report command for one measurement workspace."""
    environment_project = project_dir if environment_project_dir is None else environment_project_dir
    if environment_project.name in COVERAGE_MEASUREMENT_POLICY_OVERRIDES:
        return [
            "uv",
            "run",
            "--locked",
            "--project",
            str(environment_project),
            "--directory",
            str(project_dir),
            "--extra",
            "dev",
            "coverage",
            "report",
            "--precision=2",
        ]
    return [
        "uv",
        "run",
        "--directory",
        str(project_dir),
        "coverage",
        "report",
        "--precision=2",
    ]


def _coverage_measurement_strategy(name: str) -> str:
    """Return the diagnostic identifier for one exemplar's coverage route."""
    override = COVERAGE_MEASUREMENT_POLICY_OVERRIDES.get(name)
    return override.strategy_id if override is not None else "single-process-pytest"


def _run_coverage_git(argv: list[str], *, cwd: Path, action: str) -> str:
    """Run one bounded Git context command through the source-owned policy."""
    return _run_coverage_git_with_policy_factory(
        argv,
        cwd=cwd,
        action=action,
        process_policy_factory=_coverage_process_policy,
    )


def _provision_coverage_copy_git_context(
    repo_root: Path,
    environment_project: Path,
    measurement_repository: Path,
    measurement_project: Path,
) -> None:
    """Provision Git context through the source-owned subprocess policy."""
    _provision_coverage_copy_git_context_with_policy_factory(
        repo_root,
        environment_project,
        measurement_repository,
        measurement_project,
        process_policy_factory=_coverage_process_policy,
    )


@contextmanager
def _coverage_measurement_workspace(
    repo_root: Path,
    name: str,
) -> Iterator[tuple[Path, Path]]:
    """Yield the projects selected by the source-owned coverage policy."""
    with _coverage_measurement_workspace_with_policy_factory(
        repo_root,
        name,
        disposable=name in COVERAGE_MEASUREMENT_POLICY_OVERRIDES,
        process_policy_factory=_coverage_process_policy,
    ) as workspace:
        yield workspace


def _coverage_total_from_report(report_output: str, name: str) -> str:
    """Parse and validate the bounded coverage report's TOTAL percentage."""
    total_lines = [line for line in report_output.splitlines() if line.startswith("TOTAL")]
    if len(total_lines) != 1:
        raise RuntimeError(f"invalid or missing TOTAL coverage percentage for {name}")
    raw_percent = total_lines[0].split()[-1]
    if not raw_percent.endswith("%"):
        raise RuntimeError(f"invalid or missing TOTAL coverage percentage for {name}")
    try:
        value = float(raw_percent[:-1])
    except ValueError as exc:
        raise RuntimeError(f"invalid or missing TOTAL coverage percentage for {name}") from exc
    if not math.isfinite(value) or not 0.0 <= value <= 100.0:
        raise RuntimeError(f"invalid or missing TOTAL coverage percentage for {name}")
    return f"{raw_percent[:-1]} %"


def _validated_coverage_report(result: BoundedSubprocessResult, name: str) -> str:
    """Fail closed on report execution errors, then parse its finite TOTAL."""
    if result.timed_out:
        raise RuntimeError(f"coverage report timed out for {name} after 300s")
    if result.returncode != 0 or result.command_error:
        detail = result.command_error or result.stderr.strip() or result.stdout.strip() or "no diagnostic output"
        raise RuntimeError(f"coverage report failed for {name} (exit {result.returncode}): {detail[-1000:]}")
    return _coverage_total_from_report(result.stdout, name)


def _fresh_coverage_measurement_data_file(project_dir: Path, name: str) -> Path:
    """Remove stale data so the first non-append group starts from zero."""
    data_file = project_dir / f".coverage.measure_{name}"
    data_file.unlink(missing_ok=True)
    return data_file


def _coverage_measurement_environment(data_file: Path) -> dict[str, str]:
    """Return the child environment with conflicting global opt-ins removed."""
    env = dict(get_subprocess_env())
    for inherited_opt_in in tuple(env):
        if inherited_opt_in in {
            *_COVERAGE_GIT_ENVIRONMENT_VARIABLES,
            "TEMPLATE_ACTIVE_INFERENCE_ALLOW_GATE_REBUILD",
            "UV_FROZEN",
            "UV_NO_SYNC",
        } or inherited_opt_in.startswith(_COVERAGE_GIT_ENVIRONMENT_PREFIXES):
            env.pop(inherited_opt_in, None)
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_SYSTEM"] = os.devnull
    env["COVERAGE_FILE"] = str(data_file)
    return env


@dataclass(frozen=True)
class CoverageVerificationResult:
    """Structured outcome of one all-exemplar coverage verification."""

    all_match: bool
    measurement_complete: bool
    snapshot_rewritten: bool
    drifted_count: int
    failed_count: int
    measured_count: int
    report: str


def measure_exemplar_coverage(repo_root: Path, name: str) -> str:
    """Run one exemplar's release-profile coverage gate and return its total."""
    canonical_project_dir = repo_root.resolve() / "projects" / "templates" / name
    if not canonical_project_dir.is_dir():
        raise RuntimeError(f"exemplar not checked out: {name}")
    with _coverage_measurement_workspace(repo_root, name) as (environment_project, measurement_project):
        data_file = _fresh_coverage_measurement_data_file(measurement_project, name)
        env = _coverage_measurement_environment(data_file)
        profile = resolve_test_profile("release")
        command = _coverage_measurement_command(
            measurement_project,
            environment_project_dir=environment_project,
        )
        measurement_policy = _coverage_measurement_process_policy(name)
        strategy = _coverage_measurement_strategy(name)
        try:
            run = run_with_policy(
                command,
                cwd=repo_root,
                env=env,
                policy=measurement_policy,
            )
            if run.timed_out:
                raise RuntimeError(
                    f"coverage run timed out for {name} after {measurement_policy.timeout_seconds:g}s "
                    f"using the {profile.name} profile via {strategy}"
                )
            if run.returncode != 0 or run.command_error:
                tail = "\n".join((run.stdout + run.stderr).splitlines()[-8:])
                detail = run.command_error or tail or "no diagnostic output"
                raise RuntimeError(f"coverage run failed for {name} via {strategy} (exit {run.returncode}):\n{detail}")
            report_command = _coverage_report_command(
                measurement_project,
                environment_project_dir=environment_project,
            )
            report = run_with_policy(
                report_command,
                cwd=repo_root,
                env=env,
                policy=_coverage_process_policy("coverage-report", 300),
            )
            return _validated_coverage_report(report, name)
        finally:
            data_file.unlink(missing_ok=True)


def verify_exemplar_coverage_result(
    repo_root: Path,
    *,
    rewrite: bool = False,
) -> CoverageVerificationResult:
    """Re-measure every exemplar and return a fail-closed structured result."""
    measured: dict[str, str] = {}
    failures: list[str] = []
    for row in EXEMPLAR_SNAPSHOT:
        try:
            measured[row.name] = measure_exemplar_coverage(repo_root, row.name)
        except RuntimeError as exc:
            failures.append(f"{row.name}: {exc}")

    return _finalize_exemplar_coverage_result(
        measured,
        failures,
        rewrite=rewrite,
    )


def _finalize_exemplar_coverage_result(
    measured: dict[str, str],
    failures: list[str],
    *,
    rewrite: bool,
    snapshot: tuple[ExemplarSnapshot, ...] = EXEMPLAR_SNAPSHOT,
    source_path: Path | None = None,
) -> CoverageVerificationResult:
    """Compare measurements and publish only a complete snapshot refresh."""
    expected_names = {row.name for row in snapshot}
    measured_names = set(measured)
    effective_failures = list(failures)
    if measured_names != expected_names and not effective_failures:
        missing = sorted(expected_names - measured_names)
        unexpected = sorted(measured_names - expected_names)
        details: list[str] = []
        if missing:
            details.append(f"missing={','.join(missing)}")
        if unexpected:
            details.append(f"unexpected={','.join(unexpected)}")
        effective_failures.append(f"coverage measurement roster incomplete ({'; '.join(details)})")

    lines = [f"{'exemplar':44} {'recorded':>10} {'measured':>10}  status"]
    mismatched: list[tuple[str, str, str]] = []
    for row in snapshot:
        actual = measured.get(row.name)
        if actual is None:
            lines.append(f"{row.name:44} {row.coverage_pct:>10} {'-':>10}  NOT MEASURED")
            continue
        ok = actual.replace(" ", "") == row.coverage_pct.replace(" ", "")
        if not ok:
            mismatched.append((row.name, row.coverage_pct, actual))
        lines.append(f"{row.name:44} {row.coverage_pct:>10} {actual:>10}  {'ok' if ok else 'DRIFTED'}")

    measurement_complete = not effective_failures and measured_names == expected_names
    snapshot_rewritten = rewrite and measurement_complete
    if snapshot_rewritten:
        _rewrite_exemplar_snapshot(measured, source_path)
        lines.append(f"\nrewrote EXEMPLAR_SNAPSHOT with {len(measured)} measured values")
    elif rewrite and measured:
        lines.append("\nEXEMPLAR_SNAPSHOT not rewritten because the measurement set was incomplete")
    for failure in effective_failures:
        lines.append(f"MEASUREMENT FAILED — {failure}")
    lines.append(f"\n{len(mismatched)} drifted, {len(effective_failures)} failed, {len(measured)} measured")
    return CoverageVerificationResult(
        all_match=not mismatched and measurement_complete,
        measurement_complete=measurement_complete,
        snapshot_rewritten=snapshot_rewritten,
        drifted_count=len(mismatched),
        failed_count=len(effective_failures),
        measured_count=len(measured),
        report="\n".join(lines),
    )


def verify_exemplar_coverage(repo_root: Path, *, rewrite: bool = False) -> tuple[bool, str]:
    """Re-measure coverage while preserving the historical tuple interface."""
    result = verify_exemplar_coverage_result(repo_root, rewrite=rewrite)
    return result.all_match, result.report


def _rewrite_exemplar_snapshot(measured: dict[str, str], source_path: Path | None = None) -> None:
    """Rewrite an ``EXEMPLAR_SNAPSHOT`` tuple with measured percentages."""
    source_path = source_path or Path(__file__)
    text = source_path.read_text(encoding="utf-8")

    def _replace(match: re.Match[str]) -> str:
        name = match.group("name")
        actual = measured.get(name)
        return match.group(0) if actual is None else f'ExemplarSnapshot("{name}", "{actual}")'

    updated = re.sub(
        r'ExemplarSnapshot\(\s*"(?P<name>[^"]+)"\s*,\s*"[^"]*"\s*\)',
        _replace,
        text,
    )
    if updated != text:
        source_path.write_text(updated, encoding="utf-8")


def exemplar_source_hash(repo_root: Path, name: str) -> str:
    """Hash tracked and non-ignored project inputs that can affect coverage."""
    project_root = repo_root / "projects" / "templates" / name
    digest = hashlib.sha256()
    for logical_path, physical_path in _exemplar_source_files(repo_root, project_root):
        if physical_path.is_symlink():
            target = _validated_coverage_input_symlink_target(repo_root, physical_path)
            digest.update(logical_path.relative_to(project_root).as_posix().encode("utf-8"))
            digest.update(b"\0symlink\0")
            digest.update(os.readlink(physical_path).encode("utf-8"))
            digest.update(b"\0")
            if target.is_file():
                digest.update(target.read_bytes())
                digest.update(b"\0")
                continue
            if not target.is_dir():
                raise RuntimeError(f"coverage input symlink target is not a file or directory: {physical_path}")
            for child_logical, child_physical in _tracked_symlink_children(repo_root, logical_path, target):
                digest.update(child_logical.relative_to(project_root).as_posix().encode("utf-8"))
                digest.update(b"\0")
                digest.update(child_physical.read_bytes())
                digest.update(b"\0")
            continue
        if not physical_path.is_file():
            continue
        digest.update(logical_path.relative_to(project_root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(physical_path.read_bytes())
        digest.update(b"\0")
    if name == _ACTIVE_COVERAGE_PROJECT:
        support_identity = _coverage_support_identity(repo_root)
        digest.update(b"repository-support\0")
        digest.update(str(support_identity["digest"]).encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def _exemplar_source_files(repo_root: Path, project_root: Path) -> list[tuple[Path, Path]]:
    """Return logical/physical project files for the coverage-input inventory."""
    relative_root = project_root.relative_to(repo_root).as_posix()
    tracked = run_with_policy(
        ["git", "ls-files", "-z", "--", relative_root],
        cwd=repo_root,
        env=_coverage_git_environment(),
        policy=_coverage_process_policy("coverage-source-inventory", 30),
    )
    untracked = run_with_policy(
        ["git", "ls-files", "-z", "--others", "--exclude-standard", "--", relative_root],
        cwd=repo_root,
        env=_coverage_git_environment(),
        policy=_coverage_process_policy("coverage-source-inventory", 30),
    )
    if (
        tracked.timed_out
        or untracked.timed_out
        or tracked.returncode != 0
        or untracked.returncode != 0
        or tracked.command_error
        or untracked.command_error
    ):
        raise RuntimeError("coverage input inventory requires successful Git tracked/nonignored queries")
    relative_paths = sorted(
        {
            *_nul_delimited_git_paths(tracked.stdout, inventory="tracked coverage inputs"),
            *_nul_delimited_git_paths(untracked.stdout, inventory="nonignored coverage inputs"),
        }
    )
    candidates = [(repo_root / relative, repo_root / relative) for relative in relative_paths]
    return [
        (logical, physical)
        for logical, physical in candidates
        if _is_coverage_input_path(logical, project_root) and (physical.is_symlink() or physical.is_file())
    ]


def _is_coverage_input_path(path: Path, project_root: Path) -> bool:
    """Return whether *path* belongs to the stable project input surface."""
    try:
        relative = path.relative_to(project_root)
    except ValueError:
        return False
    if not relative.parts:
        return False
    if any(part in _COVERAGE_INPUT_EXCLUDED_PARTS for part in relative.parts):
        return False
    if any(part.startswith(".coverage.") for part in relative.parts):
        return False
    if any(part.endswith(_COVERAGE_INPUT_EXCLUDED_SUFFIXES) for part in relative.parts):
        return False
    return relative.suffix not in _COVERAGE_INPUT_EXCLUDED_FILE_SUFFIXES


def _nul_delimited_git_paths(output: str, *, inventory: str) -> list[str]:
    """Parse one complete ``git -z`` pathname stream without newline loss."""
    if not output:
        return []
    if not output.endswith("\0"):
        raise RuntimeError(f"{inventory} returned malformed non-NUL-terminated output")
    paths = output[:-1].split("\0")
    if any(not path for path in paths):
        raise RuntimeError(f"{inventory} returned an empty pathname")
    return paths


def _tracked_symlink_children(repo_root: Path, logical_path: Path, target_root: Path) -> list[tuple[Path, Path]]:
    """Return inventoried regular files reached through an in-repository symlink."""
    repo_root = repo_root.resolve()
    target_rel = target_root.relative_to(repo_root).as_posix()
    tracked = run_with_policy(
        ["git", "ls-files", "-z", "--", target_rel],
        cwd=repo_root,
        env=_coverage_git_environment(),
        policy=_coverage_process_policy("coverage-source-inventory", 30),
    )
    untracked = run_with_policy(
        ["git", "ls-files", "-z", "--others", "--exclude-standard", "--", target_rel],
        cwd=repo_root,
        env=_coverage_git_environment(),
        policy=_coverage_process_policy("coverage-source-inventory", 30),
    )
    if (
        tracked.timed_out
        or untracked.timed_out
        or tracked.returncode != 0
        or untracked.returncode != 0
        or tracked.command_error
        or untracked.command_error
    ):
        raise RuntimeError("linked coverage input inventory requires successful Git tracked/nonignored queries")
    relatives = sorted(
        {
            *_nul_delimited_git_paths(tracked.stdout, inventory="tracked linked coverage inputs"),
            *_nul_delimited_git_paths(untracked.stdout, inventory="nonignored linked coverage inputs"),
        }
    )
    children: list[tuple[Path, Path]] = []
    for relative in relatives:
        physical = repo_root / relative
        if not _is_coverage_input_path(physical, repo_root):
            continue
        if physical.is_symlink():
            raise RuntimeError(f"nested coverage input symlink is unsupported: {physical}")
        if physical.is_file():
            children.append((logical_path / physical.relative_to(target_root), physical))
    return children


def _validated_coverage_input_symlink_target(repo_root: Path, symlink_path: Path) -> Path:
    """Return a confined, non-runtime symlink target or fail closed."""
    resolved_root = repo_root.resolve()
    try:
        target = symlink_path.resolve(strict=True)
    except OSError as exc:
        raise RuntimeError(f"coverage input symlink target is unavailable: {symlink_path}") from exc
    try:
        target.relative_to(resolved_root)
    except ValueError as exc:
        raise RuntimeError(f"coverage input symlink target escapes the repository: {symlink_path}") from exc
    if not _is_coverage_input_path(target, resolved_root):
        raise RuntimeError(f"coverage input symlink targets an excluded runtime or output path: {symlink_path}")
    return target


def build_coverage_provenance(repo_root: Path) -> dict[str, object]:
    """Build provenance for the checked-in coverage percentages."""
    source_revision = _run_coverage_git(
        ["git", "rev-parse", "--verify", "HEAD^{commit}"],
        cwd=repo_root,
        action="resolving the coverage provenance source commit",
    )
    if not source_revision:
        raise RuntimeError("could not resolve source commit: empty revision")
    source_hashes = {row.name: exemplar_source_hash(repo_root, row.name) for row in EXEMPLAR_SNAPSHOT}
    measurement_support = {_ACTIVE_COVERAGE_PROJECT: _coverage_support_identity(repo_root)}
    return {
        "schema_version": COVERAGE_PROVENANCE_SCHEMA_VERSION,
        "source_inventory_mode": COVERAGE_SOURCE_INVENTORY_MODE,
        "source_tree_identity": {
            "algorithm": "sha256",
            "inventory_mode": COVERAGE_SOURCE_INVENTORY_MODE,
            "measurement_support": measurement_support,
            "projects": source_hashes,
        },
        "measured_at": EXEMPLAR_SNAPSHOT_DATE,
        "source_commit": source_revision,
        "projects": {
            row.name: {"coverage_pct": row.coverage_pct, "source_hash": source_hashes[row.name]}
            for row in EXEMPLAR_SNAPSHOT
        },
    }


def write_coverage_provenance(repo_root: Path) -> Path:
    """Write coverage source provenance after coverage gates have run."""
    target = repo_root / COVERAGE_PROVENANCE_RELATIVE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(build_coverage_provenance(repo_root), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target


def validate_coverage_provenance(repo_root: Path) -> None:
    """Fail closed when a coverage percentage is stale for its source tree."""
    path = repo_root / COVERAGE_PROVENANCE_RELATIVE_PATH
    if not path.is_file():
        raise RuntimeError(f"missing coverage provenance: {COVERAGE_PROVENANCE_RELATIVE_PATH}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("coverage provenance root must be a mapping")
    if payload.get("schema_version") != COVERAGE_PROVENANCE_SCHEMA_VERSION:
        raise RuntimeError(f"coverage provenance schema mismatch: expected {COVERAGE_PROVENANCE_SCHEMA_VERSION}")
    if payload.get("source_inventory_mode") != COVERAGE_SOURCE_INVENTORY_MODE:
        raise RuntimeError("coverage provenance source inventory mode is missing or unsupported")
    source_tree_identity = payload.get("source_tree_identity")
    if not isinstance(source_tree_identity, dict):
        raise RuntimeError("coverage provenance source-tree identity is missing")
    if source_tree_identity.get("algorithm") != "sha256":
        raise RuntimeError("coverage provenance source-tree identity algorithm is unsupported")
    if source_tree_identity.get("inventory_mode") != COVERAGE_SOURCE_INVENTORY_MODE:
        raise RuntimeError("coverage provenance source-tree identity inventory mode is unsupported")
    source_hashes = source_tree_identity.get("projects")
    if not isinstance(source_hashes, dict):
        raise RuntimeError("coverage provenance source-tree identity has no project mapping")
    projects = payload.get("projects")
    if not isinstance(projects, dict):
        raise RuntimeError("coverage provenance has no projects mapping")
    expected_names = {row.name for row in EXEMPLAR_SNAPSHOT}
    if set(source_hashes) != expected_names:
        raise RuntimeError("coverage provenance source-tree identity project roster does not match the public snapshot")
    if set(projects) != expected_names:
        raise RuntimeError("coverage provenance project roster does not match the public snapshot")
    measurement_support = source_tree_identity.get("measurement_support")
    expected_measurement_support = {_ACTIVE_COVERAGE_PROJECT: _coverage_support_identity(repo_root)}
    if measurement_support != expected_measurement_support:
        raise RuntimeError("coverage provenance measurement-support identity is stale or malformed")
    for row in EXEMPLAR_SNAPSHOT:
        record = projects.get(row.name)
        if not isinstance(record, dict) or record.get("coverage_pct") != row.coverage_pct:
            raise RuntimeError(f"coverage provenance percentage mismatch: {row.name}")
        if record.get("source_hash") != source_hashes.get(row.name):
            raise RuntimeError(f"coverage provenance source-tree identity disagrees with project row: {row.name}")
        if record.get("source_hash") != exemplar_source_hash(repo_root, row.name):
            raise RuntimeError(
                f"stale coverage snapshot for {row.name}: source hash changed; "
                "rerun its coverage gate, then refresh coverage provenance"
            )


__all__ = [
    "COVERAGE_MEASUREMENT_TIMEOUT_SECONDS",
    "COVERAGE_PROVENANCE_RELATIVE_PATH",
    "COVERAGE_PROVENANCE_SCHEMA_VERSION",
    "COVERAGE_SOURCE_INVENTORY_MODE",
    "COVERAGE_SUPPORT_IDENTITY_MODE",
    "CoverageVerificationResult",
    "EXEMPLAR_SNAPSHOT",
    "EXEMPLAR_SNAPSHOT_DATE",
    "ExemplarSnapshot",
    "_coverage_measurement_command",
    "_coverage_measurement_data_file",
    "_rewrite_exemplar_snapshot",
    "build_coverage_provenance",
    "exemplar_source_hash",
    "measure_exemplar_coverage",
    "validate_coverage_provenance",
    "verify_exemplar_coverage",
    "verify_exemplar_coverage_result",
    "write_coverage_provenance",
]
