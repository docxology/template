"""Benchmark grading for AutoResearch method-contract artifacts."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from infrastructure.autoresearch import BenchmarkTask

from src.artifact_content import is_substantive_artifact
from src.config import AutoResearchLoopConfig

# Core artifacts the loop must have emitted (and filled with real content) by the
# time method-contract benchmark grading runs (after write_core_loop_artifacts,
# write_ml_task_artifacts, and finalize_loop_payloads; before research_program.json).
# Used to grade an otherwise-absent benchmark from REAL evidence instead of
# asserting success by fiat.
_BENCHMARK_CORE_ARTIFACTS: tuple[str, ...] = (
    "output/data/autoresearch_loop.json",
    "output/data/autoresearch_plan.json",
    "output/data/autoresearch_claims.json",
    "output/data/autoresearch_stage_matrix.csv",
    "output/data/ml_task_results.json",
)

# Minimum accuracy improvement over the baseline for the ML loop to count as a
# real result, guarding against an epsilon delta (e.g. 0.0001) scoring the
# benchmark as ready. This is the DEFAULT; it is overridable via the optional
# `grading:` block in autoresearch.yaml (see _load_grading_settings).
_MIN_MEANINGFUL_ACCURACY_DELTA = 0.005


@dataclass(frozen=True)
class _GradingSettings:
    """Config-driven knobs for the readiness benchmark grade."""

    min_accuracy_delta: float = _MIN_MEANINGFUL_ACCURACY_DELTA
    core_artifacts: tuple[str, ...] = _BENCHMARK_CORE_ARTIFACTS
    metric_direction: str = "maximize"


def _load_grading_settings(project_root: Path) -> _GradingSettings:
    """Load benchmark-grading knobs from autoresearch.yaml with loud rejection.

    Absent `grading:` block → defaults (current behavior). A typo'd key keeps its
    default; an out-of-range or wrong-typed value raises ValueError rather than
    silently degrading the gate. `metric_direction` (previously a dead top-level
    knob) is now consumed here.
    """
    path = project_root / "autoresearch.yaml"
    data: dict[str, Any] = {}
    if path.is_file():
        try:
            loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise ValueError(f"autoresearch.yaml is not valid YAML: {exc}") from exc
        data = loaded if isinstance(loaded, dict) else {}
    grading = data.get("grading", {}) or {}
    if not isinstance(grading, dict):
        raise ValueError("autoresearch.yaml `grading` must be a mapping")
    unknown = set(grading) - {"min_accuracy_delta", "core_artifacts"}
    if unknown:
        # Loud rejection of a typo'd/unsupported key — a silently-ignored knob is a
        # dead knob (configurability requires a consumed-role inventory, not just
        # accepting whatever is present).
        raise ValueError(f"unsupported grading key(s): {', '.join(sorted(str(key) for key in unknown))}")
    min_delta = grading.get("min_accuracy_delta", _MIN_MEANINGFUL_ACCURACY_DELTA)
    if (
        isinstance(min_delta, bool)
        or not isinstance(min_delta, (int, float))
        or not math.isfinite(min_delta)
        or min_delta < 0
    ):
        raise ValueError("grading.min_accuracy_delta must be a finite, non-negative number")
    core = grading.get("core_artifacts", _BENCHMARK_CORE_ARTIFACTS)
    if not isinstance(core, (list, tuple)) or not core or not all(isinstance(c, str) and c.strip() for c in core):
        raise ValueError("grading.core_artifacts must be a non-empty list of path strings")
    direction = str(data.get("metric_direction", "maximize"))
    if direction not in ("maximize", "minimize"):
        raise ValueError("autoresearch.yaml metric_direction must be 'maximize' or 'minimize'")
    return _GradingSettings(min_accuracy_delta=float(min_delta), core_artifacts=tuple(core), metric_direction=direction)


def _has_supported_claim(project_root: Path) -> bool:
    """True iff >=1 claim is supported AND its cited evidence is itself substantive.

    Guards two ways: the original goalpost-move (a non-empty claims list with every
    claim ``supported: false``) AND a self-asserted ``supported: true`` flag whose
    cited ``evidence_path`` points at missing or hollow content. Support must be
    backed by real evidence on disk, not merely declared.
    """
    path = project_root / "output" / "data" / "autoresearch_claims.json"
    if not is_substantive_artifact(path):
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    claims = payload if isinstance(payload, list) else []
    for claim in claims:
        if not isinstance(claim, dict) or not claim.get("supported"):
            continue
        evidence_path = claim.get("evidence_path")
        if isinstance(evidence_path, str) and evidence_path and is_substantive_artifact(project_root / evidence_path):
            return True
    return False


def _ml_accuracy_improved(project_root: Path, settings: _GradingSettings) -> bool:
    """True iff the ML task records a finite, meaningful improvement over baseline.

    Honors the configured metric_direction: for ``maximize`` the delta must be
    >= the threshold; for ``minimize`` it must be <= -threshold.
    """
    path = project_root / "output" / "data" / "ml_task_results.json"
    if not is_substantive_artifact(path):
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    delta = payload.get("accuracy_delta") if isinstance(payload, dict) else None
    if not isinstance(delta, (int, float)) or isinstance(delta, bool) or not math.isfinite(delta):
        return False
    if settings.metric_direction == "minimize":
        return delta <= -settings.min_accuracy_delta
    return delta >= settings.min_accuracy_delta


def _benchmark_readiness_checks(project_root: Path, settings: _GradingSettings) -> list[tuple[str, bool]]:
    """Measured readiness checks: artifact substance PLUS real outcomes."""
    checks: list[tuple[str, bool]] = [
        (f"substantive:{rel}", is_substantive_artifact(project_root / rel)) for rel in settings.core_artifacts
    ]
    checks.append(("at_least_one_supported_claim", _has_supported_claim(project_root)))
    checks.append(("ml_accuracy_improved_over_baseline", _ml_accuracy_improved(project_root, settings)))
    return checks


def _grade_absent_benchmark(
    project_root: Path, task: BenchmarkTask, settings: _GradingSettings | None = None
) -> dict[str, object]:
    """Grade a benchmark whose grading file is absent, from measured evidence.

    Replaces the prior fail-open (which wrote ``score: 1.0`` with a fiat string
    asserting "all artifacts were emitted"). The score is the fraction of measured
    readiness checks that pass: each core artifact must be substantive, the claims
    ledger must record at least one supported claim, and the ML task must show a
    real accuracy improvement over the baseline. A hollow or degraded run — empty
    artifacts, unsupported claims, or no ML improvement — scores below 1.0 and is
    flagged ``incomplete`` rather than silently certified.

    Note: this is an artifact-readiness + real-outcome grade, not a research-quality
    metric; on a healthy completed run it is 1.0, and it is falsifiable when the
    underlying evidence is missing, hollow, or records no improvement.
    """
    settings = settings or _load_grading_settings(project_root)
    checks = _benchmark_readiness_checks(project_root, settings)
    passed = [name for name, ok in checks if ok]
    failed = [name for name, ok in checks if not ok]
    score = round(len(passed) / len(checks), 3) if checks else 0.0
    return {
        "id": task.identifier,
        "description": task.description,
        "score": score,
        "status": "graded" if score >= 1.0 else "incomplete",
        "evidence": (
            f"{len(passed)}/{len(checks)} readiness checks passed: core artifacts substantive, "
            ">=1 supported claim, ML accuracy improved over baseline."
        ),
        "failed_checks": failed,
        "checks": [name for name, _ in checks],
        # Effective config captured in the audit trail so a lowered bar is visible.
        "effective_min_accuracy_delta": settings.min_accuracy_delta,
        "effective_metric_direction": settings.metric_direction,
    }


def _is_auto_grade(path: Path) -> bool:
    """True iff this grading file was produced by ``_grade_absent_benchmark`` itself.

    Auto-grades carry the ``checks``/``failed_checks`` keys; a dedicated grade
    (e.g. the real ML benchmark written by ``write_ml_task_artifacts``) or a
    human-authored grade does not.
    """
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return isinstance(payload, dict) and "checks" in payload and "failed_checks" in payload


def _write_benchmark_grading_reports(project_root: Path, config: AutoResearchLoopConfig) -> list[Path]:
    # Preserve a dedicated/human grade (e.g. the real ML benchmark already written
    # this run), but always refresh our own auto-grade so a stale score cannot
    # survive a degraded rerun. A missing file is graded fresh.
    from .io import write_json

    settings = _load_grading_settings(project_root)
    paths: list[Path] = []
    for task in config.benchmark_tasks:
        path = project_root / task.grading_output
        if path.exists() and not _is_auto_grade(path):
            paths.append(path)
            continue
        paths.append(write_json(path, _grade_absent_benchmark(project_root, task, settings)))
    return paths


def _benchmark_score(path: Path) -> float | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    score = payload.get("score")
    return float(score) if isinstance(score, int | float) else None
