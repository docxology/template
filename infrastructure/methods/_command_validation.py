"""Validate emitted commands against canonical Methods plan bindings."""

from __future__ import annotations

import shlex
from pathlib import Path

from infrastructure.core.project_paths import resolve_source_manuscript_dir
from infrastructure.methods._plan_validation import _issue
from infrastructure.methods._project_boundary import _ExternalBoundary, _path_is_authorized
from infrastructure.methods.models import MethodsIssue, MethodsOrchestrationPlan


def _validate_plan_commands(
    root: Path,
    plan: MethodsOrchestrationPlan,
    issues: list[MethodsIssue],
    external_boundary: _ExternalBoundary | None,
    *,
    require_generated_artifacts: bool,
) -> None:
    """Reject malformed commands, missing entrypoints and wrong project paths."""
    lexical_root = root / plan.project_root
    manuscript = resolve_source_manuscript_dir(lexical_root)
    expected_project = (
        plan.project_root.relative_to("projects").as_posix()
        if plan.project_root.parts[0] == "projects"
        else plan.project_name
    )
    commands: list[tuple[str, str | None]] = [(command, None) for command in plan.validation_commands]
    stages = {stage.key: stage for stage in plan.stages}
    commands.extend((command, stage.key) for stage in plan.stages for command in stage.verification_commands)
    for command, stage_key in commands:
        try:
            argv = shlex.split(command)
            if argv[:3] != ["uv", "run", "python"] or len(argv) < 4:
                raise ValueError("command must use the declared uv run python entrypoint")
            if argv[3] == "-m":
                if len(argv) < 7 or argv[4] != "infrastructure.validation.cli":
                    raise ValueError("command must reference the supported validation module")
                action, path_value = argv[5:7]
                path = Path(path_value)
                expected = manuscript if action == "prerender" else lexical_root / "output"
                if action not in {"prerender", "integrity"}:
                    raise ValueError(f"unknown validation action: {action}")
                if path.is_absolute() or ".." in path.parts or not _path_is_authorized(root, path, external_boundary):
                    raise ValueError(f"validation target is outside the declared repository: {path_value}")
                if (root / path).absolute() != expected.absolute():
                    raise ValueError(f"validation target differs from the canonical {action} path: {path_value}")
                if (action == "prerender" or require_generated_artifacts) and not (root / path).is_dir():
                    raise ValueError(f"validation target directory is missing: {path_value}")
            else:
                script = Path(argv[3])
                if (
                    script.is_absolute()
                    or ".." in script.parts
                    or not _path_is_authorized(root, script, external_boundary)
                    or not (root / script).is_file()
                ):
                    raise ValueError(f"Python entrypoint is missing or outside the declared repository: {script}")
                if "--project" in argv:
                    value = argv[argv.index("--project") + 1]
                    if value not in {plan.project_name, expected_project}:
                        raise ValueError(f"command selects another project: {value}")
                if script.as_posix() == "scripts/runner/execute_pipeline.py":
                    if "--project" not in argv:
                        raise ValueError("pipeline command requires explicit project context")
                    if (
                        "--pipeline-yaml" not in argv
                        or Path(argv[argv.index("--pipeline-yaml") + 1]) != plan.pipeline_source
                    ):
                        raise ValueError("pipeline command does not bind its declared definition source")
                    is_live = stage_key and {"llm", "live"}.intersection(stages[stage_key].tags)
                    expected_mode = "live" if is_live else "core"
                    if "--mode" not in argv or argv[argv.index("--mode") + 1] != expected_mode:
                        raise ValueError("pipeline command does not select its declared capability mode")
                    if stage_key is not None and (
                        "--stage" not in argv or argv[argv.index("--stage") + 1] != stage_key
                    ):
                        raise ValueError("pipeline command does not select the declared stable stage key")
        except (ValueError, IndexError) as exc:
            issues.append(
                _issue(
                    "error",
                    "METHODS.COMMAND_INVALID",
                    f"{exc}: {command}",
                    plan.pipeline_source.as_posix(),
                    "Regenerate commands from canonical project paths and executable stage declarations.",
                )
            )
