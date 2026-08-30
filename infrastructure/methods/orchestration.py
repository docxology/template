"""Methods orchestration plans derived from project and pipeline contracts."""

from __future__ import annotations

import re
from pathlib import Path

from infrastructure.core.pipeline.dag import PipelineDAG
from infrastructure.core.pipeline.definition import PipelinePurpose, resolve_pipeline_source
from infrastructure.core.project_paths import validate_project_name
from infrastructure.methods._project_boundary import (
    _external_lifecycle_git_boundary,
    _lexical_plan_path,
    _lexical_project_root,
    _portable_project_path,
)
from infrastructure.methods._plan_builder import (
    _build_stage,
    _discover_method_sections,
    _format_optional_path,
    _optional_surface_path,
    _project_expansion_key,
    _resolve_plan_path,
    _resolve_project_root,
    _validation_commands,
)
from infrastructure.methods._plan_validation import (
    _issue,
    _validate_artifact_manifest,
    _validate_artifact_paths,
    _validate_executor_method,
    _validate_json_object,
    _validate_stage_script,
    _validate_verification_commands,
)
from infrastructure.methods.models import (
    MethodsAuditReport,
    MethodsIssue,
    MethodsOrchestrationPlan,
    MethodsProjectAudit,
)
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

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
    pipeline_path: Path | str | None = None,
    artifact_mode: str = "rendered",
) -> MethodsOrchestrationPlan:
    """Build a deterministic methods orchestration plan for a project.

    The plan is read-only: it maps existing pipeline contracts, manuscript
    methods sections, artifact manifests, evidence registries, and validation
    commands into one object that can be rendered or checked.
    """
    root = Path(repo_root).resolve()
    project_name = validate_project_name(project_name)
    project_root_abs = _resolve_project_root(root, project_name, projects_dir=projects_dir)
    lexical_project_root = _lexical_project_root(
        root,
        project_name,
        project_root_abs,
        projects_dir=projects_dir,
    )
    _external_lifecycle_git_boundary(root, lexical_project_root, project_root_abs)
    project_root = lexical_project_root.relative_to(root)
    if artifact_mode not in {"source", "rendered"}:
        raise ValueError(f"Unknown artifact mode: {artifact_mode}")
    pipeline_source_abs = resolve_pipeline_source(
        root,
        project_root_abs,
        explicit_path=pipeline_path,
        purpose=PipelinePurpose.METHODS,
    ).path
    dag = PipelineDAG.from_yaml(pipeline_source_abs)
    sorted_stage_definitions = dag.sorted_stages()

    # Compute the project key for ``{project}`` expansion: the path after
    # ``projects/`` so bare names like ``template_advanced_literature_review``
    # expand to ``templates/template_advanced_literature_review``.
    project_key = _project_expansion_key(project_name, lexical_project_root, root)

    stages = tuple(
        _build_stage(
            stage,
            order=index,
            project_key=project_key,
            project_name=project_name,
        )
        for index, stage in enumerate(sorted_stage_definitions, start=1)
    )
    artifact_manifest = project_root / "output" / "reports" / "artifact_manifest.json"
    evidence_registry = project_root / "output" / "reports" / "evidence_registry.json"
    figure_registry = _optional_surface_path(
        project_root_abs,
        "output/figures/figure_registry.json",
        display_root=project_root,
    )
    claim_ledger = _optional_surface_path(
        project_root_abs,
        "data/claim_ledger.yaml",
        display_root=project_root,
    )
    experiment_plan = _optional_surface_path(
        project_root_abs,
        "experiment_plan.yaml",
        display_root=project_root,
    )

    return MethodsOrchestrationPlan(
        project_name=project_name,
        project_root=project_root,
        pipeline_source=_portable_project_path(
            pipeline_source_abs,
            repo_root=root,
            project_root=project_root_abs,
            project_display_root=project_root,
        ),
        method_sections=_discover_method_sections(
            project_root_abs,
            root,
            project_display_root=project_root,
        ),
        artifact_manifest=artifact_manifest,
        evidence_registry=evidence_registry,
        figure_registry=figure_registry,
        claim_ledger=claim_ledger,
        experiment_plan=experiment_plan,
        stages=stages,
        validation_commands=_validation_commands(project_name, project_key),
        dropped_dependency_edges=tuple(dag.dropped_dependency_edges),
        artifact_mode=artifact_mode,
    )


def validate_methods_orchestration_plan(
    plan: MethodsOrchestrationPlan,
    *,
    repo_root: Path | str = ".",
    require_generated_artifacts: bool | None = None,
) -> tuple[MethodsIssue, ...]:
    """Validate methods surfaces and, optionally, generated evidence reports.

    Source-only publication audits validate the declared stage contracts without
    requiring ignored build outputs. Rendered audits pass
    ``require_generated_artifacts=True`` to make the manifest and evidence
    registry deterministic blocking requirements.
    """
    root = Path(repo_root).resolve()
    if require_generated_artifacts is None:
        require_generated_artifacts = plan.artifact_mode == "rendered"
    issues: list[MethodsIssue] = []
    lexical_project_root = _lexical_plan_path(root, plan.project_root)
    project_root = _resolve_plan_path(root, plan.project_root)
    pipeline_source = _resolve_plan_path(root, plan.pipeline_source)
    try:
        external_boundary = _external_lifecycle_git_boundary(
            root,
            lexical_project_root,
            project_root,
        )
    except ValueError as exc:
        external_boundary = None
        issues.append(
            _issue(
                "error",
                "METHODS.PROJECT_ROOT_OUTSIDE_REPOSITORY",
                str(exc),
                plan.project_root.as_posix(),
                "Use a managed lifecycle leaf symlink backed by a readable private Git worktree.",
            )
        )
    if not project_root.is_dir():
        issues.append(
            _issue(
                "error",
                "METHODS.PROJECT_ROOT_MISSING",
                f"project root is missing: {plan.project_root.as_posix()}",
                plan.project_root.as_posix(),
                "Resolve the project through the canonical projects directory before auditing methods.",
            )
        )
    if not pipeline_source.is_file():
        issues.append(
            _issue(
                "error",
                "METHODS.PIPELINE_SOURCE_MISSING",
                f"pipeline source is missing: {plan.pipeline_source.as_posix()}",
                plan.pipeline_source.as_posix(),
                "Declare a readable pipeline YAML source for the methods plan.",
            )
        )
    for stage_name, dependency in plan.dropped_dependency_edges:
        issues.append(
            _issue(
                "error",
                "METHODS.PIPELINE_DEPENDENCY_ORPHANED",
                f"stage {stage_name!r} depends on missing stage {dependency!r}",
                plan.pipeline_source.as_posix(),
                "Restore the dependency or remove the stage from the filtered pipeline explicitly.",
            )
        )
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
    if require_generated_artifacts:
        _validate_artifact_manifest(
            root,
            plan.artifact_manifest,
            project_root=project_root,
            issues=issues,
        )
        _validate_json_object(
            root,
            plan.evidence_registry,
            missing_code="METHODS.EVIDENCE_REGISTRY_MISSING",
            invalid_code="METHODS.EVIDENCE_REGISTRY_INVALID",
            label="evidence registry",
            issues=issues,
        )
    for stage in plan.stages:
        if not stage.key:
            issues.append(
                _issue(
                    "error",
                    "METHODS.STAGE_KEY_MISSING",
                    f"stage lacks stable key identity: {stage.name}",
                    plan.pipeline_source.as_posix(),
                    "Declare a stable key while retaining the human-readable stage name.",
                )
            )
        if not stage.script and not stage.executor_method:
            issues.append(
                _issue(
                    "error",
                    "METHODS.STAGE_EXECUTOR_MISSING",
                    f"stage has neither a script nor an executor method: {stage.name}",
                    plan.pipeline_source.as_posix(),
                    "Declare exactly one executable stage entrypoint.",
                )
            )
        if stage.executor_method:
            _validate_executor_method(plan, stage, issues)
        if stage.script:
            _validate_stage_script(root, plan, stage, issues, external_boundary)
        if not stage.failure_code.strip():
            issues.append(
                _issue(
                    "error",
                    "METHODS.STAGE_FAILURE_CODE_MISSING",
                    f"stage lacks failure_code: {stage.name}",
                    plan.pipeline_source.as_posix(),
                    "Assign a stable failure code so downstream reports can classify the failure.",
                )
            )
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
                    "error",
                    "METHODS.STAGE_OUTPUTS_MISSING",
                    f"stage lacks output_artifacts: {stage.name}",
                    plan.pipeline_source.as_posix(),
                    "Declare output artifacts so methods claims can be traced.",
                )
            )
        _validate_artifact_paths(plan, stage, root, issues, external_boundary)
        _validate_verification_commands(plan, stage, root, issues, external_boundary)
    return tuple(issues)


def audit_methods_projects(
    repo_root: Path | str,
    projects: tuple[str, ...] | list[str],
    *,
    artifact_mode: str = "rendered",
    projects_dir: str = "projects",
) -> MethodsAuditReport:
    """Build and validate deterministic methods plans for many projects."""
    audited: list[MethodsProjectAudit] = []
    for project_name in projects:
        plan = build_methods_orchestration_plan(
            repo_root,
            project_name,
            projects_dir=projects_dir,
            artifact_mode=artifact_mode,
        )
        issues = validate_methods_orchestration_plan(plan, repo_root=repo_root)
        audited.append(MethodsProjectAudit(plan=plan, issues=issues))
    return MethodsAuditReport(projects=tuple(audited), artifact_mode=artifact_mode)


def audit_public_methods(
    repo_root: Path | str,
    *,
    artifact_mode: str = "rendered",
) -> MethodsAuditReport:
    """Audit the canonical public exemplar roster."""
    return audit_methods_projects(
        repo_root,
        list(PUBLIC_PROJECT_NAMES),
        artifact_mode=artifact_mode,
    )


def render_methods_orchestration_markdown(plan: MethodsOrchestrationPlan) -> str:
    """Render a methods orchestration plan as Markdown."""
    lines = [
        f"# Methods orchestration: {plan.project_name}",
        "",
        "## Method Surfaces",
        "",
        f"- Project root: `{plan.project_root.as_posix()}`",
        f"- Pipeline source: `{plan.pipeline_source.as_posix()}`",
        f"- Schema version: `{plan.schema_version}`",
        f"- Artifact mode: `{plan.artifact_mode}`",
        f"- Artifact manifest: `{plan.artifact_manifest.as_posix()}`",
        f"- Evidence registry: `{plan.evidence_registry.as_posix()}`",
        f"- Figure registry: `{_format_optional_path(plan.figure_registry)}`",
        f"- Claim ledger: `{_format_optional_path(plan.claim_ledger)}`",
        f"- Experiment plan: `{_format_optional_path(plan.experiment_plan)}`",
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
            "| # | Key | Stage | Gate | Inputs | Outputs | Verification |",
            "| ---: | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for stage in plan.stages:
        gate = stage.gate or "-"
        inputs = "<br>".join(f"`{item}`" for item in stage.input_artifacts) or "-"
        outputs = "<br>".join(f"`{item}`" for item in stage.output_artifacts) or "-"
        commands = "<br>".join(f"`{command}`" for command in stage.verification_commands) or "-"
        key = f"`{stage.key}`" if stage.key else "-"
        lines.append(f"| {stage.order} | {key} | {stage.name} | {gate} | {inputs} | {outputs} | {commands} |")
    lines.extend(
        [
            "",
            "## Validation",
            "",
        ]
    )
    lines.extend(f"- `{command}`" for command in plan.validation_commands)
    return "\n".join(lines) + "\n"
