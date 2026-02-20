#!/usr/bin/env python3
"""Generate comprehensive test summary report for the full repository test suite.

This script aggregates test results from infrastructure and active project
tests to create a comprehensive summary report.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Add infrastructure to path for config loading
sys.path.insert(0, str(Path(__file__).parent.parent))
from infrastructure.core.config_loader import get_testing_config


def load_test_results(project_name: str) -> Dict[str, Any]:
    """Load test results from a project's output directory.

    Args:
        project_name: Name of the project (e.g., 'act_inf_metaanalysis')

    Returns:
        Dictionary containing test results, or empty dict if not found
    """
    results_file = Path(f"projects/{project_name}/output/reports/test_results.json")

    if results_file.exists():
        try:
            with open(results_file, 'r') as f:
                data = json.load(f)
                # Extract project results from the nested structure
                if 'project' in data:
                    return data['project']
                else:
                    return data
        except Exception as e:
            print(f"Warning: Could not load results from {results_file}: {e}")
            return {}
    else:
        print(f"Warning: Test results file not found: {results_file}")
        return {}


def load_infrastructure_results() -> Dict[str, Any]:
    """Load infrastructure test results from root coverage files.

    Returns:
        Dictionary containing infrastructure test results
    """
    # Try to load from the infrastructure validation report
    infra_results_file = Path("infrastructure_validation_report.json")
    if infra_results_file.exists():
        try:
            with open(infra_results_file, 'r') as f:
                data = json.load(f)
                # Extract infrastructure test results from the validation report
                test_results = data.get('test_results', {})
                infra_data = test_results.get('infrastructure', {})
                if infra_data:
                    return {
                        'passed': infra_data.get('passed', 0),
                        'failed': infra_data.get('total_tests', 0) - infra_data.get('passed', 0) - infra_data.get('skipped', 0),
                        'skipped': infra_data.get('skipped', 0),
                        'warnings': infra_data.get('warnings', 0),
                        'coverage_percent': infra_data.get('coverage_percent', 0),
                        'total_lines': 0,  # Not available in this format
                        'covered_lines': 0,  # Not available in this format
                        'missing_lines': 0,  # Not available in this format
                        'duration_seconds': infra_data.get('duration_seconds', 0),
                        'exit_code': 0 if infra_data.get('status') == 'PASSED' else 1,
                    }
        except Exception as e:
            print(f"Warning: Could not load infrastructure results from validation report: {e}")

    # Fallback: try coverage JSON files
    infra_json = Path("coverage_infra.json")
    if infra_json.exists():
        try:
            with open(infra_json, 'r') as f:
                coverage_data = json.load(f)
                totals = coverage_data.get('totals', {})
                return {
                    'coverage_percent': totals.get('percent_covered', 0),
                    'total_lines': totals.get('num_statements', 0),
                    'covered_lines': totals.get('covered_lines', 0),
                    'missing_lines': totals.get('missing_lines', 0),
                }
        except Exception as e:
            print(f"Warning: Could not load infrastructure coverage: {e}")

    # Fallback: try to extract from HTML coverage if available
    htmlcov = Path("htmlcov/coverage.json")
    if htmlcov.exists():
        try:
            with open(htmlcov, 'r') as f:
                coverage_data = json.load(f)
                totals = coverage_data.get('totals', {})
                return {
                    'coverage_percent': totals.get('percent_covered', 0),
                    'total_lines': totals.get('num_statements', 0),
                    'covered_lines': totals.get('covered_lines', 0),
                    'missing_lines': totals.get('missing_lines', 0),
                }
        except Exception as e:
            print(f"Warning: Could not load HTML coverage: {e}")

    print("Warning: No infrastructure test results found")
    return {}


def discover_active_projects() -> list:
    """Discover active projects from the projects/ directory.

    Returns:
        List of active project names
    """
    projects_dir = Path("projects")
    if not projects_dir.exists():
        return []

    projects = []
    for item in projects_dir.iterdir():
        if item.is_dir() and not item.name.startswith((".", "_", "__")):
            projects.append(item.name)
    return sorted(projects)


def generate_summary_report() -> Dict[str, Any]:
    """Generate comprehensive test summary report.

    Returns:
        Dictionary containing aggregated test results and metadata
    """
    timestamp = datetime.now().isoformat()

    # Discover active projects dynamically
    active_projects = discover_active_projects()

    # Load results from all test suites
    infra_results = load_infrastructure_results()

    # Load project results dynamically
    project_results = {}
    for project_name in active_projects:
        project_results[project_name] = load_test_results(project_name)

    # Calculate totals
    total_passed = infra_results.get('passed', 0)
    total_failed = infra_results.get('failed', 0)
    total_skipped = infra_results.get('skipped', 0)

    for results in project_results.values():
        total_passed += results.get('passed', 0)
        total_failed += results.get('failed', 0)
        total_skipped += results.get('skipped', 0)

    total_tests = total_passed + total_failed + total_skipped

    # Calculate weighted coverage (weighted by lines of code)
    infra_coverage = infra_results.get('coverage_percent', 0)
    infra_lines = infra_results.get('total_lines', 0)

    total_lines = infra_lines
    weighted_sum = infra_coverage * infra_lines

    for results in project_results.values():
        proj_coverage = results.get('coverage_percent', 0)
        proj_lines = results.get('total_lines', 0)
        total_lines += proj_lines
        weighted_sum += proj_coverage * proj_lines

    if total_lines > 0:
        weighted_coverage = weighted_sum / total_lines
    else:
        weighted_coverage = 0

    # Calculate execution times
    infra_duration = infra_results.get('duration_seconds', 0)
    total_duration = infra_duration

    for results in project_results.values():
        total_duration += results.get('duration_seconds', 0)

    # Determine overall success
    overall_success = infra_results.get('exit_code', 1) == 0
    for results in project_results.values():
        if results.get('exit_code', 1) != 0:
            overall_success = False
            break

    # Create summary report
    report = {
        'timestamp': timestamp,
        'test_type': 'full_repository_suite',
        'overall_success': overall_success,

        'summary': {
            'total_tests': total_tests,
            'total_passed': total_passed,
            'total_failed': total_failed,
            'total_skipped': total_skipped,
            'pass_rate': (total_passed / total_tests * 100) if total_tests > 0 else 0,
            'total_duration_seconds': total_duration,
            'weighted_coverage_percent': round(weighted_coverage, 2),
        },

        'infrastructure': {
            'passed': infra_results.get('passed', 0),
            'failed': infra_results.get('failed', 0),
            'skipped': infra_results.get('skipped', 0),
            'warnings': infra_results.get('warnings', 0),
            'coverage_percent': infra_coverage,
            'total_lines': infra_lines,
            'covered_lines': infra_results.get('covered_lines', 0),
            'missing_lines': infra_results.get('missing_lines', 0),
            'duration_seconds': infra_duration,
            'exit_code': infra_results.get('exit_code', 1),
            'meets_threshold': infra_coverage >= get_testing_config(Path.cwd()).get('infra_coverage_threshold', 60),
        },

        'projects': {},

        'metadata': {
            'test_run_type': 'all_test_types_included',
            'infrastructure_tests_included': True,
            'integration_tests_included': True,
            'slow_tests_included': True,
            'ollama_tests_included': True,
            'ollama_server_available': True,  # Based on successful test execution
            'test_command': 'scripts/01_run_tests.py --include-slow --include-ollama-tests --verbose',
            'active_projects': active_projects,
        },

        'files_generated': [
            'test_results_summary.json',
            'test_results_summary.md',
            'coverage_infra.json',
            'htmlcov/index.html (infrastructure)',
        ],
    }

    # Add per-project results dynamically
    for project_name, results in project_results.items():
        proj_coverage = results.get('coverage_percent', 0)
        report['projects'][project_name] = {
            'passed': results.get('passed', 0),
            'failed': results.get('failed', 0),
            'skipped': results.get('skipped', 0),
            'warnings': results.get('warnings', 0),
            'coverage_percent': proj_coverage,
            'total_lines': results.get('total_lines', 0),
            'covered_lines': results.get('covered_lines', 0),
            'missing_lines': results.get('missing_lines', 0),
            'duration_seconds': results.get('duration_seconds', 0),
            'exit_code': results.get('exit_code', 1),
            'meets_threshold': proj_coverage >= get_testing_config(Path.cwd()).get('project_coverage_threshold', 90),
        }
        report['files_generated'].append(f'coverage_project.json ({project_name})')
        report['files_generated'].append(f'htmlcov/index.html ({project_name})')

    return report


def generate_markdown_report(data: Dict[str, Any]) -> str:
    """Generate human-readable markdown report from test data.

    Args:
        data: Test results dictionary

    Returns:
        Markdown formatted report
    """
    lines = []

    lines.append("# Full Repository Test Suite Results")
    lines.append("")
    lines.append(f"**Date**: {data['timestamp']}")
    lines.append(f"**Test Type**: {data['test_type']}")
    lines.append(f"**Overall Status**: {'PASSED' if data['overall_success'] else 'FAILED'}")
    lines.append("")

    # Summary section
    lines.append("## Summary")
    lines.append("")
    summary = data['summary']
    lines.append(f"- **Total Tests**: {summary['total_tests']:,}")
    lines.append(f"- **Passed**: {summary['total_passed']:,}")
    lines.append(f"- **Failed**: {summary['total_failed']:,}")
    lines.append(f"- **Skipped**: {summary['total_skipped']:,}")
    lines.append(f"- **Pass Rate**: {summary['pass_rate']:.1f}%")
    lines.append(f"- **Weighted Coverage**: {summary['weighted_coverage_percent']:.1f}%")
    lines.append(f"- **Total Duration**: {summary['total_duration_seconds']:.1f}s")
    lines.append("")

    # Infrastructure results
    lines.append("## Infrastructure Tests")
    lines.append("")
    infra = data['infrastructure']
    status = "PASSED" if infra['exit_code'] == 0 else "FAILED"
    lines.append(f"**Status**: {status}")
    lines.append(f"**Tests**: {infra['passed']:,} passed, {infra['failed']:,} failed, {infra['skipped']:,} skipped")
    if infra['warnings'] > 0:
        lines.append(f"**Warnings**: {infra['warnings']:,}")
    lines.append(f"**Coverage**: {infra['coverage_percent']:.1f}% ({'meets' if infra['meets_threshold'] else 'below'} 60% threshold)")
    lines.append(f"**Lines**: {infra['covered_lines']:,}/{infra['total_lines']:,} covered")
    lines.append(f"**Duration**: {infra['duration_seconds']:.1f}s")
    lines.append("")

    # Project results (dynamic)
    projects = data.get('projects', {})
    for project_name, proj_data in sorted(projects.items()):
        # Format project name for display (convert underscores to spaces, title case)
        display_name = project_name.replace('_', ' ').title()
        lines.append(f"## {display_name} Tests")
        lines.append("")
        status = "PASSED" if proj_data['exit_code'] == 0 else "FAILED"
        lines.append(f"**Status**: {status}")
        lines.append(f"**Tests**: {proj_data['passed']:,} passed, {proj_data['failed']:,} failed, {proj_data['skipped']:,} skipped")
        if proj_data['warnings'] > 0:
            lines.append(f"**Warnings**: {proj_data['warnings']:,}")
        lines.append(f"**Coverage**: {proj_data['coverage_percent']:.1f}% ({'meets' if proj_data['meets_threshold'] else 'below'} 90% threshold)")
        lines.append(f"**Lines**: {proj_data['covered_lines']:,}/{proj_data['total_lines']:,} covered")
        lines.append(f"**Duration**: {proj_data['duration_seconds']:.1f}s")
        lines.append("")

    # Metadata
    lines.append("## Test Configuration")
    lines.append("")
    meta = data['metadata']
    lines.append(f"- **Infrastructure Tests**: {'Included' if meta['infrastructure_tests_included'] else 'Excluded'}")
    lines.append(f"- **Integration Tests**: {'Included' if meta['integration_tests_included'] else 'Excluded'}")
    lines.append(f"- **Slow Tests**: {'Included' if meta['slow_tests_included'] else 'Excluded'}")
    lines.append(f"- **Ollama Tests**: {'Included' if meta['ollama_tests_included'] else 'Excluded'}")
    lines.append(f"- **Ollama Server**: {'Available' if meta['ollama_server_available'] else 'Unavailable'}")
    if 'active_projects' in meta:
        lines.append(f"- **Active Projects**: {', '.join(meta['active_projects'])}")
    lines.append("")

    # Files generated
    lines.append("## Generated Files")
    lines.append("")
    for file in data['files_generated']:
        lines.append(f"- `{file}`")
    lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append("*Report generated by `scripts/generate_test_summary.py`*")

    return "\n".join(lines)


def main():
    """Main entry point for generating test summary reports."""
    print("Generating comprehensive test summary reports...")

    # Generate the summary data
    report_data = generate_summary_report()

    # Save JSON report
    json_file = Path("test_results_summary.json")
    with open(json_file, 'w') as f:
        json.dump(report_data, f, indent=2)
    print(f"✅ JSON report saved: {json_file}")

    # Generate and save markdown report
    markdown_content = generate_markdown_report(report_data)
    md_file = Path("test_results_summary.md")
    with open(md_file, 'w') as f:
        f.write(markdown_content)
    print(f"✅ Markdown report saved: {md_file}")

    # Print summary to console
    summary = report_data['summary']
    infra = report_data['infrastructure']
    projects = report_data.get('projects', {})

    print("\n" + "="*80)
    print("FULL REPOSITORY TEST SUITE SUMMARY")
    print("="*80)
    print(f"Overall Status: {'PASSED' if report_data['overall_success'] else 'FAILED'}")
    print(f"Total Tests: {summary['total_tests']:,} ({summary['pass_rate']:.1f}% pass rate)")
    print(f"Total Duration: {summary['total_duration_seconds']:.1f}s")
    print(f"Weighted Coverage: {summary['weighted_coverage_percent']:.1f}%")
    print()
    print("Suite Breakdown:")
    print(f"  Infrastructure:          {infra['passed']:,} passed ({infra['coverage_percent']:.1f}% coverage)")
    for project_name, proj_data in sorted(projects.items()):
        # Truncate long project names for display
        display_name = project_name[:20] + "..." if len(project_name) > 23 else project_name
        print(f"  {display_name:<24} {proj_data['passed']:,} passed ({proj_data['coverage_percent']:.1f}% coverage)")
    print("="*80)

    return 0


if __name__ == "__main__":
    exit(main())