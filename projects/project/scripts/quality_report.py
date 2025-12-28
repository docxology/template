#!/usr/bin/env python3
"""Generate a comprehensive quality report using infrastructure modules."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure repository root is importable for infrastructure modules
repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# Try to import build modules (may not exist)
try:
    from infrastructure.build.quality_checker import analyze_document_quality
    from infrastructure.build.reproducibility import generate_reproducibility_report
    _BUILD_MODULES_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    _BUILD_MODULES_AVAILABLE = False
    # Provide stub functions
    def analyze_document_quality(path):
        return {"status": "skipped", "reason": "infrastructure.build module not available"}
    def generate_reproducibility_report(path):
        return {"status": "skipped", "reason": "infrastructure.build module not available"}

from infrastructure.validation import verify_output_integrity, validate_markdown
from infrastructure.reporting import (
    generate_pipeline_report,
    save_pipeline_report,
    get_error_aggregator,
)
from infrastructure.core.logging_utils import get_logger, log_substep


logger = get_logger(__name__)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate manuscript quality report.")
    parser.add_argument(
        "--manuscript-dir",
        type=Path,
        default=Path(__file__).parent.parent / "manuscript",
        help="Path to manuscript directory (default: project/manuscript)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output/reports"),
        help="Directory to save quality reports.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    error_agg = get_error_aggregator()

    # Markdown validation
    markdown_issues = []
    try:
        markdown_issues, _ = validate_markdown(str(args.manuscript_dir), ".")
        log_substep(f"Markdown validation: {len(markdown_issues)} issue(s)", logger)
    except Exception as exc:
        error_agg.add_error(
            error_type="validation_error",
            message=f"Markdown validation skipped: {exc}",
            stage="quality_report",
            severity="warning",
        )

    # Quality analysis
    quality_metrics = {}
    if not _BUILD_MODULES_AVAILABLE:
        log_substep("Quality metrics: skipped (build modules not available)", logger)
        quality_metrics = {"status": "skipped", "reason": "infrastructure.build not available"}
    else:
        try:
            quality_metrics = analyze_document_quality(args.manuscript_dir)
            log_substep("Quality metrics: computed", logger)
        except Exception as exc:
            error_agg.add_error(
                error_type="quality_error",
                message=f"Quality metrics skipped: {exc}",
                stage="quality_report",
                severity="warning",
            )

    # Output integrity
    integrity_summary = {}
    try:
        integrity_summary = verify_output_integrity(Path("output"))
        integrity_summary = json.loads(json.dumps(integrity_summary, default=str))
        log_substep("Output integrity: completed", logger)
    except Exception as exc:
        error_agg.add_error(
            error_type="validation_error",
            message=f"Output integrity warning: {exc}",
            stage="quality_report",
            severity="warning",
        )

    # Reproducibility
    reproducibility = {}
    if not _BUILD_MODULES_AVAILABLE:
        log_substep("Reproducibility: skipped (build modules not available)", logger)
        reproducibility = {"status": "skipped", "reason": "infrastructure.build not available"}
    else:
        try:
            reproducibility = generate_reproducibility_report(Path("output"))
            reproducibility = json.loads(json.dumps(reproducibility, default=str))
        except Exception:
            reproducibility = {}

    # Aggregate and persist
    summary = {
        "markdown_issues": markdown_issues,
        "quality_metrics": quality_metrics,
        "integrity_summary": integrity_summary,
        "reproducibility": reproducibility,
        "errors": error_agg.get_summary(),
    }

    json_path = args.output_dir / "quality_report.json"
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # Save pipeline-style report for consistency
    report = generate_pipeline_report(
        stage_results=[
            {"name": "quality_report", "exit_code": 0, "duration": 0.0},
        ],
        total_duration=0.0,
        repo_root=Path("."),
        validation_results=summary,
        error_summary=summary["errors"],
    )
    save_pipeline_report(report, args.output_dir)

    print(f"✅ Quality report generated at {json_path}")


if __name__ == "__main__":
    main()

