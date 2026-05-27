"""Artifact writers for the AutoResearch loop."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from infrastructure.autoresearch import BenchmarkTask, ResearchProgram, RunLedger
from infrastructure.core.pipeline.artifacts import ArtifactManifest, ArtifactManifestEntry, compute_sha256

from .artifact_content import is_substantive_artifact
from .artifact_schemas import schema_manifest_payload
from .config import AutoResearchLoopConfig, load_experiment_candidates, load_seed_ideas
from .figure_registry import figure_registry_payload
from .figure_style import apply_style, load_figure_style
from .figures import (
    write_ml_bootstrap_intervals_figure,
    write_ml_calibration_reliability_figure,
    write_ml_candidate_rank_stability_figure,
    write_candidate_lifecycle_figure,
    write_closure_flow_figure,
    write_mnist_class_balance_figure,
    write_mnist_error_examples_figure,
    write_ml_candidate_scores_figure,
    write_ml_classification_metrics_heatmap,
    write_ml_complexity_accuracy_figure,
    write_ml_confusion_matrix_figure,
    write_ml_confusion_pairs_figure,
    write_ml_generalization_gap_figure,
    write_ml_learning_curve_figure,
    write_ml_paired_correctness_figure,
    write_ml_per_class_accuracy_figure,
    write_ml_probability_quality_figure,
    write_ml_probability_margin_figure,
    write_ml_robustness_matrix_figure,
    write_ml_selective_accuracy_figure,
    write_ml_training_dynamics_figure,
    write_mnist_subset_contact_sheet_figure,
    write_stage_matrix_figure,
)
from .figure_quality import write_figure_quality_report
from .diagnostics import (
    diagnostic_bundle,
)
from .manuscript_variables import (
    compute_variables_from_payload,
    save_variables,
)
from .ml_task import MLTaskResult, write_confusion_matrix_csv, write_error_examples_json, write_training_history_csv
from .models import AutoResearchLoopResult, LoopStageResult
from .phase_ledger import write_phase_ledger
from .research_object import research_object_manifest_payload
from .reports import (
    build_review_packet,
    render_ml_experiment_report,
    render_loop_markdown,
    render_review_packet_markdown,
    render_stage_matrix_csv,
    render_summary_markdown,
)

_ALWAYS_MANIFEST_EXCLUSIONS = frozenset(
    {
        "output/figures/autoresearch_stage_matrix.png",
        "output/figures/figure_registry.json",
        "output/reports/autoresearch_loop.md",
        "output/reports/autoresearch_readiness.json",
        "output/reports/autoresearch_readiness.md",
        "output/reports/evidence_registry.json",
    }
)
_VOLATILE_LOOP_STATE_ARTIFACTS = frozenset(
    {
        "output/data/autoresearch_loop.json",
        "output/data/autoresearch_review_packet.json",
        "output/data/manuscript_variables.json",
        "output/figures/autoresearch_stage_matrix.png",
        "output/reports/autoresearch_loop.json",
        "output/reports/autoresearch_loop.md",
        "output/reports/autoresearch_review_packet.md",
        "output/reports/autoresearch_summary.md",
    }
)


def write_json(path: Path, payload: object) -> Path:
    """Write JSON payload to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_text(path: Path, text: str) -> Path:
    """Write text payload to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def relative_path(project_root: Path, path: Path) -> str:
    """Return a project-relative path string when possible."""
    try:
        return str(path.relative_to(project_root))
    except ValueError:
        return str(path)


def write_artifact_manifest(
    project_root: Path,
    paths: list[Path],
    *,
    exclude_volatile: bool = False,
) -> Path:
    """Write the artifact manifest for declared loop outputs."""
    manifest_path = (project_root / "output" / "reports" / "artifact_manifest.json").resolve()
    entries = []
    for index, path in enumerate(
        sorted(
            {
                path.resolve()
                for path in paths
                if path.exists()
                and path.resolve() != manifest_path
                and relative_path(project_root, path) not in _ALWAYS_MANIFEST_EXCLUSIONS
                and (not exclude_volatile or relative_path(project_root, path) not in _VOLATILE_LOOP_STATE_ARTIFACTS)
            }
        ),
        start=1,
    ):
        entries.append(
            ArtifactManifestEntry(
                path=relative_path(project_root, path),
                size_bytes=path.stat().st_size,
                sha256=compute_sha256(path),
                stage_num=index,
                stage_name="AutoResearch loop",
                contract_match=True,
            )
        )
    manifest = ArtifactManifest(entries=tuple(entries), issues=())
    return write_json(manifest_path, manifest.to_dict())


def write_core_loop_artifacts(
    project_root: Path,
    plan_payload: dict[str, Any],
    config: AutoResearchLoopConfig,
    stage_results: tuple[LoopStageResult, ...],
    generated_at: str,
    project_name: str,
) -> list[Path]:
    """Write plan, loop markdown, figure, and stage matrix before readiness is known."""
    output = project_root / "output"
    data_dir = output / "data"
    reports_dir = output / "reports"
    figures_dir = output / "figures"
    for directory in (data_dir, reports_dir, figures_dir):
        directory.mkdir(parents=True, exist_ok=True)

    provisional = AutoResearchLoopResult(
        project_name=project_name,
        generated_at=generated_at,
        config=config,
        stage_results=stage_results,
        claims=(),
        readiness_valid=False,
        output_paths=(),
    )
    style = load_figure_style(project_root)
    with apply_style(style):
        figure_path = write_stage_matrix_figure(figures_dir, provisional)
    return [
        write_json(data_dir / "autoresearch_plan.json", plan_payload),
        write_text(reports_dir / "autoresearch_loop.md", render_loop_markdown(provisional)),
        write_text(data_dir / "autoresearch_stage_matrix.csv", render_stage_matrix_csv(provisional)),
        figure_path,
        write_json(figures_dir / "figure_registry.json", figure_registry_payload(provisional)),
    ]


def write_method_contract_artifacts(
    project_root: Path,
    config: AutoResearchLoopConfig,
    *,
    generated_at: str,
    ml_result: MLTaskResult | None = None,
) -> list[Path]:
    """Write bounded-loop method artifacts used by readiness validation."""
    output = project_root / "output"
    data_dir = output / "data"
    reports_dir = output / "reports"
    data_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    program = ResearchProgram(
        path="program.md",
        summary=_program_summary(project_root),
        autonomy_level=config.autonomy_level,
        budget_policy=config.budget_policy,
        edit_allowlist=config.edit_allowlist,
    )
    ideas = load_seed_ideas(project_root)
    candidates = load_experiment_candidates(project_root)
    iterations_used = (
        ml_result.evaluated_candidate_count if ml_result is not None else config.budget_policy.max_iterations
    )
    budget_exhausted = bool(ml_result.budget_exhausted) if ml_result is not None else True
    run_ledger = RunLedger(
        budget_policy=config.budget_policy,
        iterations_used=iterations_used,
        wall_clock_minutes_used=0,
        llm_calls_used=0,
        cost_usd_used=0.0,
        budget_exhausted=budget_exhausted,
        exhaustion_reason="candidate iteration budget reached"
        if budget_exhausted
        else "candidate loop completed within budget",
    )
    review_decisions = {
        "schema": "template-autoresearch-review-decisions-v1",
        "generated_at": generated_at,
        "publication_approved": config.human_review.publication_approved,
        "human_review_source": config.human_review.source_path,
        "human_review_source_exists": config.human_review.source_exists,
        "decisions": [
            {
                "gate": gate.name,
                "required": gate.required,
                "decision": config.human_review.decisions.get(gate.name, "deferred"),
                "rationale": "Decision is read from human_review.yaml when present; generated readiness is not approval.",
            }
            for gate in config.review_gates
        ],
    }
    benchmark_report_paths = _write_benchmark_grading_reports(project_root, config)
    benchmark_scores = {
        "generated_at": generated_at,
        "tasks": [
            {
                "id": task.identifier,
                "description": task.description,
                "grading_output_path": task.grading_output,
                "status": "graded" if (project_root / task.grading_output).exists() else "missing",
                "score": _benchmark_score(project_root / task.grading_output),
            }
            for task in config.benchmark_tasks
        ],
        "task_count": len(config.benchmark_tasks),
    }

    paths = [
        write_json(data_dir / "research_program.json", program.to_dict()),
        write_json(
            data_dir / "idea_ledger.json",
            {
                "generated_at": generated_at,
                "ideas": [idea.to_dict() for idea in ideas],
                "candidates": [candidate.to_dict() for candidate in candidates],
            },
        ),
        write_json(data_dir / "run_ledger.json", run_ledger.to_dict()),
        write_json(data_dir / "review_decisions.json", review_decisions),
        write_json(data_dir / "benchmark_scores.json", benchmark_scores),
    ]
    paths.extend(benchmark_report_paths)
    return paths


def write_ml_task_artifacts(project_root: Path, result: MLTaskResult, *, generated_at: str) -> list[Path]:
    """Write deterministic ML task artifacts."""
    output = project_root / "output"
    data_dir = output / "data"
    reports_dir = output / "reports"
    figures_dir = output / "figures"
    for directory in (data_dir, reports_dir, figures_dir):
        directory.mkdir(parents=True, exist_ok=True)

    candidate_ledger = {
        "generated_at": generated_at,
        "objective": {
            "metric": result.task_config.metric_name,
            "direction": result.task_config.metric_direction,
        },
        "budget": {
            "candidate_count": result.candidate_count,
            "evaluated_candidate_count": result.evaluated_candidate_count,
            "budget_exhausted": result.budget_exhausted,
            "llm_calls_used": result.llm_calls_used,
            "cost_usd_used": result.cost_usd_used,
        },
        "baseline": result.baseline.to_dict(),
        "accepted_candidate_id": result.accepted_candidate_id,
        "candidates": [candidate.to_dict() for candidate in result.candidates],
    }
    benchmark_score = {
        "id": "ml-loop-score",
        "description": "Grade bounded ML-loop metric improvement, budget compliance, and offline execution.",
        "score": result.benchmark_score,
        "status": "graded",
        "evidence": {
            "results": "output/data/ml_task_results.json",
            "candidate_ledger": "output/data/ml_candidate_ledger.json",
            "accepted_candidate_id": result.accepted_candidate_id,
            "accuracy_delta": round(result.accuracy_delta, 6),
        },
    }
    diagnostics = diagnostic_bundle(project_root, result)
    classification_payload = diagnostics["classification_diagnostics"]
    calibration_payload = diagnostics["calibration_report"]
    calibration_intervals_payload = diagnostics["calibration_bin_intervals"]
    robustness_payload = diagnostics["robustness_report"]
    probability_payload = diagnostics["probability_diagnostics"]
    bootstrap_payload = diagnostics["bootstrap_intervals"]
    paired_payload = diagnostics["paired_comparison"]
    statistical_payload = diagnostics["statistical_summary"]
    training_payload = diagnostics["training_diagnostics"]
    candidate_intervals_payload = diagnostics["candidate_intervals"]
    class_balance_payload = diagnostics["class_balance"]
    rank_stability_payload = diagnostics["candidate_rank_stability"]
    selection_payload = diagnostics["candidate_selection_audit"]
    boundary_payload = diagnostics["diagnostic_boundary"]
    registry_payload = figure_registry_payload(ml_result=result)

    style = load_figure_style(project_root)
    with apply_style(style):
        artifacts = [
            write_json(data_dir / "figure_style.json", {"generated_at": generated_at, **style.to_dict()}),
            write_json(data_dir / "mnist_task_config.json", result.task_config.to_dict()),
            write_json(data_dir / "ml_task_results.json", result.to_dict()),
            write_json(data_dir / "ml_candidate_ledger.json", candidate_ledger),
            write_confusion_matrix_csv(
                data_dir / "ml_confusion_matrix.csv", result.accepted_candidate.confusion_matrix
            ),
            write_training_history_csv(data_dir / "ml_training_history.csv", result),
            write_error_examples_json(data_dir / "ml_error_examples.json", project_root, result),
            write_json(data_dir / "ml_prediction_records.json", diagnostics["prediction_records"]),
            write_json(data_dir / "ml_classification_diagnostics.json", classification_payload),
            write_json(data_dir / "ml_candidate_intervals.json", candidate_intervals_payload),
            write_json(data_dir / "ml_class_balance.json", class_balance_payload),
            write_json(data_dir / "ml_calibration_report.json", calibration_payload),
            write_json(data_dir / "ml_calibration_bin_intervals.json", calibration_intervals_payload),
            write_json(data_dir / "ml_robustness_report.json", robustness_payload),
            write_json(data_dir / "ml_probability_diagnostics.json", probability_payload),
            write_json(data_dir / "ml_bootstrap_intervals.json", bootstrap_payload),
            write_json(data_dir / "ml_paired_comparison.json", paired_payload),
            write_json(data_dir / "ml_statistical_summary.json", statistical_payload),
            write_json(data_dir / "ml_training_diagnostics.json", training_payload),
            write_json(data_dir / "ml_candidate_rank_stability.json", rank_stability_payload),
            write_json(data_dir / "ml_candidate_selection_audit.json", selection_payload),
            write_json(data_dir / "ml_diagnostic_boundary.json", boundary_payload),
            write_text(reports_dir / "ml_experiment_report.md", render_ml_experiment_report(result)),
            write_json(reports_dir / "ml_benchmark_score.json", benchmark_score),
            write_ml_candidate_scores_figure(figures_dir, result, candidate_intervals_payload),
            write_ml_confusion_matrix_figure(figures_dir, result),
            write_ml_per_class_accuracy_figure(figures_dir, result),
            write_ml_learning_curve_figure(figures_dir, result),
            write_ml_complexity_accuracy_figure(figures_dir, result),
            write_mnist_error_examples_figure(project_root, figures_dir, result),
            write_ml_calibration_reliability_figure(figures_dir, calibration_payload, calibration_intervals_payload),
            write_ml_classification_metrics_heatmap(figures_dir, classification_payload),
            write_ml_confusion_pairs_figure(figures_dir, classification_payload),
            write_ml_generalization_gap_figure(figures_dir, classification_payload),
            write_ml_robustness_matrix_figure(figures_dir, robustness_payload),
            write_ml_probability_margin_figure(figures_dir, probability_payload),
            write_ml_bootstrap_intervals_figure(figures_dir, bootstrap_payload),
            write_ml_paired_correctness_figure(figures_dir, paired_payload),
            write_ml_selective_accuracy_figure(figures_dir, statistical_payload),
            write_ml_probability_quality_figure(figures_dir, statistical_payload),
            write_ml_training_dynamics_figure(figures_dir, training_payload),
            write_ml_candidate_rank_stability_figure(figures_dir, rank_stability_payload),
            write_candidate_lifecycle_figure(figures_dir, result),
            write_mnist_class_balance_figure(figures_dir, class_balance_payload),
            write_mnist_subset_contact_sheet_figure(project_root, figures_dir, result),
            write_json(figures_dir / "figure_registry.json", registry_payload),
            write_figure_quality_report(
                data_dir / "figure_quality_report.json",
                project_root,
                registry_payload,
                generated_at=generated_at,
            ),
        ]
    return artifacts


def write_final_visual_artifacts(
    project_root: Path,
    result: AutoResearchLoopResult,
    ml_result: MLTaskResult,
) -> list[Path]:
    """Regenerate final figures and registry from the current loop state."""
    figures_dir = project_root / "output" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    diagnostics = diagnostic_bundle(project_root, ml_result)
    classification_payload = diagnostics["classification_diagnostics"]
    calibration_payload = diagnostics["calibration_report"]
    calibration_intervals_payload = diagnostics["calibration_bin_intervals"]
    robustness_payload = diagnostics["robustness_report"]
    probability_payload = diagnostics["probability_diagnostics"]
    bootstrap_payload = diagnostics["bootstrap_intervals"]
    paired_payload = diagnostics["paired_comparison"]
    statistical_payload = diagnostics["statistical_summary"]
    training_payload = diagnostics["training_diagnostics"]
    candidate_intervals_payload = diagnostics["candidate_intervals"]
    class_balance_payload = diagnostics["class_balance"]
    rank_stability_payload = diagnostics["candidate_rank_stability"]
    registry_payload = figure_registry_payload(result, ml_result)
    style = load_figure_style(project_root)
    with apply_style(style):
        artifacts = [
            write_json(
                project_root / "output" / "data" / "figure_style.json",
                {"generated_at": result.generated_at, **style.to_dict()},
            ),
            write_stage_matrix_figure(figures_dir, result),
            write_ml_candidate_scores_figure(figures_dir, ml_result, candidate_intervals_payload),
            write_ml_confusion_matrix_figure(figures_dir, ml_result),
            write_ml_per_class_accuracy_figure(figures_dir, ml_result),
            write_ml_learning_curve_figure(figures_dir, ml_result),
            write_ml_complexity_accuracy_figure(figures_dir, ml_result),
            write_mnist_error_examples_figure(project_root, figures_dir, ml_result),
            write_ml_calibration_reliability_figure(figures_dir, calibration_payload, calibration_intervals_payload),
            write_ml_classification_metrics_heatmap(figures_dir, classification_payload),
            write_ml_confusion_pairs_figure(figures_dir, classification_payload),
            write_ml_generalization_gap_figure(figures_dir, classification_payload),
            write_ml_robustness_matrix_figure(figures_dir, robustness_payload),
            write_ml_probability_margin_figure(figures_dir, probability_payload),
            write_ml_bootstrap_intervals_figure(figures_dir, bootstrap_payload),
            write_ml_paired_correctness_figure(figures_dir, paired_payload),
            write_ml_selective_accuracy_figure(figures_dir, statistical_payload),
            write_ml_probability_quality_figure(figures_dir, statistical_payload),
            write_ml_training_dynamics_figure(figures_dir, training_payload),
            write_ml_candidate_rank_stability_figure(figures_dir, rank_stability_payload),
            write_candidate_lifecycle_figure(figures_dir, ml_result),
            write_mnist_class_balance_figure(figures_dir, class_balance_payload),
            write_mnist_subset_contact_sheet_figure(project_root, figures_dir, ml_result),
            write_closure_flow_figure(figures_dir, result),
            write_json(figures_dir / "figure_registry.json", registry_payload),
            write_figure_quality_report(
                project_root / "output" / "data" / "figure_quality_report.json",
                project_root,
                registry_payload,
                generated_at=result.generated_at,
                require_all_registered=True,
            ),
        ]
    return artifacts


def finalize_loop_payloads(
    project_root: Path,
    result: AutoResearchLoopResult,
) -> list[Path]:
    """Write JSON payloads and reports that depend on final readiness and claims."""
    output = project_root / "output"
    data_dir = output / "data"
    reports_dir = output / "reports"
    loop_payload = result.to_dict()
    paths = [
        write_json(data_dir / "autoresearch_loop.json", loop_payload),
        write_json(data_dir / "autoresearch_claims.json", [claim.to_dict() for claim in result.claims]),
        write_json(data_dir / "autoresearch_review_packet.json", build_review_packet(result)),
        write_json(reports_dir / "autoresearch_loop.json", loop_payload),
        write_text(reports_dir / "autoresearch_loop.md", render_loop_markdown(result)),
        write_text(reports_dir / "autoresearch_review_packet.md", render_review_packet_markdown(result)),
        write_text(reports_dir / "autoresearch_summary.md", render_summary_markdown(result)),
    ]
    variables = compute_variables_from_payload(loop_payload)
    paths.append(save_variables(variables, data_dir / "manuscript_variables.json"))
    return paths


def update_result_payloads(project_root: Path, result: AutoResearchLoopResult) -> list[Path]:
    """Refresh loop JSON and review payloads after output paths are finalized."""
    output = project_root / "output"
    data_dir = output / "data"
    reports_dir = output / "reports"
    loop_payload = result.to_dict()
    paths = [
        write_json(data_dir / "autoresearch_loop.json", loop_payload),
        write_json(data_dir / "autoresearch_claims.json", [claim.to_dict() for claim in result.claims]),
        write_json(data_dir / "autoresearch_review_packet.json", build_review_packet(result)),
        write_json(reports_dir / "autoresearch_loop.json", loop_payload),
        write_text(reports_dir / "autoresearch_loop.md", render_loop_markdown(result)),
        write_text(reports_dir / "autoresearch_review_packet.md", render_review_packet_markdown(result)),
        write_text(reports_dir / "autoresearch_summary.md", render_summary_markdown(result)),
    ]
    paths.append(
        save_variables(
            compute_variables_from_payload(loop_payload),
            data_dir / "manuscript_variables.json",
        )
    )
    return paths


def write_schema_manifest(project_root: Path, paths: list[Path], *, generated_at: str) -> Path:
    """Write the schema-version manifest; fail the run if any payload is nonconforming.

    This makes schema conformance a HARD production gate (not just an emitted field):
    a governance payload that carries a contracted schema tag but violates its
    field/type contract aborts the loop loudly rather than being written as green.
    """
    payload = schema_manifest_payload(project_root, paths, generated_at=generated_at)
    if not payload["valid"]:
        nonconforming = payload["nonconforming_schema_artifacts"]
        rows = nonconforming if isinstance(nonconforming, list) else []
        offenders = "; ".join(f"{row.get('path')} ({row.get('violations')})" for row in rows if isinstance(row, dict))
        raise ValueError(f"nonconforming schema artifact(s) — governance gate failed: {offenders}")
    return write_json(
        project_root / "output" / "data" / "autoresearch_schema_manifest.json",
        payload,
    )


def write_research_object_manifest(project_root: Path, paths: list[Path], *, generated_at: str) -> Path:
    """Write the local research-object manifest."""
    return write_json(
        project_root / "output" / "data" / "research_object_manifest.json",
        research_object_manifest_payload(project_root, paths, generated_at=generated_at),
    )


def write_autoresearch_phase_ledger(
    project_root: Path,
    result: AutoResearchLoopResult,
    paths: list[Path],
    *,
    generated_at: str,
    settlement_pass_count: int,
) -> Path:
    """Write the deterministic phase ledger for the loop settlement order."""
    return write_phase_ledger(
        project_root / "output" / "data" / "autoresearch_phase_ledger.json",
        project_root,
        result,
        paths,
        generated_at=generated_at,
        settlement_pass_count=settlement_pass_count,
    )


def write_loop_payloads(
    project_root: Path,
    plan_payload: dict[str, Any],
    config: AutoResearchLoopConfig,
    stage_results: tuple[LoopStageResult, ...],
    result: AutoResearchLoopResult,
) -> list[Path]:
    """Write all loop outputs once using core and finalize phases."""
    core_paths = write_core_loop_artifacts(
        project_root,
        plan_payload,
        config,
        stage_results,
        result.generated_at,
        result.project_name,
    )
    return [*core_paths, *finalize_loop_payloads(project_root, result)]


def _program_summary(project_root: Path) -> str:
    path = project_root / "program.md"
    if not path.exists():
        return "Human-authored research program."
    for paragraph in path.read_text(encoding="utf-8").split("\n\n"):
        text = " ".join(line.strip() for line in paragraph.splitlines() if line.strip() and not line.startswith("#"))
        if text:
            return text
    return "Human-authored research program."


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
