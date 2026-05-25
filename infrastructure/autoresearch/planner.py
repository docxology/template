"""AutoResearch readiness plan construction."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from infrastructure.autoresearch.config import load_autoresearch_config
from infrastructure.autoresearch.models import AutoResearchPlan, AutoResearchStage
from infrastructure.core.pipeline.dag import PipelineDAG, StageDefinition
from infrastructure.project.discovery import resolve_project_root
from infrastructure.project.domain_profile import load_domain_profile
from infrastructure.project.experiment_plan import load_experiment_plan


def build_autoresearch_plan(
    repo_root: Path,
    project_name: str,
    projects_dir: str = "projects",
) -> AutoResearchPlan:
    """Build a deterministic AutoResearch plan from existing project metadata."""
    repo_root = repo_root.resolve()
    project_root = _resolve_project_root(repo_root, project_name, projects_dir)
    config = load_autoresearch_config(project_root)
    profile = load_domain_profile(project_root)
    experiment_plan = load_experiment_plan(project_root)
    dag = PipelineDAG.from_yaml(_pipeline_yaml(repo_root, project_root))
    stages = tuple(_stage_from_definition(stage) for stage in dag.sorted_stages())
    declared_gates = tuple(dict.fromkeys(stage.gate for stage in stages if stage.gate is not None))
    required_artifacts = tuple(dict.fromkeys((*profile.artifact_expectations, *config.required_artifacts)))
    topic = config.topic or profile.display_name or project_name

    return AutoResearchPlan(
        repo_root=repo_root,
        project_root=project_root,
        project_name=project_name,
        config=replace(config, topic=topic),
        domain=profile.domain,
        display_name=profile.display_name,
        experiment_protocol=experiment_plan.protocol if experiment_plan else "",
        experiment_conditions=tuple(condition.name for condition in experiment_plan.conditions)
        if experiment_plan
        else (),
        stages=stages,
        declared_gates=declared_gates,
        stage_gates=config.stage_gates,
        required_artifacts=required_artifacts,
        quality_checks=config.quality_checks,
    )


def _resolve_project_root(repo_root: Path, project_name: str, projects_dir: str) -> Path:
    if projects_dir == "projects":
        return resolve_project_root(repo_root, project_name).resolve()
    return (repo_root / projects_dir / project_name).resolve()


def _pipeline_yaml(repo_root: Path, project_root: Path) -> Path:
    project_yaml = project_root / "pipeline.yaml"
    if project_yaml.exists():
        return project_yaml
    return repo_root / "infrastructure" / "core" / "pipeline" / "pipeline.yaml"


def _stage_from_definition(stage: StageDefinition) -> AutoResearchStage:
    contract = stage.contract
    return AutoResearchStage(
        name=stage.name,
        depends_on=tuple(stage.depends_on),
        gate=contract.gate,
        input_artifacts=tuple(contract.input_artifacts),
        output_artifacts=tuple(contract.output_artifacts),
        definition_of_done=contract.definition_of_done,
        failure_code=contract.failure_code,
    )
