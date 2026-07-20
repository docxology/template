"""Project-aware single-stage pipeline execution helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from infrastructure.core.pipeline.dag import PipelineDAG
from infrastructure.core.pipeline.definition import PipelinePurpose, resolve_pipeline_source
from infrastructure.core.pipeline.executor import PipelineExecutor
from infrastructure.core.pipeline.stages import build_stage_subprocess_env, resolve_pipeline_script_path
from infrastructure.core.pipeline.stage_registry import (
    normalize_stage_key,
    resolve_stage_definition,
    script_argv_for_stage,
)
from infrastructure.core.pipeline.types import PipelineConfig
from infrastructure.core.runtime.environment import get_python_command

logger = get_logger(__name__)
_LEGACY_AGGREGATES = frozenset({"tests", "executive_report"})


def execute_single_stage(
    stage: str,
    project_name: str,
    repo_root: Path,
    *,
    pipeline_path: Path | str | None = None,
) -> int:
    """Execute one selected-project DAG stage or an explicit compatibility aggregate."""
    token = normalize_stage_key(stage)
    if token in _LEGACY_AGGREGATES:
        return _execute_legacy_aggregate(token, project_name, repo_root)

    config = PipelineConfig(
        project_name=project_name,
        repo_root=repo_root,
        pipeline_path=Path(pipeline_path) if pipeline_path is not None else None,
    )
    source = resolve_pipeline_source(
        repo_root,
        config.project_dir,
        explicit_path=pipeline_path,
        purpose=PipelinePurpose.EXECUTION,
    )
    definition = resolve_stage_definition(PipelineDAG.from_yaml(source.path), token)
    logger.info(
        "Executing stage '%s' (%s) for project '%s' from %s",
        definition.name,
        definition.key or "name-only",
        project_name,
        source.path,
    )
    if definition.script:
        script = definition.script.replace("{project}", project_name)
        script_path = resolve_pipeline_script_path(repo_root, script)
        cmd = get_python_command() + [str(script_path), *definition.args, "--project", project_name]
        result = subprocess.run(
            cmd,
            cwd=str(repo_root),
            env=build_stage_subprocess_env(repo_root, config.project_dir),
            check=False,
            timeout=1800,
        )
        if result.returncode == 2 and definition.allow_skip:
            return 0
        return result.returncode
    if definition.method:
        executor = PipelineExecutor(config)
        method = getattr(executor, definition.method, None)
        if method is None:
            raise SystemExit(f"Stage '{definition.name}' references missing executor method '{definition.method}'")
        return 0 if bool(method()) else 1
    raise SystemExit(f"Stage '{definition.name}' has neither script nor method")


def _execute_legacy_aggregate(stage: str, project_name: str, repo_root: Path) -> int:
    script_and_args = script_argv_for_stage(stage)
    command = get_python_command() + [
        str(repo_root / script_and_args[0]),
        *script_and_args[1:],
        "--project",
        project_name,
    ]
    logger.info("Executing compatibility stage '%s' for project '%s'", stage, project_name)
    return subprocess.run(command, cwd=str(repo_root), check=False, timeout=1800).returncode
