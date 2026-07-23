"""Methods orchestration plans derived from project and pipeline contracts."""

from __future__ import annotations

import json
import re
import shlex
from pathlib import Path
from pathlib import PurePosixPath

from infrastructure.core.pipeline.artifacts import (
    ArtifactManifest,
    ArtifactManifestEntry,
    validate_artifact_manifest,
)
from infrastructure.core.pipeline.dag import PipelineDAG, StageDefinition
from infrastructure.core.pipeline.definition import PipelinePurpose, resolve_pipeline_source
from infrastructure.core.pipeline.executor import PipelineExecutor
from infrastructure.methods.models import (
    MethodStage,
    MethodsAuditReport,
    MethodsIssue,
    MethodsOrchestrationPlan,
    MethodsProjectAudit,
)
from infrastructure.project.discovery import resolve_project_root
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
    project_root_abs = _resolve_project_root(root, project_name, projects_dir=projects_dir)
    project_root = _relative_to(project_root_abs, root)
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
    project_key = _project_expansion_key(project_name, project_root_abs, root)

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

    return MethodsOrchestrationPlan(
        project_name=project_name,
        project_root=project_root,
        pipeline_source=_relative_to(pipeline_source_abs, root),
        method_sections=_discover_method_sections(project_root_abs, root),
        artifact_manifest=artifact_manifest,
        evidence_registry=evidence_registry,
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
    project_root = _resolve_plan_path(root, plan.project_root)
    pipeline_source = _resolve_plan_path(root, plan.pipeline_source)
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
            _validate_stage_script(root, plan, stage, issues)
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
        _validate_artifact_paths(plan, stage, root, issues)
        _validate_verification_commands(plan, stage, root, issues)
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


def _build_stage(
    stage: StageDefinition,
    *,
    order: int,
    project_key: str,
    project_name: str = "",
) -> MethodStage:
    contract = stage.contract
    method = stage.method or (f"Execute the declared script for {stage.name}." if stage.script else "")
    return MethodStage(
        key=stage.key or "",
        name=stage.name,
        order=order,
        depends_on=tuple(stage.depends_on),
        tags=tuple(stage.tags),
        gate=contract.gate or "",
        script=_expand_artifact(stage.script or "", project_key),
        method=method,
        executor_method=(stage.method or "") if not stage.script else "",
        allow_skip=stage.allow_skip,
        input_artifacts=tuple(_expand_artifact(item, project_key) for item in contract.input_artifacts),
        output_artifacts=tuple(_expand_artifact(item, project_key) for item in contract.output_artifacts),
        definition_of_done=contract.definition_of_done,
        failure_code=contract.failure_code,
        verification_commands=_stage_verification_commands(stage, project_key, project_name),
    )


def _stage_verification_commands(stage: StageDefinition, project_key: str, project_name: str = "") -> tuple[str, ...]:
    stage_key = stage.key
    if stage.script:
        args = " ".join(stage.args)
        spacer = " " if args else ""
        script_path = stage.script.replace("{project}", project_key)
        resolved_name = project_name or project_key
        project_arg = "" if "--project" in stage.args else f" --project {resolved_name}"
        commands = [f"uv run python {script_path}{spacer}{args}{project_arg}"]
        if stage_key:
            commands.append(
                f"uv run python scripts/runner/execute_pipeline.py --project {resolved_name} --stage {stage_key}"
            )
        return tuple(commands)
    if stage_key:
        resolved_name = project_name or project_key
        return (f"uv run python scripts/runner/execute_pipeline.py --project {resolved_name} --stage {stage_key}",)
    return ()


def _validation_commands(project_name: str, project_root_key: str) -> tuple[str, ...]:
    return (
        f"uv run python scripts/runner/execute_pipeline.py --project {project_name} --core-only",
        f"uv run python -m infrastructure.validation.cli prerender {project_root_key}/manuscript --repo-root .",
        f"uv run python -m infrastructure.validation.cli integrity {project_root_key}/output",
    )


def _resolve_project_root(root: Path, project_name: str, *, projects_dir: str) -> Path:
    candidate = root / projects_dir / project_name
    if candidate.exists() or projects_dir != "projects":
        return candidate.resolve()
    return resolve_project_root(root, project_name)


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


def _expand_artifact(value: str, project_key: str) -> str:
    return value.replace("{project}", project_key)


def _project_expansion_key(
    project_name: str,
    project_root: Path,
    repo_root: Path | None = None,
) -> str:
    """Compute the ``{project}`` expansion key that is the part after ``projects/``.

    When *project_name* already carries a qualified prefix (e.g.
    ``templates/template_code_project``) it is used directly.  Otherwise the
    key is derived from *project_root* relative to the ``projects/``
    directory, so bare names like ``template_advanced_literature_review``
    expand to ``templates/template_advanced_literature_review``.
    """
    if "/" in project_name:
        return project_name
    # Try to use the canonical ``projects/`` prefix for standard layouts.
    if repo_root is not None:
        try:
            rel = project_root.resolve().relative_to((repo_root / "projects").resolve())
            return rel.as_posix()
        except ValueError:
            pass
        try:
            rel = project_root.resolve().relative_to(repo_root.resolve())
            return rel.as_posix()
        except ValueError:
            pass
    return project_root.as_posix()


def _relative_to(path: Path, root: Path) -> Path:
    try:
        return path.resolve().relative_to(root)
    except ValueError:
        return path


def _resolve_plan_path(root: Path, path: Path) -> Path:
    """Resolve a plan path without allowing it to escape the repository."""
    candidate = path if path.is_absolute() else root / path
    return candidate.resolve(strict=False)


def _validate_stage_script(
    root: Path,
    plan: MethodsOrchestrationPlan,
    stage: MethodStage,
    issues: list[MethodsIssue],
) -> None:
    """Validate a declared stage script and its repository containment."""
    script = Path(stage.script)
    if script.is_absolute() or ".." in script.parts:
        issues.append(
            _issue(
                "error",
                "METHODS.STAGE_SCRIPT_OUTSIDE_REPOSITORY",
                f"stage script is not repository-relative: {stage.script}",
                plan.pipeline_source.as_posix(),
                "Use a repository-relative script path without parent traversal.",
            )
        )
        return

    resolved = (root / script).resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError:
        issues.append(
            _issue(
                "error",
                "METHODS.STAGE_SCRIPT_OUTSIDE_REPOSITORY",
                f"stage script escapes repository root: {stage.script}",
                plan.pipeline_source.as_posix(),
                "Keep stage scripts inside the repository or use a declared executor method.",
            )
        )
        return
    if not resolved.is_file():
        issues.append(
            _issue(
                "error",
                "METHODS.STAGE_SCRIPT_MISSING",
                f"stage script does not exist: {stage.script}",
                plan.pipeline_source.as_posix(),
                "Add the script or correct the pipeline declaration.",
            )
        )


def _validate_executor_method(
    plan: MethodsOrchestrationPlan,
    stage: MethodStage,
    issues: list[MethodsIssue],
) -> None:
    """Verify built-in executor methods against the actual executor class."""
    if not hasattr(PipelineExecutor, stage.executor_method):
        issues.append(
            _issue(
                "error",
                "METHODS.STAGE_EXECUTOR_METHOD_MISSING",
                f"stage references missing executor method: {stage.executor_method}",
                plan.pipeline_source.as_posix(),
                "Use a method implemented by PipelineExecutor/PipelineStageMixin or declare a script.",
            )
        )


def _validate_artifact_paths(
    plan: MethodsOrchestrationPlan,
    stage: MethodStage,
    root: Path,
    issues: list[MethodsIssue],
) -> None:
    """Reject unsafe artifact declarations before any filesystem probing."""
    for kind, paths in (("input", stage.input_artifacts), ("output", stage.output_artifacts)):
        for value in paths:
            normalized = PurePosixPath(value)
            if normalized.is_absolute() or ".." in normalized.parts:
                issues.append(
                    _issue(
                        "error",
                        "METHODS.ARTIFACT_PATH_UNSAFE",
                        f"{kind} artifact path is absolute or traverses parents: {value}",
                        plan.pipeline_source.as_posix(),
                        "Use repository-relative artifact paths rooted inside the project or output tree.",
                    )
                )
                continue
            resolved = (root / Path(value)).resolve(strict=False)
            try:
                resolved.relative_to(root)
            except ValueError:
                issues.append(
                    _issue(
                        "error",
                        "METHODS.ARTIFACT_PATH_OUTSIDE_REPOSITORY",
                        f"{kind} artifact path escapes the repository: {value}",
                        plan.pipeline_source.as_posix(),
                        "Keep artifact declarations inside the repository boundary.",
                    )
                )


def _validate_verification_commands(
    plan: MethodsOrchestrationPlan,
    stage: MethodStage,
    root: Path,
    issues: list[MethodsIssue],
) -> None:
    """Check generated commands for a resolvable Python script entrypoint."""
    for command in stage.verification_commands:
        try:
            argv = shlex.split(command)
        except ValueError as exc:
            issues.append(
                _issue(
                    "error",
                    "METHODS.VERIFICATION_COMMAND_INVALID",
                    f"verification command cannot be parsed: {exc}",
                    plan.pipeline_source.as_posix(),
                    "Generate argv-safe commands from structured stage metadata.",
                )
            )
            continue
        script_index = next((index for index, token in enumerate(argv) if token.endswith(".py")), None)
        if script_index is None:
            continue
        script_path = Path(argv[script_index])
        if script_path.is_absolute() or not (root / script_path).is_file():
            issues.append(
                _issue(
                    "error",
                    "METHODS.VERIFICATION_SCRIPT_MISSING",
                    f"verification command references a missing script: {script_path}",
                    plan.pipeline_source.as_posix(),
                    "Compile verification commands from the same resolved script path as the stage.",
                )
            )
        if stage.script and stage.script.startswith("projects/") and "--project" not in argv:
            issues.append(
                _issue(
                    "warning",
                    "METHODS.PROJECT_CONTEXT_IMPLICIT",
                    f"project-local verification command relies on the script default project: {command}",
                    plan.pipeline_source.as_posix(),
                    "Migrate the project entrypoint to the shared --project argument contract.",
                )
            )


def _validate_json_object(
    root: Path,
    path: Path,
    *,
    missing_code: str,
    invalid_code: str,
    label: str,
    issues: list[MethodsIssue],
) -> None:
    absolute = root / path
    if not absolute.exists():
        issues.append(
            _issue(
                "error",
                missing_code,
                f"required methods evidence file is missing: {path.as_posix()}",
                path.as_posix(),
                "Run the core pipeline or refresh output reports before publication.",
            )
        )
        return
    try:
        payload = json.loads(absolute.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        detail = f"{label} is not readable JSON: {exc}"
    else:
        if isinstance(payload, dict) and payload:
            return
        detail = f"{label} must be a non-empty JSON object"
    issues.append(
        _issue(
            "error",
            invalid_code,
            detail,
            path.as_posix(),
            "Regenerate the report from the core pipeline before publication.",
        )
    )


def _validate_artifact_manifest(
    root: Path,
    path: Path,
    *,
    project_root: Path,
    issues: list[MethodsIssue],
) -> None:
    """Validate artifact JSON structure, hashes, and current file provenance."""
    absolute = root / path
    if not absolute.exists():
        issues.append(
            _issue(
                "error",
                "METHODS.ARTIFACT_MANIFEST_MISSING",
                f"required methods evidence file is missing: {path.as_posix()}",
                path.as_posix(),
                "Run the core pipeline or refresh output reports before publication.",
            )
        )
        return
    try:
        payload = json.loads(absolute.read_text(encoding="utf-8"))
        manifest = _artifact_manifest_from_payload(payload)
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        issues.append(
            _issue(
                "error",
                "METHODS.ARTIFACT_MANIFEST_INVALID",
                f"artifact manifest is not valid structured evidence: {exc}",
                path.as_posix(),
                "Regenerate the report through the shared artifact-manifest writer.",
            )
        )
        return
    if not manifest.entries:
        issues.append(
            _issue(
                "error",
                "METHODS.ARTIFACT_MANIFEST_INVALID",
                "artifact manifest must contain at least one artifact entry",
                path.as_posix(),
                "Run a rendering or analysis stage that produces a real output artifact.",
            )
        )
        return
    for manifest_issue in validate_artifact_manifest(manifest, project_dir=project_root).issues:
        issues.append(
            _issue(
                "error",
                "METHODS.ARTIFACT_MANIFEST_DRIFT",
                manifest_issue,
                path.as_posix(),
                "Regenerate the artifact manifest together with the current output tree.",
            )
        )

    stage_names = {entry.stage_name for entry in manifest.entries if entry.stage_num > 0}
    if not stage_names:
        issues.append(
            _issue(
                "warning",
                "METHODS.STAGE_PROVENANCE_UNAVAILABLE",
                "artifact manifest is an integrity snapshot, not stage-level provenance",
                path.as_posix(),
                "Run the canonical PipelineExecutor stages to produce per-stage artifact manifests.",
            )
        )


def _artifact_manifest_from_payload(payload: object) -> ArtifactManifest:
    """Parse the shared artifact-manifest schema without accepting loose JSON."""
    if not isinstance(payload, dict):
        raise ValueError("artifact manifest must contain a mapping")
    raw_entries = payload.get("entries")
    raw_issues = payload.get("issues", [])
    if not isinstance(raw_entries, list) or not isinstance(raw_issues, list):
        raise ValueError("artifact manifest entries/issues must be lists")
    entries: list[ArtifactManifestEntry] = []
    for raw_entry in raw_entries:
        if not isinstance(raw_entry, dict):
            raise ValueError("artifact manifest entry must contain a mapping")
        entries.append(
            ArtifactManifestEntry(
                path=str(raw_entry.get("path", "")),
                size_bytes=int(raw_entry.get("size_bytes", 0) or 0),
                sha256=str(raw_entry.get("sha256", "")),
                stage_num=int(raw_entry.get("stage_num", 0) or 0),
                stage_name=str(raw_entry.get("stage_name", "")),
                contract_match=bool(raw_entry.get("contract_match", False)),
                timestamp=str(raw_entry.get("timestamp", "")),
            )
        )
    return ArtifactManifest(entries=tuple(entries), issues=tuple(str(issue) for issue in raw_issues))


def _issue(severity: str, code: str, message: str, path: str, suggestion: str) -> MethodsIssue:
    return MethodsIssue(
        severity=severity,
        code=code,
        message=message,
        path=path,
        suggestion=suggestion,
    )
