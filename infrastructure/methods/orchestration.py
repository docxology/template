"""Methods orchestration plans derived from project and pipeline contracts."""

from __future__ import annotations

import re
from pathlib import Path

from infrastructure.core.pipeline.dag import PipelineDAG, StageDefinition
from infrastructure.methods.models import MethodStage, MethodsIssue, MethodsOrchestrationPlan
from infrastructure.project.discovery import resolve_project_root

_STAGE_NAME_TO_KEY = {
    "Clean Output Directories": "clean",
    "Environment Setup": "setup",
    "Infrastructure Tests": "infra_tests",
    "Project Tests": "project_tests",
    "Project Analysis": "analysis",
    "PDF Rendering": "render_pdf",
    "Output Validation": "validate",
    "LLM Scientific Review": "llm_reviews",
    "LLM Translations": "llm_translations",
    "Copy Outputs": "copy",
}

_METHOD_SECTION_TOKENS = ("method", "methodology", "experimental_setup", "protocol")

# A manuscript file is a method section if its *filename* carries a method token
# (above) OR it contains a top-level Methods/Methodology/Protocol heading. The
# heading fallback covers exemplars (e.g. template_template) whose Methods content
# lives inside a differently-named section file such as `03a_architecture.md`.
_METHOD_HEADING_RE = re.compile(
    r"(?m)^#{1,3}[ \t]+(?:methods?|methodology|experimental[ _-]setup|protocol)\b",
    re.IGNORECASE,
)


def build_methods_orchestration_plan(
    repo_root: Path | str,
    project_name: str,
    *,
    projects_dir: str = "projects",
) -> MethodsOrchestrationPlan:
    """Build a deterministic methods orchestration plan for a project.

    The plan is read-only: it maps existing pipeline contracts, manuscript
    methods sections, artifact manifests, evidence registries, and validation
    commands into one object that can be rendered or checked.
    """
    root = Path(repo_root).resolve()
    project_root_abs = _resolve_project_root(root, project_name, projects_dir=projects_dir)
    project_root = _relative_to(project_root_abs, root)
    pipeline_source_abs = _pipeline_source(root, project_root_abs)
    dag = PipelineDAG.from_yaml(pipeline_source_abs)

    stages = tuple(
        _build_stage(
            stage,
            order=index,
            project_name=project_name,
        )
        for index, stage in enumerate(dag.sorted_stages(), start=1)
    )
    artifact_manifest = project_root / "output" / "reports" / "artifact_manifest.json"
    evidence_registry = project_root / "output" / "reports" / "evidence_registry.json"

    return MethodsOrchestrationPlan(
        project_name=project_name,
        project_root=project_root,
        pipeline_source=_relative_to(pipeline_source_abs, root),
        method_sections=_discover_method_sections(project_root_abs, root),
        artifact_manifest=artifact_manifest,
        evidence_registry=evidence_registry,
        stages=stages,
        validation_commands=_validation_commands(project_name),
    )


def validate_methods_orchestration_plan(
    plan: MethodsOrchestrationPlan,
    *,
    repo_root: Path | str = ".",
) -> tuple[MethodsIssue, ...]:
    """Validate that the methods plan has the publication-critical surfaces."""
    root = Path(repo_root).resolve()
    issues: list[MethodsIssue] = []
    if not plan.stages:
        issues.append(
            _issue(
                "error",
                "METHODS.PIPELINE_STAGES_MISSING",
                "pipeline has no stages",
                plan.pipeline_source.as_posix(),
                "Declare pipeline stages with contracts before publishing methods.",
            )
        )
    if not plan.method_sections:
        issues.append(
            _issue(
                "error",
                "METHODS.METHOD_SECTION_MISSING",
                "manuscript has no methods or methodology section file",
                (plan.project_root / "manuscript").as_posix(),
                "Add a methods section or rename the section file to include methods/methodology.",
            )
        )
    _validate_relative_file(root, plan.artifact_manifest, "METHODS.ARTIFACT_MANIFEST_MISSING", issues)
    _validate_relative_file(root, plan.evidence_registry, "METHODS.EVIDENCE_REGISTRY_MISSING", issues)
    for stage in plan.stages:
        if not stage.definition_of_done.strip():
            issues.append(
                _issue(
                    "error",
                    "METHODS.STAGE_DONE_MISSING",
                    f"stage lacks definition_of_done: {stage.name}",
                    plan.pipeline_source.as_posix(),
                    "Add a concrete stage contract definition_of_done.",
                )
            )
        if not stage.output_artifacts:
            issues.append(
                _issue(
                    "warning",
                    "METHODS.STAGE_OUTPUTS_MISSING",
                    f"stage lacks output_artifacts: {stage.name}",
                    plan.pipeline_source.as_posix(),
                    "Declare output artifacts so methods claims can be traced.",
                )
            )
    return tuple(issues)


def render_methods_orchestration_markdown(plan: MethodsOrchestrationPlan) -> str:
    """Render a methods orchestration plan as Markdown."""
    lines = [
        f"# Methods orchestration: {plan.project_name}",
        "",
        "## Method Surfaces",
        "",
        f"- Project root: `{plan.project_root.as_posix()}`",
        f"- Pipeline source: `{plan.pipeline_source.as_posix()}`",
        f"- Artifact manifest: `{plan.artifact_manifest.as_posix()}`",
        f"- Evidence registry: `{plan.evidence_registry.as_posix()}`",
        "- Manuscript method sections:",
    ]
    if plan.method_sections:
        lines.extend(f"  - `{section}`" for section in plan.method_sections)
    else:
        lines.append("  - none found")
    lines.extend(
        [
            "",
            "## Stage Contracts",
            "",
            "| # | Stage | Gate | Inputs | Outputs | Verification |",
            "| ---: | --- | --- | --- | --- | --- |",
        ]
    )
    for stage in plan.stages:
        gate = stage.gate or "-"
        inputs = "<br>".join(f"`{item}`" for item in stage.input_artifacts) or "-"
        outputs = "<br>".join(f"`{item}`" for item in stage.output_artifacts) or "-"
        commands = "<br>".join(f"`{command}`" for command in stage.verification_commands) or "-"
        lines.append(f"| {stage.order} | {stage.name} | {gate} | {inputs} | {outputs} | {commands} |")
    lines.extend(
        [
            "",
            "## Validation",
            "",
        ]
    )
    lines.extend(f"- `{command}`" for command in plan.validation_commands)
    return "\n".join(lines) + "\n"


def _build_stage(
    stage: StageDefinition,
    *,
    order: int,
    project_name: str,
) -> MethodStage:
    contract = stage.contract
    return MethodStage(
        name=stage.name,
        order=order,
        depends_on=tuple(stage.depends_on),
        tags=tuple(stage.tags),
        gate=contract.gate or "",
        script=stage.script or "",
        method=stage.method or "",
        input_artifacts=tuple(_expand_artifact(item, project_name) for item in contract.input_artifacts),
        output_artifacts=tuple(_expand_artifact(item, project_name) for item in contract.output_artifacts),
        definition_of_done=contract.definition_of_done,
        failure_code=contract.failure_code,
        verification_commands=_stage_verification_commands(stage, project_name),
    )


def _stage_verification_commands(stage: StageDefinition, project_name: str) -> tuple[str, ...]:
    stage_key = _STAGE_NAME_TO_KEY.get(stage.name)
    if stage.script:
        args = " ".join(stage.args)
        spacer = " " if args else ""
        commands = [f"uv run python scripts/{stage.script}{spacer}{args} --project {project_name}"]
        if stage_key:
            commands.append(
                f"uv run python scripts/runner/execute_pipeline.py --project {project_name} --stage {stage_key}"
            )
        return tuple(commands)
    fallback_key = stage_key or stage.name.lower().replace(" ", "_")
    return (f"uv run python scripts/runner/execute_pipeline.py --project {project_name} --stage {fallback_key}",)


def _validation_commands(project_name: str) -> tuple[str, ...]:
    return (
        f"uv run python scripts/runner/execute_pipeline.py --project {project_name} --core-only",
        f"uv run python -m infrastructure.validation.cli prerender projects/{project_name}/manuscript --repo-root .",
        f"uv run python -m infrastructure.validation.cli integrity projects/{project_name}/output",
    )


def _resolve_project_root(root: Path, project_name: str, *, projects_dir: str) -> Path:
    candidate = root / projects_dir / project_name
    if candidate.exists() or projects_dir != "projects":
        return candidate.resolve()
    return resolve_project_root(root, project_name)


def _pipeline_source(root: Path, project_root: Path) -> Path:
    project_pipeline = project_root / "pipeline.yaml"
    if project_pipeline.exists():
        return project_pipeline
    return root / "infrastructure" / "core" / "pipeline" / "pipeline.yaml"


def _discover_method_sections(project_root: Path, repo_root: Path) -> tuple[str, ...]:
    manuscript_dir = project_root / "manuscript"
    if not manuscript_dir.is_dir():
        return ()
    sections = []
    for path in sorted(manuscript_dir.glob("*.md")):
        normalized = path.stem.lower().replace("-", "_")
        if any(token in normalized for token in _METHOD_SECTION_TOKENS):
            sections.append(_relative_to(path, repo_root).as_posix())
            continue
        try:
            body = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if _METHOD_HEADING_RE.search(body):
            sections.append(_relative_to(path, repo_root).as_posix())
    return tuple(sections)


def _expand_artifact(value: str, project_name: str) -> str:
    return value.replace("{project}", project_name)


def _relative_to(path: Path, root: Path) -> Path:
    try:
        return path.resolve().relative_to(root)
    except ValueError:
        return path


def _validate_relative_file(root: Path, path: Path, code: str, issues: list[MethodsIssue]) -> None:
    if (root / path).exists():
        return
    issues.append(
        _issue(
            "error",
            code,
            f"required methods evidence file is missing: {path.as_posix()}",
            path.as_posix(),
            "Run the core pipeline or refresh output reports before publication.",
        )
    )


def _issue(severity: str, code: str, message: str, path: str, suggestion: str) -> MethodsIssue:
    return MethodsIssue(
        severity=severity,
        code=code,
        message=message,
        path=path,
        suggestion=suggestion,
    )
