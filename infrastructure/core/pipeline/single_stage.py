"""Single-stage pipeline execution helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from infrastructure.core.runtime.environment import get_python_command

logger = get_logger(__name__)

_STAGE_TO_SCRIPT: dict[str, list[str]] = {
    "clean": ["scripts/00_setup_environment.py"],
    "setup": ["scripts/00_setup_environment.py"],
    "infra_tests": ["scripts/01_run_tests.py", "--infra-only", "--verbose", "--infra-scope", "pipeline-smoke"],
    "project_tests": ["scripts/01_run_tests.py", "--project-only", "--verbose"],
    "tests": ["scripts/01_run_tests.py", "--verbose", "--infra-scope", "pipeline-smoke"],
    "analysis": ["scripts/02_run_analysis.py"],
    "render_pdf": ["scripts/03_render_pdf.py"],
    "validate": ["scripts/04_validate_output.py"],
    "copy": ["scripts/05_copy_outputs.py"],
    "llm_reviews": ["scripts/06_llm_review.py", "--reviews-only"],
    "llm_translations": ["scripts/06_llm_review.py", "--translations-only"],
    "executive_report": ["scripts/07_generate_executive_report.py"],
}


def execute_single_stage(stage: str, project_name: str, repo_root: Path) -> int:
    """Execute a single stage script in a subprocess."""
    stage_key = stage.strip().lower()
    if stage_key not in _STAGE_TO_SCRIPT:
        valid = ", ".join(sorted(_STAGE_TO_SCRIPT.keys()))
        raise SystemExit(f"Unknown stage '{stage}'. Valid: {valid}")

    script_and_args = _STAGE_TO_SCRIPT[stage_key]
    script_rel = script_and_args[0]
    extra_args = script_and_args[1:]
    cmd = get_python_command() + [str(repo_root / script_rel)] + extra_args + ["--project", project_name]
    logger.info("Executing stage '%s' for project '%s': %s", stage_key, project_name, " ".join(cmd))
    result = subprocess.run(cmd, cwd=str(repo_root), check=False, timeout=1800)
    return result.returncode
