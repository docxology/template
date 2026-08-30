"""Private plan-building helpers for methods orchestration."""

from __future__ import annotations

import re
import shlex
from pathlib import Path

from infrastructure.core.pipeline.dag import StageDefinition
from infrastructure.methods._project_boundary import (
    _portable_project_path,
)
from infrastructure.methods.models import MethodStage
from infrastructure.project.discovery import resolve_project_root

_METHOD_SECTION_TOKENS = ("method", "methodology", "experimental_setup", "protocol")
_METHOD_HEADING_RE = re.compile(
    r"(?m)^#{1,3}[ \t]+(?:methods?|methodology|experimental[ _-]setup|protocol)\b",
    re.IGNORECASE,
)


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
        script_path = stage.script.replace("{project}", project_key)
        resolved_name = project_name or project_key
        argv = ["uv", "run", "python", script_path, *stage.args]
        if "--project" not in stage.args:
            argv.extend(["--project", resolved_name])
        commands = [shlex.join(argv)]
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
    if candidate.exists() or candidate.is_symlink() or projects_dir != "projects":
        return candidate.resolve()
    return resolve_project_root(root, project_name)


def _discover_method_sections(
    project_root: Path,
    repo_root: Path,
    *,
    project_display_root: Path | None = None,
) -> tuple[str, ...]:
    manuscript_dir = project_root / "manuscript"
    if not manuscript_dir.is_dir():
        return ()
    sections = []
    for path in sorted(manuscript_dir.glob("*.md")):
        normalized = path.stem.lower().replace("-", "_")
        if any(token in normalized for token in _METHOD_SECTION_TOKENS):
            sections.append(_display_project_child(path, project_root, repo_root, project_display_root).as_posix())
            continue
        try:
            body = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if _METHOD_HEADING_RE.search(body):
            sections.append(_display_project_child(path, project_root, repo_root, project_display_root).as_posix())
    return tuple(sections)


def _display_project_child(
    path: Path,
    project_root: Path,
    repo_root: Path,
    project_display_root: Path | None,
) -> Path:
    return _portable_project_path(
        path,
        repo_root=repo_root,
        project_root=project_root,
        project_display_root=project_display_root or project_root,
    )


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
            rel = project_root.absolute().relative_to((repo_root / "projects").absolute())
            return rel.as_posix()
        except ValueError:
            pass
        try:
            rel = project_root.resolve().relative_to(repo_root.resolve())
            return rel.as_posix()
        except ValueError:
            pass
    return project_root.as_posix()


def _optional_surface_path(
    project_root: Path,
    relative_path: str,
    *,
    display_root: Path | None = None,
) -> Path | None:
    """Return a project-relative surface path only when its source exists."""
    path = project_root / relative_path
    if not path.is_file():
        return None
    return (display_root / relative_path) if display_root is not None else path


def _format_optional_path(path: Path | None) -> str:
    """Render an optional methods surface without inventing a file."""
    return path.as_posix() if path is not None else "not present"


def _resolve_plan_path(root: Path, path: Path) -> Path:
    """Resolve a plan path without allowing it to escape the repository."""
    candidate = path if path.is_absolute() else root / path
    return candidate.resolve(strict=False)
