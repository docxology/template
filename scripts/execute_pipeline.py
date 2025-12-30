#!/usr/bin/env python3
"""Execute research project pipeline stages.

This script provides pipeline execution functionality extracted from run.sh
into testable Python code following the thin orchestrator pattern.
"""

import sys
from pathlib import Path

# Add repo root to Python path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from infrastructure.core.logging_utils import get_logger
from infrastructure.core.pipeline import PipelineConfig, PipelineExecutor
from infrastructure.core.pipeline_summary import generate_pipeline_summary
from infrastructure.core.environment import get_python_command

logger = get_logger(__name__)

_STAGE_TO_SCRIPT: dict[str, list[str]] = {
    "clean": ["scripts/00_setup_environment.py"],  # setup script also validates dirs; clean is handled in PipelineExecutor
    "setup": ["scripts/00_setup_environment.py"],
    "infra_tests": ["scripts/01_run_tests.py", "--infra-only"],
    "project_tests": ["scripts/01_run_tests.py", "--project-only"],
    "tests": ["scripts/01_run_tests.py"],
    "analysis": ["scripts/02_run_analysis.py"],
    "render_pdf": ["scripts/03_render_pdf.py"],
    "validate": ["scripts/04_validate_output.py"],
    "copy": ["scripts/05_copy_outputs.py"],
    "llm_reviews": ["scripts/06_llm_review.py", "--reviews-only"],
    "llm_translations": ["scripts/06_llm_review.py", "--translations-only"],
    "executive_report": ["scripts/07_generate_executive_report.py"],
}


def execute_single_stage(stage: str, project_name: str, repo_root: Path) -> int:
    """Execute a single stage script in a subprocess.

    This is intentionally a thin wrapper around existing stage entry points.
    """
    stage_key = stage.strip().lower()
    if stage_key not in _STAGE_TO_SCRIPT:
        valid = ", ".join(sorted(_STAGE_TO_SCRIPT.keys()))
        raise SystemExit(f"Unknown stage '{stage}'. Valid: {valid}")

    script_and_args = _STAGE_TO_SCRIPT[stage_key]
    script_rel = script_and_args[0]
    extra_args = script_and_args[1:]

    # Most scripts support --project; executive report ignores it but accepts it.
    cmd = get_python_command() + [str(repo_root / script_rel)] + extra_args + ["--project", project_name]
    logger.info(f"Executing stage '{stage_key}' for project '{project_name}': {' '.join(cmd)}")

    import subprocess

    result = subprocess.run(cmd, cwd=str(repo_root), check=False)
    return result.returncode


def execute_pipeline(
    project_name: str,
    repo_root: Path,
    skip_infra: bool = False,
    skip_llm: bool = False,
    resume: bool = False,
    core_only: bool = False,
) -> int:
    """Execute pipeline for a single project.

    Args:
        project_name: Name of the project to execute
        repo_root: Repository root path
        skip_infra: Whether to skip infrastructure tests
        skip_llm: Whether to skip LLM stages
        resume: Whether to resume from checkpoint
        core_only: Whether to run core pipeline only (no LLM)

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Create pipeline configuration
        config = PipelineConfig(
            project_name=project_name,
            repo_root=repo_root,
            skip_infra=skip_infra,
            skip_llm=skip_llm,
            resume=resume
        )

        # Execute pipeline
        executor = PipelineExecutor(config)

        if core_only:
            results = executor.execute_core_pipeline()
        else:
            results = executor.execute_full_pipeline()

        # Generate and display summary
        output_dir = repo_root / 'projects' / project_name / 'output'
        summary = generate_pipeline_summary(
            project_name=project_name,
            stage_results=results,
            total_duration=sum(r.duration for r in results),
            output_dir=output_dir,
            format='text'
        )
        print(summary)

        # Return appropriate exit code
        success = all(r.success for r in results)
        return 0 if success else 1

    except Exception as e:
        logger.error(f'Pipeline execution failed: {e}')
        return 1


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Execute research project pipeline")
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument("--skip-infra", action="store_true", help="Skip infrastructure tests")
    parser.add_argument("--skip-llm", action="store_true", help="Skip LLM stages")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    parser.add_argument("--core-only", action="store_true", help="Run core pipeline only (no LLM)")
    parser.add_argument(
        "--stage",
        help="Run a single stage and exit (setup, infra_tests, project_tests, analysis, render_pdf, validate, copy, llm_reviews, llm_translations, executive_report)",
    )

    args = parser.parse_args()

    if args.stage:
        return execute_single_stage(args.stage, args.project, repo_root)

    return execute_pipeline(
        project_name=args.project,
        repo_root=repo_root,
        skip_infra=args.skip_infra,
        skip_llm=args.skip_llm,
        resume=args.resume,
        core_only=args.core_only
    )


if __name__ == "__main__":
    sys.exit(main())