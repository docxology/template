"""Test reporting module - Parse test output and generate test reports.

This module provides utilities for parsing pytest output and generating
structured test reports. Part of the infrastructure layer (Layer 1) - 
reusable across all projects.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


def parse_pytest_output(stdout: str, stderr: str, exit_code: int) -> Dict[str, Any]:
    """Parse pytest output to extract metrics.
    
    Args:
        stdout: Standard output from pytest
        stderr: Standard error from pytest
        exit_code: Exit code from pytest
        
    Returns:
        Dictionary with test metrics including:
        - passed: Number of passed tests
        - failed: Number of failed tests
        - skipped: Number of skipped tests
        - total: Total number of tests
        - warnings: Number of warnings
        - exit_code: Exit code from pytest
        - coverage_percent: Coverage percentage (if present)
    """
    results: Dict[str, Any] = {
        'passed': 0,
        'failed': 0,
        'skipped': 0,
        'total': 0,
        'warnings': 0,
        'exit_code': exit_code,
    }
    
    # Parse summary line (e.g., "1747 passed, 2 skipped, 41 deselected in 37.59s")
    summary_pattern = r'(\d+)\s+passed|(\d+)\s+failed|(\d+)\s+skipped|(\d+)\s+deselected'
    for match in re.finditer(summary_pattern, stdout):
        if match.group(1):  # passed
            results['passed'] = int(match.group(1))
        elif match.group(2):  # failed
            results['failed'] = int(match.group(2))
        elif match.group(3):  # skipped
            results['skipped'] = int(match.group(3))
    
    results['total'] = results['passed'] + results['failed'] + results['skipped']
    
    # Count warnings
    results['warnings'] = stdout.count(' warning') + stderr.count(' warning')
    
    # Parse coverage if present
    coverage_match = re.search(r'(\d+\.\d+)%', stdout)
    if coverage_match:
        results['coverage_percent'] = float(coverage_match.group(1))
    
    return results


def generate_test_report(
    infra_results: Dict[str, Any],
    project_results: Dict[str, Any],
    repo_root: Path
) -> Dict[str, Any]:
    """Generate structured test report from infrastructure and project test results.
    
    Args:
        infra_results: Infrastructure test results dictionary
        project_results: Project test results dictionary
        repo_root: Repository root path (for metadata)
        
    Returns:
        Complete test report dictionary with:
        - timestamp: ISO format timestamp
        - infrastructure: Infrastructure test results
        - project: Project test results
        - summary: Combined summary with totals and pass/fail status
    """
    report: Dict[str, Any] = {
        'timestamp': datetime.now().isoformat(),
        'infrastructure': infra_results,
        'project': project_results,
        'summary': {
            'total_passed': infra_results.get('passed', 0) + project_results.get('passed', 0),
            'total_failed': infra_results.get('failed', 0) + project_results.get('failed', 0),
            'total_skipped': infra_results.get('skipped', 0) + project_results.get('skipped', 0),
            'total_tests': infra_results.get('total', 0) + project_results.get('total', 0),
            'all_passed': (infra_results.get('exit_code', 1) == 0 and 
                          project_results.get('exit_code', 1) == 0),
        }
    }
    
    # Add coverage summary
    if 'coverage_percent' in infra_results:
        report['summary']['infrastructure_coverage'] = infra_results['coverage_percent']
    if 'coverage_percent' in project_results:
        report['summary']['project_coverage'] = project_results['coverage_percent']
    
    return report


def save_test_report(report: Dict[str, Any], output_dir: Path) -> Tuple[Path, Path]:
    """Save test report to JSON and generate Markdown summary.
    
    Args:
        report: Test report dictionary
        output_dir: Output directory path (will be created if needed)
        
    Returns:
        Tuple of (json_path, md_path) for the saved files
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save JSON report
    json_path = output_dir / "test_results.json"
    with open(json_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Test report saved: {json_path}")
    
    # Generate markdown summary
    md_path = output_dir / "test_results.md"
    with open(md_path, 'w') as f:
        f.write("# Test Results Summary\n\n")
        f.write(f"Generated: {report['timestamp']}\n\n")
        f.write("## Infrastructure Tests\n\n")
        f.write(f"- Passed: {report['infrastructure'].get('passed', 0)}\n")
        f.write(f"- Failed: {report['infrastructure'].get('failed', 0)}\n")
        f.write(f"- Skipped: {report['infrastructure'].get('skipped', 0)}\n")
        if 'coverage_percent' in report['infrastructure']:
            f.write(f"- Coverage: {report['infrastructure']['coverage_percent']:.2f}%\n")
        f.write("\n## Project Tests\n\n")
        f.write(f"- Passed: {report['project'].get('passed', 0)}\n")
        f.write(f"- Failed: {report['project'].get('failed', 0)}\n")
        f.write(f"- Skipped: {report['project'].get('skipped', 0)}\n")
        if 'coverage_percent' in report['project']:
            f.write(f"- Coverage: {report['project']['coverage_percent']:.2f}%\n")
        f.write("\n## Summary\n\n")
        f.write(f"- Total Passed: {report['summary']['total_passed']}\n")
        f.write(f"- Total Failed: {report['summary']['total_failed']}\n")
        f.write(f"- Total Tests: {report['summary']['total_tests']}\n")
        f.write(f"- Status: {'✅ PASSED' if report['summary']['all_passed'] else '❌ FAILED'}\n")
    
    logger.info(f"Test summary saved: {md_path}")
    
    return (json_path, md_path)












