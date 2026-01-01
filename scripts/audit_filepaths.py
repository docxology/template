#!/usr/bin/env python3
"""Thin orchestrator for comprehensive filepath and reference audit.

This script coordinates audit operations using modular infrastructure validation modules.
It provides a unified interface for auditing filepaths, references, and documentation accuracy.

Usage:
    python scripts/audit_filepaths.py [--output OUTPUT_FILE] [--format FORMAT] [--verbose]

Options:
    --output OUTPUT_FILE    Save report to specified file (default: docs/audit/FILEPATH_AUDIT_REPORT.md)
    --format FORMAT         Output format: 'markdown' or 'json' (default: markdown)
    --verbose              Show detailed progress information
    --project PROJECT      Audit specific project only (default: all projects)

Examples:
    python scripts/audit_filepaths.py
    python scripts/audit_filepaths.py --output my_audit.md --verbose
    python scripts/audit_filepaths.py --format json --output audit.json
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add root to path for infrastructure imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.core.logging_utils import get_logger, setup_logger
from infrastructure.validation.audit_orchestrator import (
    run_comprehensive_audit,
    generate_audit_report
)

logger = get_logger(__name__)

def main():
    """Main entry point for the audit script."""
    parser = argparse.ArgumentParser(
        description="Comprehensive audit of filepaths and references in documentation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/audit_filepaths.py
  python scripts/audit_filepaths.py --output docs/audit/my_audit.md --verbose
  python scripts/audit_filepaths.py --format json --output audit_results.json
  python scripts/audit_filepaths.py --project project
        """
    )

    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=Path('docs/audit/FILEPATH_AUDIT_REPORT.md'),
        help='Output file for the audit report'
    )

    parser.add_argument(
        '--format', '-f',
        choices=['markdown', 'json'],
        default='markdown',
        help='Output format for the report'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed progress information'
    )

    parser.add_argument(
        '--project',
        help='Audit specific project only (default: all projects)'
    )

    args = parser.parse_args()

    # Set up logging
    if args.verbose:
        setup_logger(__name__, level=10)  # DEBUG level

    # Find repository root
    repo_root = Path(__file__).parent.parent

    try:
        # Run comprehensive audit using orchestrator
        logger.info("🔍 Starting comprehensive filepath and reference audit...")
        scan_results = run_comprehensive_audit(
            repo_root,
            verbose=args.verbose,
            include_code_validation=True,
            include_directory_validation=True,
            include_import_validation=True,
            include_placeholder_validation=True
        )

        # Generate and save report
        logger.info("📊 Generating audit report...")
        report = generate_audit_report(scan_results, args.format)

        # Ensure output directory exists
        args.output.parent.mkdir(parents=True, exist_ok=True)

        # Save report
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)

        # Print summary to console
        total_issues = sum(scan_results.statistics.values())

        print("\n" + "="*80)
        print("AUDIT COMPLETE")
        print("="*80)
        print(f"Files scanned: {scan_results.scanned_files}")
        print(f"Issues found: {total_issues}")
        print(f"Duration: {scan_results.scan_duration:.2f}s")
        print(f"Report saved: {args.output}")

        if total_issues > 0:
            print("\n🚨 Issues found by category:")
            for category, count in scan_results.statistics.items():
                if count > 0:
                    print(f"   • {category.replace('_', ' ').title()}: {count}")

        # Exit with appropriate code
        sys.exit(0 if total_issues == 0 else 1)

    except Exception as e:
        logger.error(f"Audit failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point for the audit script."""
    parser = argparse.ArgumentParser(
        description="Comprehensive audit of filepaths and references in documentation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/audit_filepaths.py
  python scripts/audit_filepaths.py --output docs/audit/my_report.md --verbose
  python scripts/audit_filepaths.py --fix
        """
    )

    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=Path('docs/audit/FILEPATH_AUDIT_REPORT.md'),
        help='Output file for the audit report'
    )

    parser.add_argument(
        '--format', '-f',
        choices=['markdown', 'json'],
        default='markdown',
        help='Output format for the report'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed progress information'
    )

    parser.add_argument(
        '--project',
        help='Audit specific project only (default: all projects)'
    )

    args = parser.parse_args()

    # Set up logging
    if args.verbose:
        setup_logger(__name__, level=10)  # DEBUG level

    # Find repository root
    repo_root = Path(__file__).parent.parent

    try:
        # Run comprehensive audit using orchestrator
        logger.info("🔍 Starting comprehensive filepath and reference audit...")
        scan_results = run_comprehensive_audit(
            repo_root,
            verbose=args.verbose,
            include_code_validation=True,
            include_directory_validation=True,
            include_import_validation=True,
            include_placeholder_validation=True
        )

        # Generate and save report
        logger.info("📊 Generating audit report...")
        report = generate_audit_report(scan_results, args.format)

        # Ensure output directory exists
        args.output.parent.mkdir(parents=True, exist_ok=True)

        # Save report
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)

        # Print summary to console
        total_issues = sum(scan_results.statistics.values())

        print("\n" + "="*80)
        print("AUDIT COMPLETE")
        print("="*80)
        print(f"Files scanned: {scan_results.scanned_files}")
        print(f"Issues found: {total_issues}")
        print(f"Duration: {scan_results.scan_duration:.2f}s")
        print(f"Report saved: {args.output}")

        if total_issues > 0:
            print("\n🚨 Issues found by category:")
            for category, count in scan_results.statistics.items():
                if count > 0:
                    print(f"   • {category.replace('_', ' ').title()}: {count}")

        # Exit with appropriate code
        sys.exit(0 if total_issues == 0 else 1)

    except Exception as e:
        logger.error(f"Audit failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()