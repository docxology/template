"""Contract tests for the public AutoResearch exemplar project."""

from __future__ import annotations

from pathlib import Path

from infrastructure.autoresearch import build_autoresearch_plan
from infrastructure.project.discovery import discover_projects
from infrastructure.project.git_guards import ALLOWED_PROJECT_DIRS
from infrastructure.project.public_scope import public_project_names


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_template_autoresearch_project_is_public_and_discoverable() -> None:
    repo_root = _repo_root()
    project_names = {project.qualified_name for project in discover_projects(repo_root)}

    assert "template_autoresearch_project" in project_names
    assert "template_autoresearch_project" in public_project_names(repo_root)
    assert "projects/template_autoresearch_project/" in ALLOWED_PROJECT_DIRS


def test_template_autoresearch_project_declares_exact_stage_gates() -> None:
    repo_root = _repo_root()
    plan = build_autoresearch_plan(repo_root, "template_autoresearch_project")
    stage_names = {stage.name for stage in plan.stages}

    assert plan.config.strict is True
    assert set(plan.stage_gates) <= stage_names
    assert {"Project Tests", "Project Analysis", "Output Validation"}.issubset(set(plan.stage_gates))
    assert "output/data/autoresearch_loop.json" in plan.required_artifacts


def test_template_autoresearch_project_has_project_docs_contract() -> None:
    project_root = _repo_root() / "projects" / "template_autoresearch_project"
    docs_dir = project_root / "docs"
    required_docs = {
        "README.md",
        "AGENTS.md",
        "configuration.md",
        "outputs.md",
        "runbook.md",
    }

    assert docs_dir.is_dir()
    for filename in required_docs:
        path = docs_dir / filename
        assert path.is_file(), filename
        text = path.read_text(encoding="utf-8")
        assert "template_autoresearch_project" in text
        assert "{{" not in text
        assert "}}" not in text

    readme = (docs_dir / "README.md").read_text(encoding="utf-8")
    assert "./run.sh --pipeline --project template_autoresearch_project" in readme
    outputs = (docs_dir / "outputs.md").read_text(encoding="utf-8")
    assert "output/reports/autoresearch_review_packet.md" in outputs
    assert "output/data/autoresearch_stage_matrix.csv" in outputs
    assert "output/data/research_program.json" in outputs
    assert "output/data/idea_ledger.json" in outputs
    assert "output/data/run_ledger.json" in outputs
    assert "output/data/review_decisions.json" in outputs
    assert "output/data/benchmark_scores.json" in outputs
    assert "output/data/ml_task_results.json" in outputs
    assert "output/data/ml_candidate_ledger.json" in outputs
    assert "output/reports/ml_experiment_report.md" in outputs
    assert "output/reports/ml_benchmark_score.json" in outputs


def test_template_autoresearch_project_declares_program_and_seed_ideas() -> None:
    project_root = _repo_root() / "projects" / "template_autoresearch_project"

    program = project_root / "program.md"
    seed_ideas = project_root / "seed_ideas.yaml"

    assert program.is_file()
    assert "human-authored research program" in program.read_text(encoding="utf-8")
    assert seed_ideas.is_file()
    assert "accepted" in seed_ideas.read_text(encoding="utf-8")
    assert "idea-ml-loop" in seed_ideas.read_text(encoding="utf-8")
