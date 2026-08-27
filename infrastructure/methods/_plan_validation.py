"""Private validation helpers for methods orchestration plans."""

from __future__ import annotations

import json
import shlex
from pathlib import Path, PurePosixPath

from infrastructure.core.pipeline.artifacts import (
    ArtifactManifest,
    artifact_manifest_from_payload,
    output_inventory_mode_for_project,
    validate_artifact_manifest,
)
from infrastructure.core.pipeline.executor import PipelineExecutor
from infrastructure.methods._project_boundary import (
    _ExternalBoundary,
    _path_is_authorized,
)
from infrastructure.methods.models import MethodStage, MethodsIssue, MethodsOrchestrationPlan


def _validate_stage_script(
    root: Path,
    plan: MethodsOrchestrationPlan,
    stage: MethodStage,
    issues: list[MethodsIssue],
    external_boundary: _ExternalBoundary | None,
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
    if not _path_is_authorized(root, script, external_boundary):
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
    external_boundary: _ExternalBoundary | None,
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
            if not _path_is_authorized(root, Path(value), external_boundary):
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
    external_boundary: _ExternalBoundary | None,
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
        if (
            script_path.is_absolute()
            or ".." in script_path.parts
            or not _path_is_authorized(root, script_path, external_boundary)
            or not (root / script_path).is_file()
        ):
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
    for manifest_issue in validate_artifact_manifest(
        manifest,
        project_dir=project_root,
        expected_inventory_mode=output_inventory_mode_for_project(root, project_root),
    ).issues:
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
    return artifact_manifest_from_payload(payload)


def _issue(severity: str, code: str, message: str, path: str, suggestion: str) -> MethodsIssue:
    return MethodsIssue(
        severity=severity,
        code=code,
        message=message,
        path=path,
        suggestion=suggestion,
    )
