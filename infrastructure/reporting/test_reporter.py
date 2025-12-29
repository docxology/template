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
from typing import Dict, Any, Tuple, Optional

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


def parse_coverage_json(coverage_json_path: Path) -> Optional[Dict[str, Any]]:
    """Parse coverage.json file for detailed per-module coverage data.

    Args:
        coverage_json_path: Path to coverage.json file

    Returns:
        Dictionary with detailed coverage information by module, or None if file not found
    """
    if not coverage_json_path.exists():
        logger.debug(f"Coverage JSON file not found: {coverage_json_path}")
        return None

    try:
        with open(coverage_json_path, 'r') as f:
            coverage_data = json.load(f)

        # Extract file-level coverage information
        file_coverage = {}
        for file_path, file_data in coverage_data.get('files', {}).items():
            # Calculate coverage percentage for this file
            executed_lines = len(file_data.get('executed_lines', []))
            missing_lines = len(file_data.get('missing_lines', []))
            excluded_lines = len(file_data.get('excluded_lines', []))

            total_lines = executed_lines + missing_lines + excluded_lines
            if total_lines > 0:
                coverage_percent = (executed_lines / total_lines) * 100
            else:
                coverage_percent = 0.0

            file_coverage[file_path] = {
                'coverage_percent': coverage_percent,
                'executed_lines': executed_lines,
                'missing_lines': missing_lines,
                'excluded_lines': excluded_lines,
                'total_lines': total_lines,
            }

        # Calculate overall coverage
        total_executed = sum(data['executed_lines'] for data in file_coverage.values())
        total_missing = sum(data['missing_lines'] for data in file_coverage.values())
        total_excluded = sum(data['excluded_lines'] for data in file_coverage.values())
        total_lines = total_executed + total_missing + total_excluded

        overall_coverage = (total_executed / total_lines * 100) if total_lines > 0 else 0.0

        return {
            'overall_coverage': overall_coverage,
            'total_executed': total_executed,
            'total_missing': total_missing,
            'total_excluded': total_excluded,
            'total_lines': total_lines,
            'file_coverage': file_coverage,
        }

    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to parse coverage JSON file {coverage_json_path}: {e}")
        return None


def parse_pytest_output(stdout: str, stderr: str, exit_code: int) -> Dict[str, Any]:
    """Parse pytest output to extract comprehensive metrics.

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
        - discovery_count: Number of tests discovered during collection
        - execution_phases: Timing breakdown for collection/execution phases
        - test_categories: Breakdown by test markers/categories
    """
    results: Dict[str, Any] = {
        'passed': 0,
        'failed': 0,
        'skipped': 0,
        'total': 0,
        'warnings': 0,
        'exit_code': exit_code,
        'discovery_count': 0,
        'execution_phases': {},
        'test_categories': {},
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

    # Parse discovery count from collection output (e.g., "collected 187 items")
    discovery_match = re.search(r'collected\s+(\d+)\s+items?', stdout)
    if discovery_match:
        results['discovery_count'] = int(discovery_match.group(1))

    # Parse execution timing phases
    # Look for patterns like "test session starts", "collecting", etc.
    timing_patterns = {
        'setup': r'test session starts.*?in\s+([\d.]+)s',
        'collection': r'collecting.*?in\s+([\d.]+)s',
        'execution': r'(\d+)\s+passed.*?in\s+([\d.]+)s',
    }

    for phase, pattern in timing_patterns.items():
        match = re.search(pattern, stdout, re.DOTALL)
        if match:
            if phase == 'execution' and len(match.groups()) > 1:
                results['execution_phases'][phase] = float(match.group(2))
            elif phase != 'execution':
                results['execution_phases'][phase] = float(match.group(1))

    # Parse test categories by markers (slow, integration, requires_ollama, etc.)
    # Look for markers in the output
    marker_indicators = ['slow', 'integration', 'requires_ollama']
    for marker in marker_indicators:
        # Count occurrences of marker-related output
        marker_count = stdout.count(f'::{marker}') + stdout.count(f' - {marker}')
        if marker_count > 0:
            results['test_categories'][marker] = marker_count

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
    repo_root: Path,
    include_coverage_details: bool = True
) -> Dict[str, Any]:
    """Generate structured test report from infrastructure and project test results.

    Args:
        infra_results: Infrastructure test results dictionary
        project_results: Project test results dictionary
        repo_root: Repository root path (for metadata)
        include_coverage_details: Whether to include detailed coverage data from coverage.json

    Returns:
        Complete test report dictionary with:
        - timestamp: ISO format timestamp
        - infrastructure: Infrastructure test results
        - project: Project test results
        - summary: Combined summary with totals and pass/fail status
        - coverage_details: Detailed coverage information (if include_coverage_details=True)
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

    # Add detailed coverage information if requested
    if include_coverage_details:
        coverage_details = {}

        # Try to read infrastructure coverage details
        infra_coverage_json = repo_root / "htmlcov" / "coverage.json"
        infra_coverage = parse_coverage_json(infra_coverage_json)
        if infra_coverage:
            coverage_details['infrastructure'] = infra_coverage

        # Try to read project coverage details
        project_coverage_json = repo_root / "htmlcov" / "coverage.json"
        project_coverage = parse_coverage_json(project_coverage_json)
        if project_coverage:
            coverage_details['project'] = project_coverage

        if coverage_details:
            report['coverage_details'] = coverage_details

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
















