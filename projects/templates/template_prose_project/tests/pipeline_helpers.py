"""Test helpers that call infrastructure prose analysis before src pipeline."""

from __future__ import annotations

from pathlib import Path


def analyze_manuscript_for_config(project_root: Path, config) -> object:
    from infrastructure.prose import analyze_manuscript

    manuscript_dir = Path(project_root) / config.manuscript_dir
    return analyze_manuscript(
        manuscript_dir.resolve(),
        long_sentence_threshold=config.prose.long_sentence_threshold,
    )


def run_prose_pipeline_with_analysis(config, project_root: Path, **kwargs):
    from src.pipeline import run_prose_pipeline

    report = analyze_manuscript_for_config(project_root, config)
    return run_prose_pipeline(
        config,
        project_root=project_root,
        manuscript_report=report,
        **kwargs,
    )
