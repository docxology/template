#!/usr/bin/env python3
"""Ento-Linguistic analysis pipeline orchestrator.

This script orchestrates the complete Ento-Linguistic analysis workflow:
1. Literature mining and corpus collection
2. Terminology extraction and domain classification
3. Conceptual mapping and network analysis
4. Domain-specific analysis across all six domains
5. Discourse analysis and rhetorical patterns
6. Visualization generation and reporting

IMPORTANT: This script follows the thin orchestrator pattern - all business
logic is in src/ modules, this script only orchestrates the workflow.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure src/ and repo root are on path
project_root = Path(__file__).parent.parent
repo_root = project_root.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(repo_root))

# Local logging
from src.utils.logging import (get_logger, log_progress_bar, log_stage,
                               log_substep)
from src.utils.reporting import (generate_pipeline_report,
                                 get_error_aggregator, save_pipeline_report)
from src.utils.validation import verify_output_integrity

logger = get_logger(__name__)


def _parse_args() -> argparse.Namespace:
    """Parse CLI arguments for Ento-Linguistic analysis pipeline."""
    parser = argparse.ArgumentParser(
        description="Ento-Linguistic Analysis Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run complete analysis pipeline
  python3 scripts/analysis_pipeline.py

  # Run specific stages
  python3 scripts/analysis_pipeline.py --stages literature terminology

  # Dry run to see what would be executed
  python3 scripts/analysis_pipeline.py --dry-run

  # Run with custom corpus
  python3 scripts/analysis_pipeline.py --corpus-file /path/to/corpus.json
        """,
    )

    # Define analysis stages
    stage_names = [
        "literature_mining",
        "terminology_extraction",
        "conceptual_mapping",
        "domain_analysis",
        "discourse_analysis",
        "visualization",
        "reporting",
    ]

    parser.add_argument(
        "--stages",
        nargs="+",
        choices=stage_names + ["all"],
        default=["all"],
        help="Run specific stages or 'all' for complete pipeline.",
    )
    parser.add_argument(
        "--corpus-file",
        type=Path,
        help="Path to literature corpus JSON file (default: auto-detect).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be executed without running.",
    )
    parser.add_argument(
        "--list-stages",
        action="store_true",
        help="List available stages and exit.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Custom output directory.",
    )

    return parser.parse_args(), stage_names


# Import local utilities
from src.utils.figure_manager import FigureManager

# Directory creation handled inline

logger.info("Ento-Linguistic Analysis Pipeline initialized")


def run_analysis_stage(
    stage_name: str,
    corpus_file: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> bool:
    """Run a specific Ento-Linguistic analysis stage.

    Args:
        stage_name: Name of the analysis stage to run (must be a valid stage name)
        corpus_file: Optional path to literature corpus file for stages that need it
        output_dir: Optional custom output directory
        dry_run: If True, only show what would be executed without running

    Returns:
        True if stage completed successfully, False otherwise

    Raises:
        No exceptions are raised directly, but subprocess failures are logged

    Example:
        >>> success = run_analysis_stage("literature_mining", dry_run=True)
        >>> print(f"Stage would {'succeed' if success else 'fail'}")
    """
    logger.debug(
        f"run_analysis_stage() entry: stage_name={stage_name}, corpus_file={corpus_file}, output_dir={output_dir}, dry_run={dry_run}"
    )

    script_commands = {
        "literature_mining": [
            sys.executable,
            "scripts/literature_analysis_pipeline.py",
            "--max-publications",
            "500",
        ],
        "terminology_extraction": [
            sys.executable,
            "scripts/literature_analysis_pipeline.py",
            "--max-publications",
            "500",
        ],
        "conceptual_mapping": [sys.executable, "scripts/conceptual_mapping_script.py"],
        "domain_analysis": [sys.executable, "scripts/domain_analysis_script.py", "all"],
        "discourse_analysis": [sys.executable, "scripts/discourse_analysis_script.py"],
        "visualization": [sys.executable, "scripts/generate_domain_figures.py", "all"],
        "reporting": [
            sys.executable,
            "scripts/literature_analysis_pipeline.py",
            "--max-publications",
            "500",
        ],
    }

    # Validate inputs
    if stage_name not in script_commands:
        error_msg = f"Unknown stage: {stage_name}"
        logger.error(error_msg)
        logger.error(f"Available stages: {list(script_commands.keys())}")
        logger.error(
            "Suggestion: Use one of the available stage names, or 'all' to run all stages"
        )
        return False

    command = script_commands[stage_name]

    # Add corpus file if specified
    if corpus_file and stage_name in [
        "literature_mining",
        "terminology_extraction",
        "conceptual_mapping",
    ]:
        command.extend(["--corpus-file", str(corpus_file)])

    # Add output directory if specified
    if output_dir:
        command.extend(["--output-dir", str(output_dir)])

    if dry_run:
        logger.info(f"[DRY RUN] Would execute: {' '.join(command)}")
        logger.debug(f"run_analysis_stage() exit: dry_run=True, returning True")
        return True

    try:
        log_substep(f"Running {stage_name} stage", logger)
        result = subprocess.run(
            command, cwd=project_root, capture_output=True, text=True
        )

        if result.returncode == 0:
            log_substep(f"✅ {stage_name} completed successfully", logger)
            if result.stdout:
                logger.info(f"Output: {result.stdout.strip()}")
            logger.debug(
                f"run_analysis_stage() exit: success, returncode={result.returncode}"
            )
            return True
        else:
            log_substep(f"❌ {stage_name} failed with code {result.returncode}", logger)
            if result.stderr:
                logger.error(f"Error: {result.stderr.strip()}")
            logger.debug(
                f"run_analysis_stage() exit: failure, returncode={result.returncode}"
            )
            return False

    except Exception as e:
        logger.exception(f"❌ {stage_name} failed with exception")
        log_substep(f"Stage execution failed: {e}", logger)
        logger.debug(f"run_analysis_stage() exit: exception occurred")
        return False


def main() -> None:
    """Main entry point for Ento-Linguistic analysis pipeline."""
    args, stage_names = _parse_args()

    if args.list_stages:
        logger.info("Available analysis stages:")
        for i, stage in enumerate(stage_names, 1):
            logger.info(f"  {i}. {stage}")
        return

    # Determine which stages to run
    if "all" in args.stages:
        stages_to_run = stage_names
    else:
        stages_to_run = args.stages

    logger.info(f"Ento-Linguistic Analysis Pipeline starting")
    logger.info(f"Stages to run: {', '.join(stages_to_run)}")

    if args.dry_run:
        logger.info("DRY RUN MODE - No actual execution")

    # Ensure output directories exist
    output_dir = args.output_dir or project_root / "output"
    (output_dir / "data").mkdir(parents=True, exist_ok=True)
    (output_dir / "figures").mkdir(parents=True, exist_ok=True)
    (output_dir / "reports").mkdir(parents=True, exist_ok=True)

    # Run stages
    results = {}
    failed_stages = []

    for stage in stages_to_run:
        success = run_analysis_stage(
            stage,
            corpus_file=args.corpus_file,
            output_dir=output_dir,
            dry_run=args.dry_run,
        )

        results[stage] = "success" if success else "failed"
        if not success:
            failed_stages.append(stage)

    # Summary
    successful_stages = [s for s, r in results.items() if r == "success"]
    failed_count = len(failed_stages)

    if not args.dry_run:
        logger.info(f"\n{'='*60}")
        logger.info("ENTO-LINGUISTIC ANALYSIS PIPELINE RESULTS")
        logger.info(f"{'='*60}")
        logger.info(f"Total stages: {len(stages_to_run)}")
        logger.info(f"Successful: {len(successful_stages)}")
        logger.info(f"Failed: {failed_count}")

        if successful_stages:
            logger.info(f"Completed stages: {', '.join(successful_stages)}")

        if failed_stages:
            logger.error(f"Failed stages: {', '.join(failed_stages)}")
            logger.error("Check logs for error details")

        if failed_count == 0:
            logger.info("🎉 All stages completed successfully!")
            logger.info(f"Output directory: {output_dir}")
        else:
            logger.error(f"❌ {failed_count} stage(s) failed")
            sys.exit(1)
    else:
        logger.info(f"\nDry run complete - would execute {len(stages_to_run)} stages")


if __name__ == "__main__":
    main()
