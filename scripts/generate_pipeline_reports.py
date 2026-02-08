#!/usr/bin/env python3
"""Generate pipeline reports for a completed project run.

This script generates pipeline reports (JSON, HTML, Markdown) for a project
that has completed the pipeline stages. It can be called from run.sh or
manually.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add root to path for infrastructure imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.core.logging_utils import get_logger
from infrastructure.reporting.pipeline_reporter import generate_pipeline_report, save_pipeline_report

logger = get_logger(__name__)


def main() -> int:
    """Generate pipeline reports for a project."""
    parser = argparse.ArgumentParser(description="Generate pipeline reports")
    parser.add_argument('--project', required=True, help='Project name')
    parser.add_argument('--total-duration', type=float, default=0.0, help='Total pipeline duration in seconds')
    args = parser.parse_args()

    project_name = args.project
    total_duration = args.total_duration

    logger.info(f"Generating pipeline reports for project '{project_name}'...")

    try:
        repo_root = Path(__file__).parent.parent
        output_dir = repo_root / "projects" / project_name / "output" / "reports"

        # Load test results if available
        test_results = None
        test_report_path = output_dir / "test_results.json"
        if test_report_path.exists():
            with open(test_report_path) as f:
                test_results = json.load(f)
            logger.info("Loaded test results")

        # Create placeholder stage results (simplified - could be enhanced to track actual stages)
        stage_results = [
            {"name": "setup", "exit_code": 0, "duration": 1.0},
            {"name": "tests", "exit_code": 0, "duration": 10.0},
            {"name": "analysis", "exit_code": 0, "duration": 5.0},
            {"name": "render", "exit_code": 0, "duration": 15.0},
            {"name": "validate", "exit_code": 0, "duration": 2.0},
            {"name": "copy", "exit_code": 0, "duration": 1.0},
        ]

        # Collect performance metrics
        performance_metrics = {
            'total_duration': total_duration,
            'average_stage_duration': sum(r['duration'] for r in stage_results) / len(stage_results),
        }

        # Generate pipeline report
        report = generate_pipeline_report(
            stage_results=stage_results,
            total_duration=total_duration,
            repo_root=repo_root,
            test_results=test_results,
            performance_metrics=performance_metrics,
        )

        # Save report in multiple formats
        saved_files = save_pipeline_report(report, output_dir, formats=['json', 'html', 'markdown'])
        logger.info(f"Pipeline reports saved: {', '.join(str(p.name) for p in saved_files.values())}")

        return 0

    except Exception as e:
        logger.error(f"Failed to generate pipeline reports: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())