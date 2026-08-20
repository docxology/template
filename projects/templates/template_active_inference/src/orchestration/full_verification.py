"""Full project verification workflow: preflight, chunked pytest, coverage pass."""

from __future__ import annotations

import hashlib
import io
import json
import os
import shlex
import subprocess
import sys
import time
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Literal

import defusedxml.ElementTree as ET
from coverage import Coverage

from .portable_execution import build_bounded_env, run_bounded_subprocess
from .semantic_coverage import (
    SEMANTIC_SHEAF_CERTIFICATE_COVERAGE_LABEL as _SEMANTIC_SHEAF_CERTIFICATE_COVERAGE_LABEL,
    SEMANTIC_SHEAF_CERTIFICATE_COVERAGE_SELECTORS as _SEMANTIC_SHEAF_CERTIFICATE_COVERAGE_SELECTORS,
    SEMANTIC_SHEAF_COVERAGE_MODULE as _SEMANTIC_SHEAF_COVERAGE_MODULE,
    SEMANTIC_SHEAF_DEPENDENCY_COVERAGE_LABEL as _SEMANTIC_SHEAF_DEPENDENCY_COVERAGE_LABEL,
    SEMANTIC_SHEAF_DEPENDENCY_COVERAGE_SELECTORS as _SEMANTIC_SHEAF_DEPENDENCY_COVERAGE_SELECTORS,
    semantic_sheaf_test_selectors as _semantic_sheaf_test_selectors,
)

VerificationProfile = Literal["quick", "release", "exhaustive"]

_PROJECT_TEST_RECEIPT_SCHEMA = "template/project-test-receipt/1"
_PROJECT_TEST_RECEIPT_ENV = "TEMPLATE_PROJECT_TEST_RECEIPT"
_PROJECT_TEST_RUN_ID_ENV = "TEMPLATE_PROJECT_TEST_RUN_ID"
_PROJECT_TEST_PROJECT_ENV = "TEMPLATE_PROJECT_TEST_PROJECT"
_PROJECT_TEST_COMMAND_SHA_ENV = "TEMPLATE_PROJECT_TEST_COMMAND_SHA256"
_MAX_JUNIT_BYTES = 50_000_000
_MAX_PYTEST_EVIDENCE_BYTES = 10_000
_PYTEST_EVIDENCE_SCHEMA = "template-active-inference/pytest-evidence/1"


def _relative_test_path(project_root: Path, path: Path) -> str:
    return str(path.relative_to(project_root))


_REFRESHABLE_GENERATORS = frozenset(
    {
        "compose_manuscript.py",
        "z_generate_manuscript_variables.py",
        "generate_figures.py",
        "generate_method_inventory.py",
    }
)
_GENERATOR_OBSERVER_FLAGS = frozenset({"--check", "--list-tracks", "--validate-only"})
_FINGERPRINT_EXCLUDED_PARTS = frozenset({".git", ".pytest_cache", ".venv", "htmlcov", "__pycache__"})
_MAX_FAILURE_STREAM_CHARS = 4_000
_FIXED_POINT_COVERAGE_MODULE = "tests/test_fixed_point_direct.py"
_FIXED_POINT_COVERAGE_LABEL = "Fixed-point settlement checks"
_DEFAULT_COMMAND_TIMEOUT_SECONDS = 1800
_FIXED_POINT_COVERAGE_TIMEOUT_SECONDS = 2400


def _project_state_fingerprint(project_root: Path) -> str:
    """Return a deterministic source/output fingerprint for refresh caching.

    The fingerprint intentionally includes both inputs and generated contract
    outputs. A refresh is skipped only when the exact same generator already
    observed this byte state after a successful run, so a downstream producer
    changing any contract artifact naturally invalidates the cache.
    """
    digest = hashlib.sha256()
    for path in sorted(project_root.rglob("*")):
        if not path.is_file() or _FINGERPRINT_EXCLUDED_PARTS.intersection(path.parts):
            continue
        if path.name.startswith(".coverage"):
            continue
        relative = path.relative_to(project_root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        try:
            digest.update(path.read_bytes())
        except OSError:
            # A concurrently written disposable output will be reflected by
            # the next fingerprint; never turn cache bookkeeping into a gate.
            continue
        digest.update(b"\0")
    return digest.hexdigest()


def _generator_name(command: list[str]) -> str | None:
    """Return the refreshable script name in a command, if any."""
    if _GENERATOR_OBSERVER_FLAGS.intersection(command):
        return None
    for part in command:
        name = Path(part).name
        if name in _REFRESHABLE_GENERATORS:
            return name
    return None


def _bounded_failure_detail(*, command_error: str, stdout: str, stderr: str) -> str:
    """Return labeled, tail-bounded diagnostics from every subprocess stream."""

    blocks: list[str] = []
    for label, value in (("command error", command_error), ("stdout", stdout), ("stderr", stderr)):
        detail = value.strip()
        if not detail:
            continue
        if len(detail) > _MAX_FAILURE_STREAM_CHARS:
            detail = (
                f"...[truncated to final {_MAX_FAILURE_STREAM_CHARS} characters]\n{detail[-_MAX_FAILURE_STREAM_CHARS:]}"
            )
        blocks.append(f"[{label}]\n{detail}")
    return "\n".join(blocks)


def _command_timeout_seconds(label: str) -> int:
    """Return the sole named command-timeout exception or the default bound."""
    if label == f"Coverage pass: {_FIXED_POINT_COVERAGE_LABEL}":
        return _FIXED_POINT_COVERAGE_TIMEOUT_SECONDS
    return _DEFAULT_COMMAND_TIMEOUT_SECONDS


class _RefreshCache:
    """In-run fixed-point cache for idempotent generator commands."""

    def __init__(self, *, clock: Callable[[], float] = time.perf_counter) -> None:
        """Initialize an empty in-run refresh cache."""
        self._last_outputs: dict[str, str] = {}
        self._clock = clock
        self._events: list[dict[str, object]] = []

    def run(
        self,
        project_root: Path,
        command: list[str],
        label: str,
        command_runner: Callable[..., None],
    ) -> None:
        """Run a generator command, skipping it when the project state is unchanged.

        If the command's generator is refreshable and the project fingerprint
        matches the last observed state for that generator, the command is
        skipped.  Otherwise the command is executed and the new fingerprint
        is cached.
        """
        generator = _generator_name(command)
        if generator is None:
            started = self._clock()
            command_runner(project_root, command, label)
            self._events.append(
                {
                    "label": label,
                    "generator": None,
                    "action": "ran",
                    "elapsed_seconds": round(self._clock() - started, 6),
                }
            )
            return
        before = _project_state_fingerprint(project_root)
        if self._last_outputs.get(generator) == before:
            print(f"\n==> {label}\n    fixed point unchanged; skipped {generator}")
            self._events.append({"label": label, "generator": generator, "action": "skipped", "elapsed_seconds": 0.0})
            return
        started = self._clock()
        command_runner(project_root, command, label)
        self._last_outputs[generator] = _project_state_fingerprint(project_root)
        self._events.append(
            {
                "label": label,
                "generator": generator,
                "action": "ran",
                "elapsed_seconds": round(self._clock() - started, 6),
            }
        )

    def receipt(self, *, baseline_seconds: float | None = None) -> dict[str, object]:
        """Return timing/cache evidence without making a performance claim."""
        elapsed_values: list[float] = []
        for event in self._events:
            elapsed = event.get("elapsed_seconds")
            if not isinstance(elapsed, (int, float)) or isinstance(elapsed, bool):
                raise ValueError("refresh receipt elapsed_seconds must be numeric")
            elapsed_values.append(float(elapsed))
        observed = round(sum(elapsed_values), 6)
        reduction = None
        target_met = None
        if baseline_seconds is not None and baseline_seconds > 0:
            reduction = round(1.0 - observed / baseline_seconds, 6)
            target_met = reduction >= 0.30
        return {
            "schema_version": "template-active-inference/refresh-receipt/1",
            "events": tuple(self._events),
            "observed_seconds": observed,
            "baseline_seconds": baseline_seconds,
            "reduction_fraction": reduction,
            "target_reduction_fraction": 0.30,
            "target_met": target_met,
        }


def _all_test_modules(project_root: Path) -> list[str]:
    return [_relative_test_path(project_root, path) for path in sorted((project_root / "tests").rglob("test_*.py"))]


def _chunked_test_groups(project_root: Path) -> list[tuple[str, list[str]]]:
    chunks: list[tuple[str, list[str]]] = [
        (
            "Focused contract and infrastructure checks",
            [
                "tests/test_validation_spine.py",
                "tests/test_documentation_contracts.py",
                "tests/test_method_inventory.py",
                "tests/test_gate_support_contracts.py",
            ],
        ),
        (
            "Gate and manuscript-focused checks",
            [
                "tests/gates/test_claim_ledger.py",
                "tests/gates/test_manuscript_gates.py",
                "tests/gates/test_output_gates.py",
            ],
        ),
    ]
    sheaf_chunks = [
        _relative_test_path(project_root, path) for path in sorted((project_root / "tests").glob("test_sheaf_*.py"))
    ]
    chunks.append(
        (
            "Roadmap and sheaf consolidation checks",
            [
                "tests/test_roadmap_promotion.py",
                *sheaf_chunks,
            ],
        )
    )
    chunks.extend(
        [
            (
                "Canonical sheaf negative-control checks",
                ["tests/test_track_consolidation_negative.py"],
            ),
            (
                "Sheaf consolidation surface checks",
                [
                    "tests/test_track_consolidation_surface.py",
                    "tests/test_track_consolidation_support_contracts.py",
                ],
            ),
        ]
    )
    return [(label, modules) for label, modules in chunks if modules]


_ANALYTICAL_FIGURE_FORMAL_COVERAGE_MODULES = (
    "tests/test_aggregate_forgery_controls.py",
    "tests/test_analytical_guards.py",
    "tests/test_bernoulli_toy.py",
    "tests/test_claim_ledger_direct.py",
    "tests/test_coverage_pipeline.py",
    "tests/test_cue_tmaze_model.py",
    "tests/test_decomposition.py",
    "tests/test_dirichlet_learning.py",
    "tests/test_efe_decomposition.py",
    "tests/test_efe_lean_identity.py",
    "tests/test_extension_scripts.py",
    "tests/test_figure_io_direct.py",
    "tests/test_figure_style.py",
    "tests/test_figures.py",
    "tests/test_figures_sheaf_direct.py",
    "tests/test_formal_interop_direct.py",
    "tests/test_free_energy.py",
    "tests/test_gnn.py",
    "tests/test_graph_world.py",
    "tests/test_helpers_direct.py",
    "tests/test_image_content_hash.py",
    "tests/test_integration_audit_modularity.py",
    "tests/test_integrity_remediations.py",
    "tests/test_invariants.py",
    "tests/test_joint_dist.py",
    "tests/test_layers_report.py",
    "tests/test_lean_boundary.py",
    "tests/test_lean_gate.py",
    "tests/test_lean_gate_direct.py",
)
_MANUSCRIPT_PIPELINE_COVERAGE_MODULES = (
    "tests/test_manuscript_hydrate.py",
    "tests/test_manuscript_refresh_direct.py",
    "tests/test_manuscript_variables.py",
    "tests/test_pipeline_artifacts.py",
    "tests/test_pipeline_manifest.py",
    "tests/test_precision_sweep.py",
    "tests/test_pymdp_config.py",
)
_RENDERING_SEMANTIC_VALIDATION_COVERAGE_MODULES = (
    "tests/test_render_pdf.py",
    "tests/test_scholarship_direct.py",
    "tests/test_self_contained.py",
    "tests/test_semantic_certificate_direct.py",
    "tests/test_semantic_extensions.py",
    "tests/test_semantic_issues_direct.py",
    "tests/test_semantic_issues_more_direct.py",
)


def _coverage_test_groups(project_root: Path) -> list[tuple[str, list[str]]]:
    chunks = _chunked_test_groups(project_root)
    chunked_modules = {module for _, modules in chunks for module in modules}
    residual_groups = [
        (
            "Analytical, figure, and formal checks",
            list(_ANALYTICAL_FIGURE_FORMAL_COVERAGE_MODULES),
        ),
        (
            "Manuscript, pipeline, precision, and configuration checks",
            list(_MANUSCRIPT_PIPELINE_COVERAGE_MODULES),
        ),
        (
            "Rendering, scholarship, and semantic validation checks",
            list(_RENDERING_SEMANTIC_VALIDATION_COVERAGE_MODULES),
        ),
    ]
    semantic_groups = [
        (
            _SEMANTIC_SHEAF_CERTIFICATE_COVERAGE_LABEL,
            list(_SEMANTIC_SHEAF_CERTIFICATE_COVERAGE_SELECTORS),
        ),
        (
            _SEMANTIC_SHEAF_DEPENDENCY_COVERAGE_LABEL,
            list(_SEMANTIC_SHEAF_DEPENDENCY_COVERAGE_SELECTORS),
        ),
    ]
    explicitly_planned_modules = (
        {module for _, modules in residual_groups for module in modules}
        | chunked_modules
        | {_FIXED_POINT_COVERAGE_MODULE, _SEMANTIC_SHEAF_COVERAGE_MODULE}
    )
    terminal_modules = [
        module for module in _all_test_modules(project_root) if module not in explicitly_planned_modules
    ]
    return [
        *chunks,
        (_FIXED_POINT_COVERAGE_LABEL, [_FIXED_POINT_COVERAGE_MODULE]),
        *residual_groups,
        *semantic_groups,
        ("Simulation, support, and visualization checks", terminal_modules),
    ]


def _validate_coverage_test_groups(project_root: Path, groups: list[tuple[str, list[str]]]) -> None:
    """Fail closed unless groups exactly cover modules and semantic node selectors."""
    empty_groups = sorted(label for label, selectors in groups if not selectors)
    expected_modules = set(_all_test_modules(project_root))
    expected_ordinary_modules = expected_modules - {_SEMANTIC_SHEAF_COVERAGE_MODULE}
    expected_semantic_selectors = _semantic_sheaf_test_selectors(project_root)
    planned_selectors = [selector for _, selectors in groups for selector in selectors]
    counts = Counter(planned_selectors)
    duplicates = sorted(selector for selector, count in counts.items() if count != 1)

    ordinary_modules = [selector for selector in planned_selectors if "::" not in selector]
    ordinary_counts = Counter(ordinary_modules)
    missing_modules = sorted(expected_ordinary_modules.difference(ordinary_counts))
    unexpected_modules = sorted(set(ordinary_modules).difference(expected_ordinary_modules))
    semantic_bare_module = _SEMANTIC_SHEAF_COVERAGE_MODULE in ordinary_counts
    semantic_prefix = f"{_SEMANTIC_SHEAF_COVERAGE_MODULE}::"
    planned_semantic_selectors = [selector for selector in planned_selectors if selector.startswith(semantic_prefix)]
    unexpected_node_selectors = sorted(
        selector for selector in planned_selectors if "::" in selector and not selector.startswith(semantic_prefix)
    )
    missing_semantic = sorted(set(expected_semantic_selectors).difference(planned_semantic_selectors))
    unexpected_semantic = sorted(set(planned_semantic_selectors).difference(expected_semantic_selectors))
    semantic_order_mismatch = planned_semantic_selectors != expected_semantic_selectors
    actual_semantic_groups = [
        (label, selectors)
        for label, selectors in groups
        if any(selector.startswith(semantic_prefix) for selector in selectors)
    ]
    expected_semantic_groups = [
        (
            _SEMANTIC_SHEAF_CERTIFICATE_COVERAGE_LABEL,
            list(_SEMANTIC_SHEAF_CERTIFICATE_COVERAGE_SELECTORS),
        ),
        (
            _SEMANTIC_SHEAF_DEPENDENCY_COVERAGE_LABEL,
            list(_SEMANTIC_SHEAF_DEPENDENCY_COVERAGE_SELECTORS),
        ),
    ]
    semantic_group_mismatch = actual_semantic_groups != expected_semantic_groups

    details: list[str] = []
    if empty_groups:
        details.append(f"empty={empty_groups}")
    if duplicates:
        details.append(f"duplicates={duplicates}")
    if missing_modules:
        details.append(f"missing_modules={missing_modules}")
    if unexpected_modules:
        details.append(f"unexpected_modules={unexpected_modules}")
    if semantic_bare_module:
        details.append(f"semantic_bare_module={_SEMANTIC_SHEAF_COVERAGE_MODULE}")
    if unexpected_node_selectors:
        details.append(f"unexpected_node_selectors={unexpected_node_selectors}")
    if missing_semantic:
        details.append(f"missing_semantic_selectors={missing_semantic}")
    if unexpected_semantic:
        details.append(f"unexpected_semantic_selectors={unexpected_semantic}")
    if semantic_order_mismatch:
        details.append("semantic_selector_order=does_not_match_source")
    if semantic_group_mismatch:
        details.append("semantic_selector_groups=do_not_match_declared_8_7_cohorts")
    if details:
        raise RuntimeError("coverage groups must partition tests exactly once: " + "; ".join(details))


def _validated_coverage_test_groups(project_root: Path) -> list[tuple[str, list[str]]]:
    """Return a complete module/node partition validated against test source."""
    groups = _coverage_test_groups(project_root)
    _validate_coverage_test_groups(project_root, groups)
    return groups


def _profile_marker_args(profile: VerificationProfile | None) -> list[str]:
    """Return additive pytest selection args for a named verification profile."""
    if profile is None:
        return []
    if profile == "quick":
        expression = (
            "not slow and not long_running and not requires_ollama and not requires_docker "
            "and not network and not bench and not benchmark and not performance "
            "and not private_project and not external_fixture"
        )
    elif profile == "release":
        expression = (
            "not long_running and not requires_ollama and not requires_docker and not network "
            "and not bench and not benchmark and not performance and not private_project "
            "and not external_fixture"
        )
    elif profile == "exhaustive":
        expression = (
            "not requires_ollama and not requires_docker and not network "
            "and not bench and not benchmark and not performance and not private_project "
            "and not external_fixture"
        )
    else:  # pragma: no cover - Literal callers are validated by the CLI
        raise ValueError(f"unknown verification profile: {profile}")
    return ["-m", expression]


def _coverage_command(
    selectors: list[str],
    *,
    append: bool,
    final: bool,
    profile: VerificationProfile | None = None,
    junit_path: Path | None = None,
    evidence_path: Path | None = None,
) -> list[str]:
    # Use the verifier's current interpreter so Stage 01's exact, injected
    # pytest/Coverage versions also produce the database and JUnit evidence.
    # A nested ``uv run`` would ignore the outer overlay and silently fall
    # back to the project's independently resolved environment.
    cmd = [sys.executable, "-m", "pytest", *selectors, "--cov=src", "-q"]
    cmd.extend(_profile_marker_args(profile))
    if append:
        cmd.append("--cov-append")
    if final:
        cmd.extend(["--cov-report=term-missing", "--cov-fail-under=90", "--durations=20"])
    else:
        # The project TOML sets fail_under=90 for the aggregate suite. A
        # partial chunk is intentionally below that threshold; enforce it only
        # on the final append pass.
        cmd.extend(["--cov-report=", "--cov-fail-under=0"])
    if junit_path is not None:
        cmd.append(f"--junitxml={junit_path}")
    if evidence_path is not None:
        cmd.append(f"--template-test-evidence={evidence_path}")
    return cmd


def _project_test_receipt_context() -> tuple[Path, str, str, str] | None:
    """Return the Stage-01 receipt context, if the generic runner requested one."""
    raw_path = os.environ.get(_PROJECT_TEST_RECEIPT_ENV, "").strip()
    if not raw_path:
        return None
    run_id = os.environ.get(_PROJECT_TEST_RUN_ID_ENV, "").strip()
    project = os.environ.get(_PROJECT_TEST_PROJECT_ENV, "").strip()
    command_sha = os.environ.get(_PROJECT_TEST_COMMAND_SHA_ENV, "").strip()
    if not run_id or not project or not command_sha:
        raise RuntimeError("Stage-01 receipt environment is incomplete")
    receipt_path = Path(raw_path)
    if not receipt_path.is_absolute():
        raise RuntimeError("Stage-01 receipt path must be absolute")
    return receipt_path, run_id, project, command_sha


def _junit_outcomes(junit_paths: list[Path]) -> dict[str, int]:
    """Aggregate the final coverage groups' real JUnit outcomes once."""
    totals = {"passed": 0, "failed": 0, "skipped": 0, "total": 0, "collection_errors": 0}
    if not junit_paths:
        raise RuntimeError("Stage-01 receipt requested but no final coverage JUnit reports were declared")
    for path in junit_paths:
        if path.is_symlink() or not path.is_file():
            raise RuntimeError(f"Stage-01 coverage group did not write JUnit evidence: {path}")
        if path.stat().st_size > _MAX_JUNIT_BYTES:
            raise RuntimeError(f"Stage-01 JUnit evidence exceeds {_MAX_JUNIT_BYTES} bytes: {path}")
        try:
            root = ET.parse(path).getroot()
        except (OSError, ET.ParseError) as exc:
            raise RuntimeError(f"cannot parse Stage-01 JUnit evidence {path}: {exc}") from exc
        suites = [root] if root.tag.rsplit("}", 1)[-1] == "testsuite" else list(root.findall("./testsuite"))
        if not suites:
            raise RuntimeError(f"Stage-01 JUnit evidence has no testsuite counts: {path}")
        for suite in suites:
            try:
                tests = int(suite.attrib.get("tests", "0"))
                failures = int(suite.attrib.get("failures", "0"))
                errors = int(suite.attrib.get("errors", "0"))
                skipped = int(suite.attrib.get("skipped", "0"))
            except ValueError as exc:
                raise RuntimeError(f"invalid count in Stage-01 JUnit evidence {path}") from exc
            passed = tests - failures - errors - skipped
            if min(tests, failures, errors, skipped, passed) < 0:
                raise RuntimeError(f"inconsistent count in Stage-01 JUnit evidence {path}")
            totals["passed"] += passed
            totals["failed"] += failures
            totals["skipped"] += skipped
            totals["total"] += tests
            totals["collection_errors"] += errors
    return totals


def _pytest_evidence(evidence_paths: list[Path]) -> tuple[int, int]:
    """Return aggregate warning and discovery counts from pytest sidecars."""
    if not evidence_paths:
        raise RuntimeError("Stage-01 receipt requested but no pytest evidence sidecars were declared")
    warnings = 0
    discovery_count = 0
    for path in evidence_paths:
        if path.is_symlink() or not path.is_file():
            raise RuntimeError(f"Stage-01 coverage group did not write pytest evidence: {path}")
        if path.stat().st_size > _MAX_PYTEST_EVIDENCE_BYTES:
            raise RuntimeError(f"Stage-01 pytest evidence exceeds {_MAX_PYTEST_EVIDENCE_BYTES} bytes: {path}")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"cannot parse Stage-01 pytest evidence {path}: {exc}") from exc
        if not isinstance(payload, dict) or payload.get("schema_version") != _PYTEST_EVIDENCE_SCHEMA:
            raise RuntimeError(f"Stage-01 pytest evidence has the wrong schema: {path}")
        for key in ("warnings", "discovery_count"):
            value = payload.get(key)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise RuntimeError(f"Stage-01 pytest evidence field {key} is invalid: {path}")
        warnings += payload["warnings"]
        discovery_count += payload["discovery_count"]
    return warnings, discovery_count


def _write_project_test_receipt(
    project_root: Path,
    context: tuple[Path, str, str, str],
    junit_paths: list[Path],
    evidence_paths: list[Path],
) -> None:
    """Write a nonce-bound receipt for the generic Stage-01 adapter."""
    receipt_path, run_id, project, command_sha = context
    outcomes = _junit_outcomes(junit_paths)
    warnings, discovery_count = _pytest_evidence(evidence_paths)
    if outcomes["total"] <= 0:
        raise RuntimeError("Stage-01 verifier refuses to receipt a zero-test run")
    if discovery_count < outcomes["total"]:
        raise RuntimeError("Stage-01 pytest discovery count is smaller than its JUnit outcome count")
    coverage = Coverage(
        data_file=str(project_root / ".coverage"),
        config_file=str(project_root / "pyproject.toml"),
    )
    coverage.load()
    coverage_percent = float(coverage.report(file=io.StringIO(), ignore_errors=False))
    payload = {
        "schema_version": _PROJECT_TEST_RECEIPT_SCHEMA,
        "project": project,
        "run_id": run_id,
        "command_sha256": command_sha,
        "coverage_percent": coverage_percent,
        "results": {
            **outcomes,
            "discovery_count": discovery_count,
            "warnings": warnings,
        },
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = receipt_path.with_name(f".{receipt_path.name}.tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, receipt_path)


def _run(
    project_root: Path,
    cmd: list[str],
    label: str,
    *,
    env: dict[str, str] | None = None,
    process_runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
    clock: Callable[[], float] = time.perf_counter,
) -> None:
    print(f"\n==> {label}")
    print(f"    $ {' '.join(shlex.quote(part) for part in cmd)}")
    start = clock()
    process_env = os.environ.copy()
    process_env.setdefault("MPLBACKEND", "Agg")
    process_env.setdefault("PYTHONUNBUFFERED", "1")
    process_env.setdefault("TEMPLATE_ACTIVE_INFERENCE_FIXED_POINT_PASSES", "2")
    if env:
        process_env.update(env)
    # Receipt authority belongs only to this top-level verifier process. If
    # inherited by nested pytest, tests that exercise ``run_verification``
    # would recursively enter receipt mode and demand JUnit sidecars from their
    # in-memory command runners. Producers and tests need none of these values.
    for receipt_key in (
        _PROJECT_TEST_RECEIPT_ENV,
        _PROJECT_TEST_RUN_ID_ENV,
        _PROJECT_TEST_PROJECT_ENV,
        _PROJECT_TEST_COMMAND_SHA_ENV,
    ):
        process_env.pop(receipt_key, None)
    if process_runner is not None:
        result = process_runner(
            cmd,
            cwd=project_root,
            env=process_env,
            text=True,
            check=False,
        )
        returncode = result.returncode
        detail = ""
    else:
        bounded = run_bounded_subprocess(
            cmd,
            cwd=project_root,
            env=build_bounded_env(process_env),
            timeout=_command_timeout_seconds(label),
            capture_output=True,
        )
        returncode = bounded.returncode
        detail = _bounded_failure_detail(
            command_error=bounded.command_error,
            stdout=bounded.stdout,
            stderr=bounded.stderr,
        )
    elapsed = clock() - start
    print(f"    status: {returncode}  elapsed: {elapsed:.1f}s")
    if returncode != 0:
        suffix = f":\n{detail}" if detail else ""
        raise RuntimeError(f"{label} failed with return code {returncode}{suffix}")


def _run_chunked_coverage(
    project_root: Path,
    coverage_groups: list[tuple[str, list[str]]],
    *,
    profile: VerificationProfile | None,
    receipt_context: tuple[Path, str, str, str] | None,
    command_runner: Callable[..., None],
) -> tuple[list[Path], list[Path]]:
    """Run one fresh then append-only coverage subprocess per test group."""
    junit_paths: list[Path] = []
    evidence_paths: list[Path] = []
    for index, (label, selectors) in enumerate(coverage_groups):
        junit_path = receipt_context[0].parent / f"coverage-{index:02d}.xml" if receipt_context else None
        evidence_path = receipt_context[0].parent / f"coverage-{index:02d}-evidence.json" if receipt_context else None
        if junit_path is not None:
            junit_paths.append(junit_path)
        if evidence_path is not None:
            evidence_paths.append(evidence_path)
        command_runner(
            project_root,
            _coverage_command(
                selectors,
                append=index > 0,
                final=index == len(coverage_groups) - 1,
                profile=profile,
                junit_path=junit_path,
                evidence_path=evidence_path,
            ),
            f"Coverage pass: {label}",
        )
    return junit_paths, evidence_paths


def run_coverage_only(
    project_root: Path,
    *,
    profile: VerificationProfile,
    command_runner: Callable[..., None] = _run,
) -> None:
    """Run canonical coverage groups without verifier-owned producer phases."""
    coverage_groups = _validated_coverage_test_groups(project_root)
    _run_chunked_coverage(
        project_root,
        coverage_groups,
        profile=profile,
        receipt_context=None,
        command_runner=command_runner,
    )


def run_verification(
    project_root: Path,
    *,
    skip_chunks: bool = False,
    monolithic_coverage: bool = False,
    profile: VerificationProfile | None = None,
    command_runner: Callable[..., None] = _run,
) -> None:
    """Run verification, optionally applying a typed pytest profile."""
    refresh_cache = _RefreshCache()
    receipt_context = _project_test_receipt_context()
    junit_paths: list[Path] = []
    evidence_paths: list[Path] = []
    profile_args = _profile_marker_args(profile)
    preflight = [
        ("Compose manuscript sections", ["uv", "run", "python", "scripts/compose_manuscript.py"]),
        (
            "Validate compose contracts",
            ["uv", "run", "python", "scripts/compose_manuscript.py", "--validate-only", "--strict"],
        ),
        ("Run analytical sweep", ["uv", "run", "python", "scripts/run_analytical_sweep.py"]),
        ("Simulate SI T-maze", ["uv", "run", "python", "scripts/simulate_si_tmaze.py"]),
        ("Simulate SI graph-world", ["uv", "run", "python", "scripts/simulate_si_graph_world.py"]),
        ("Compute analysis statistics", ["uv", "run", "python", "scripts/compute_statistics.py"]),
        ("Render registered figures", ["uv", "run", "python", "scripts/generate_figures.py"]),
        ("Render belief animation", ["uv", "run", "python", "scripts/render_animation.py"]),
        ("Generate validation spine", ["uv", "run", "python", "scripts/generate_validation_spine.py"]),
        ("Generate toy sweep tracks", ["uv", "run", "python", "scripts/generate_toy_sweep_tracks.py"]),
        ("Generate formal interop tracks", ["uv", "run", "python", "scripts/generate_formal_interop_tracks.py"]),
        ("Generate integration audit", ["uv", "run", "python", "scripts/generate_integration_audit.py"]),
        ("Generate canonical sheaf tracks", ["uv", "run", "python", "scripts/generate_sheaf_tracks.py"]),
        ("Generate manuscript variables", ["uv", "run", "python", "scripts/z_generate_manuscript_variables.py"]),
        ("Settle post-figure fixed point", ["uv", "run", "python", "scripts/z_generate_manuscript_variables.py"]),
        ("Final compose before output gate", ["uv", "run", "python", "scripts/compose_manuscript.py"]),
        ("Settle post-compose fixed point", ["uv", "run", "python", "scripts/z_generate_manuscript_variables.py"]),
        ("Settled final compose before output gate", ["uv", "run", "python", "scripts/compose_manuscript.py"]),
        ("Validate generated outputs", ["uv", "run", "python", "scripts/validate_outputs.py"]),
        ("Check documentation contract", ["uv", "run", "python", "scripts/check_documentation_contract.py", "--check"]),
        ("Generate method inventory", ["uv", "run", "python", "scripts/generate_method_inventory.py"]),
        ("Check method inventory", ["uv", "run", "python", "scripts/generate_method_inventory.py", "--check"]),
    ]
    for label, cmd in preflight:
        refresh_cache.run(project_root, cmd, label, command_runner)

    if not skip_chunks:
        for label, modules in _chunked_test_groups(project_root):
            command_runner(project_root, ["uv", "run", "pytest", *modules, *profile_args, "-q"], label)

    postflight = [
        ("Pre-coverage compose refresh", ["uv", "run", "python", "scripts/compose_manuscript.py"]),
        ("Pre-coverage fixed-point refresh", ["uv", "run", "python", "scripts/z_generate_manuscript_variables.py"]),
        ("Pre-coverage figure refresh", ["uv", "run", "python", "scripts/generate_figures.py"]),
        (
            "Pre-coverage post-figure fixed-point refresh",
            ["uv", "run", "python", "scripts/z_generate_manuscript_variables.py"],
        ),
        ("Pre-coverage final compose refresh", ["uv", "run", "python", "scripts/compose_manuscript.py"]),
        (
            "Pre-coverage post-compose fixed-point refresh",
            ["uv", "run", "python", "scripts/z_generate_manuscript_variables.py"],
        ),
        ("Pre-coverage settled final compose refresh", ["uv", "run", "python", "scripts/compose_manuscript.py"]),
        ("Pre-coverage output gate", ["uv", "run", "python", "scripts/validate_outputs.py"]),
        (
            "Pre-coverage documentation gate",
            ["uv", "run", "python", "scripts/check_documentation_contract.py", "--check"],
        ),
        (
            "Pre-coverage method inventory gate",
            ["uv", "run", "python", "scripts/generate_method_inventory.py", "--check"],
        ),
    ]
    for label, cmd in postflight:
        refresh_cache.run(project_root, cmd, label, command_runner)

    if monolithic_coverage:
        junit_path = receipt_context[0].parent / "coverage-monolithic.xml" if receipt_context else None
        evidence_path = receipt_context[0].parent / "coverage-monolithic-evidence.json" if receipt_context else None
        if junit_path is not None:
            junit_paths.append(junit_path)
        if evidence_path is not None:
            evidence_paths.append(evidence_path)
        monolithic_command = [
            sys.executable,
            "-m",
            "pytest",
            "tests/",
            "--cov=src",
            *profile_args,
            "--cov-fail-under=90",
            "--durations=20",
            "-q",
            "--maxfail=1",
        ]
        if junit_path is not None:
            monolithic_command.append(f"--junitxml={junit_path}")
        if evidence_path is not None:
            monolithic_command.append(f"--template-test-evidence={evidence_path}")
        refresh_cache.run(
            project_root,
            monolithic_command,
            "Full suite coverage pass",
            command_runner,
        )
    else:
        coverage_groups = _validated_coverage_test_groups(project_root)
        coverage_junit_paths, coverage_evidence_paths = _run_chunked_coverage(
            project_root,
            coverage_groups,
            profile=profile,
            receipt_context=receipt_context,
            command_runner=lambda root, command, label: refresh_cache.run(
                root,
                command,
                label,
                command_runner,
            ),
        )
        junit_paths.extend(coverage_junit_paths)
        evidence_paths.extend(coverage_evidence_paths)

    final_refresh = [
        ("Post-coverage compose refresh", ["uv", "run", "python", "scripts/compose_manuscript.py"]),
        ("Post-coverage fixed-point refresh", ["uv", "run", "python", "scripts/z_generate_manuscript_variables.py"]),
        ("Post-coverage figure refresh", ["uv", "run", "python", "scripts/generate_figures.py"]),
        (
            "Post-coverage post-figure fixed-point refresh",
            ["uv", "run", "python", "scripts/z_generate_manuscript_variables.py"],
        ),
        ("Post-coverage final compose refresh", ["uv", "run", "python", "scripts/compose_manuscript.py"]),
        (
            "Post-coverage post-compose fixed-point refresh",
            ["uv", "run", "python", "scripts/z_generate_manuscript_variables.py"],
        ),
        ("Post-coverage settled final compose refresh", ["uv", "run", "python", "scripts/compose_manuscript.py"]),
        ("Post-coverage output gate", ["uv", "run", "python", "scripts/validate_outputs.py"]),
        (
            "Post-coverage documentation gate",
            ["uv", "run", "python", "scripts/check_documentation_contract.py", "--check"],
        ),
        (
            "Post-coverage method inventory gate",
            ["uv", "run", "python", "scripts/generate_method_inventory.py", "--check"],
        ),
    ]
    for label, cmd in final_refresh:
        refresh_cache.run(project_root, cmd, label, command_runner)
    if receipt_context is not None:
        _write_project_test_receipt(project_root, receipt_context, junit_paths, evidence_paths)
