"""Scripts package - entry point orchestrators for the build pipeline.

This package contains thin orchestrators that coordinate the template's
build pipeline stages. All business logic is in infrastructure/ modules.
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

_logger = logging.getLogger(__name__)


def ensure_repo_root_on_path() -> Path:
    """Prepend the repository root to ``sys.path`` and return the Path.

    Idempotent — subsequent calls do not re-insert if already present. Lets each
    script in this package be runnable directly (``python scripts/foo.py``) while
    still importing ``infrastructure`` and ``projects`` as top-level packages.

    Returns:
        The absolute :class:`Path` to the repository root.
    """
    repo_root = Path(__file__).resolve().parent.parent
    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)
    return repo_root


@dataclass
class PipelineStageDefinition:
    """Typed definition of a pipeline stage for the interactive menu."""

    script: str
    requires_ollama: bool
    description: str
    note: Optional[str] = None


# Menu option to script mapping (for run.sh interactive menu).
# This documents the relationship between menu choices and underlying entry points.
MENU_SCRIPT_MAPPING = {
    0: PipelineStageDefinition(
        script="00_setup_environment.py",
        requires_ollama=False,
        description="Setup Environment",
    ),
    1: PipelineStageDefinition(
        script="01_run_tests.py",
        requires_ollama=False,
        description="Run Tests (infrastructure + project)",
    ),
    2: PipelineStageDefinition(
        script="02_run_analysis.py",
        requires_ollama=False,
        description="Run Analysis",
    ),
    3: PipelineStageDefinition(
        script="03_render_pdf.py",
        requires_ollama=False,
        note="Requires analysis outputs to be available",
        description="Render PDF",
    ),
    4: PipelineStageDefinition(
        script="04_validate_output.py",
        requires_ollama=False,
        description="Validate Output",
    ),
    5: PipelineStageDefinition(
        script="06_llm_review.py",
        requires_ollama=True,
        description="LLM Review (reviews-only from run.sh)",
    ),
    6: PipelineStageDefinition(
        script="06_llm_review.py",
        requires_ollama=True,
        description="LLM Translations (translations-only from run.sh)",
    ),
    7: PipelineStageDefinition(
        script="05_copy_outputs.py",
        requires_ollama=False,
        description="Copy Outputs",
    ),
    8: PipelineStageDefinition(
        script="execute_pipeline.py",
        requires_ollama=False,
        description="Run Full Pipeline (via execute_pipeline.py)",
    ),
}

__all__ = [
    "MENU_SCRIPT_MAPPING",
    "PipelineStageDefinition",
    "ensure_repo_root_on_path",
]
