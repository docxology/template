"""Scripts package - entry point orchestrators for the build pipeline.

This package contains thin orchestrators that coordinate the template's
build pipeline stages. All business logic is in infrastructure/ modules.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class PipelineStageDefinition:
    """Typed definition of a pipeline stage for the interactive menu."""

    script: str
    function: str
    requires_ollama: bool
    description: str
    note: Optional[str] = None


# Menu option to script mapping (for run.sh interactive menu).
# This documents the relationship between menu choices and underlying entry points.
MENU_SCRIPT_MAPPING = {
    0: PipelineStageDefinition(
        script="00_setup_environment.py",
        function="run_setup_environment",
        requires_ollama=False,
        description="Setup Environment",
    ),
    1: PipelineStageDefinition(
        script="01_run_tests.py",
        function="run_all_tests",
        requires_ollama=False,
        description="Run Tests (infrastructure + project)",
    ),
    2: PipelineStageDefinition(
        script="02_run_analysis.py",
        function="run_analysis_standalone",
        requires_ollama=False,
        description="Run Analysis",
    ),
    3: PipelineStageDefinition(
        script="03_render_pdf.py",
        function="run_pdf_rendering",
        requires_ollama=False,
        note="Requires analysis outputs to be available",
        description="Render PDF",
    ),
    4: PipelineStageDefinition(
        script="04_validate_output.py",
        function="run_validation_standalone",
        requires_ollama=False,
        description="Validate Output",
    ),
    5: PipelineStageDefinition(
        script="06_llm_review.py",
        function="run_llm_review",
        requires_ollama=True,
        description="LLM Review (reviews-only from run.sh)",
    ),
    6: PipelineStageDefinition(
        script="06_llm_review.py",
        function="run_llm_translations",
        requires_ollama=True,
        description="LLM Translations (translations-only from run.sh)",
    ),
    7: PipelineStageDefinition(
        script="05_copy_outputs.py",
        function="run_copy_outputs_standalone",
        requires_ollama=False,
        description="Copy Outputs",
    ),
    8: PipelineStageDefinition(
        script="execute_pipeline.py",
        function="run_full_pipeline",
        requires_ollama=False,
        description="Run Full Pipeline (via execute_pipeline.py)",
    ),
}

try:
    from infrastructure.llm.review.pipeline_runner import ReviewMode
except ImportError:
    pass

__all__ = [
    "MENU_SCRIPT_MAPPING",
    "ReviewMode",
]
