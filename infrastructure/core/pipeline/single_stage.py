"""Single-stage pipeline execution helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from infrastructure.core.pipeline.stage_registry import script_argv_for_stage
from infrastructure.core.runtime.environment import get_python_command

logger = get_logger(__name__)


def execute_single_stage(stage: str, project_name: str, repo_root: Path) -> int:
    """Execute a single stage script in a subprocess."""
    script_and_args = script_argv_for_stage(stage)
    script_rel = script_and_args[0]
    extra_args = list(script_and_args[1:])
    cmd = get_python_command() + [str(repo_root / script_rel)] + extra_args + ["--project", project_name]
    logger.info("Executing stage '%s' for project '%s': %s", stage.strip().lower(), project_name, " ".join(cmd))
    result = subprocess.run(cmd, cwd=str(repo_root), check=False, timeout=1800)
    return result.returncode
