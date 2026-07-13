"""Stage-related grader checks using canonical pipeline vocabulary."""

from __future__ import annotations

from infrastructure.core.pipeline.stage_vocabulary import text_mentions_stage


def mentions_project_analysis(lower: str, _original: str) -> bool:
    return text_mentions_stage(lower, "Project Analysis") or "02_run_analysis" in lower


def mentions_output_validation(lower: str, _original: str) -> bool:
    return (
        text_mentions_stage(lower, "Output Validation")
        or "validation.cli" in lower
        or ("validate" in lower and any(w in lower for w in ("stage", "cli", "render", "copy")))
    )


def mentions_any_pipeline_stage(lower: str, _original: str) -> bool:
    return any(
        token in lower for token in ("render", "validate", "analysis", "tests", "project analysis", "pdf rendering")
    )
