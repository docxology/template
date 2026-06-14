"""Core loop and method-contract artifact writers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from infrastructure.autoresearch import ResearchProgram, RunLedger

from src.figures import figures_process
from src.config import AutoResearchLoopConfig, load_experiment_candidates, load_seed_ideas
from src.figures.figure_registry import figure_registry_payload
from src.figures.figure_style import apply_style, load_figure_style
from src.ml.task import MLTaskResult
from src.models import AutoResearchLoopResult, LoopStageResult
from src.reports import render_loop_markdown, render_stage_matrix_csv

from .benchmark import _benchmark_score, _write_benchmark_grading_reports, write_benchmark_boundary
from .io import write_json, write_text


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
        figure_path = figures_process.write_stage_matrix_figure(figures_dir, provisional)
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
        write_benchmark_boundary(project_root, config, ml_result=ml_result),
    ]
    paths.extend(benchmark_report_paths)
    return paths


def _program_summary(project_root: Path) -> str:
    path = project_root / "program.md"
    if not path.exists():
        return "Human-authored research program."
    for paragraph in path.read_text(encoding="utf-8").split("\n\n"):
        text = " ".join(line.strip() for line in paragraph.splitlines() if line.strip() and not line.startswith("#"))
        if text:
            return text
    return "Human-authored research program."
