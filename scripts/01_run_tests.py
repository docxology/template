#!/usr/bin/env python3
"""Test suite orchestrator script.

This thin orchestrator runs the complete test suite for the project:
1. Runs infrastructure tests with 49%+ coverage
2. Runs project tests with 70%+ coverage
3. Reports test results
4. Validates test infrastructure

Stage 01 of the pipeline orchestration.

Note: For separate infrastructure/project test runs, use ./run.sh which
provides an interactive menu with options 1 (infrastructure) and 2 (project).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Add root to path for infrastructure imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.core.logging_utils import (
    get_logger, log_success, log_header, log_substep, log_with_spinner
)

# Set up logger for this module
logger = get_logger(__name__)


def run_infrastructure_tests(repo_root: Path, quiet: bool = True) -> tuple[int, dict]:
    """Execute infrastructure test suite with coverage.
    
    Args:
        repo_root: Repository root path
        quiet: If True, suppress individual test names (show only summary)
        
    Returns:
        Tuple of (exit_code, test_results_dict)
    """
    log_substep("Running infrastructure tests (49% coverage threshold)...")
    log_substep("(Skipping LLM integration tests - run separately with: pytest -m requires_ollama)")
    
    # Build pytest command for infrastructure tests
    # Skip requires_ollama tests - they are slow and require external Ollama service
    # Warnings are controlled by pyproject.toml (--disable-warnings + filterwarnings)
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(repo_root / "tests" / "infrastructure"),
        str(repo_root / "tests" / "test_coverage_completion.py"),
        "--ignore=" + str(repo_root / "tests" / "integration" / "test_module_interoperability.py"),
        "-m", "not requires_ollama",
        "--cov=infrastructure",
        "--cov-report=term-missing",
        "--cov-report=html",
        "--cov-report=json",
        "--cov-fail-under=49",
        "--tb=short",
    ]
    
    # Add verbosity based on quiet mode
    if quiet:
        cmd.append("-q")  # Quiet mode - only show summary
    else:
        cmd.append("-v")  # Verbose - show all test names
    
    try:
        # Set up environment with correct Python paths
        env = os.environ.copy()
        pythonpath = os.pathsep.join([
            str(repo_root),
            str(repo_root / "infrastructure"),
            str(repo_root / "project" / "src"),
        ])
        env["PYTHONPATH"] = pythonpath
        
        # Capture output to extract warning count and parse results
        result = subprocess.run(
            cmd, 
            cwd=str(repo_root), 
            env=env, 
            check=False,
            capture_output=True,
            text=True
        )
        
        # Parse test results from output
        test_results = parse_test_output(result.stdout, result.stderr, result.returncode)
        
        # Print output (filtered in quiet mode)
        if result.stdout:
            if quiet:
                # In quiet mode, only show summary lines
                for line in result.stdout.split('\n'):
                    if any(keyword in line for keyword in ['passed', 'failed', 'skipped', 'warnings', 'ERROR', 'FAILED', 'PASSED', 'coverage']):
                        print(line)
            else:
                print(result.stdout)
        
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        # Check for warnings in output
        warning_count = result.stdout.count(" warning") + result.stderr.count(" warning")
        if warning_count > 0:
            logger.warning(f"Infrastructure tests completed with {warning_count} warning(s)")
        
        if result.returncode == 0:
            log_success("Infrastructure tests passed", logger)
        else:
            logger.error("Infrastructure tests failed")
        
        return result.returncode, test_results
    except Exception as e:
        logger.error(f"Failed to run infrastructure tests: {e}", exc_info=True)
        return 1, {}


def run_project_tests(repo_root: Path, quiet: bool = True) -> tuple[int, dict]:
    """Execute project test suite with coverage.
    
    Args:
        repo_root: Repository root path
        quiet: If True, suppress individual test names (show only summary)
        
    Returns:
        Tuple of (exit_code, test_results_dict)
    """
    log_substep("Running project tests (70% coverage threshold)...")
    
    # Build pytest command for project tests
    # Warnings are controlled by pyproject.toml (--disable-warnings + filterwarnings)
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(repo_root / "project" / "tests"),
        "--ignore=" + str(repo_root / "project" / "tests" / "integration"),
        "--cov=project/src",
        "--cov-report=term-missing",
        "--cov-report=html",
        "--cov-report=json",
        "--cov-fail-under=70",
        "--tb=short",
    ]
    
    # Add verbosity based on quiet mode
    if quiet:
        cmd.append("-q")  # Quiet mode - only show summary
    else:
        cmd.append("-v")  # Verbose - show all test names
    
    try:
        # Set up environment with correct Python paths
        env = os.environ.copy()
        pythonpath = os.pathsep.join([
            str(repo_root),
            str(repo_root / "infrastructure"),
            str(repo_root / "project" / "src"),
        ])
        env["PYTHONPATH"] = pythonpath
        
        # Capture output to extract warning count and parse results
        result = subprocess.run(
            cmd, 
            cwd=str(repo_root), 
            env=env, 
            check=False,
            capture_output=True,
            text=True
        )
        
        # Parse test results from output
        test_results = parse_test_output(result.stdout, result.stderr, result.returncode)
        
        # Print output (filtered in quiet mode)
        if result.stdout:
            if quiet:
                # In quiet mode, only show summary lines
                for line in result.stdout.split('\n'):
                    if any(keyword in line for keyword in ['passed', 'failed', 'skipped', 'warnings', 'ERROR', 'FAILED', 'PASSED', 'coverage']):
                        print(line)
            else:
                print(result.stdout)
        
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        # Check for warnings in output
        warning_count = result.stdout.count(" warning") + result.stderr.count(" warning")
        if warning_count > 0:
            logger.warning(f"Project tests completed with {warning_count} warning(s)")
        
        if result.returncode == 0:
            log_success("Project tests passed", logger)
        else:
            logger.error("Project tests failed")
        
        return result.returncode, test_results
    except Exception as e:
        logger.error(f"Failed to run project tests: {e}", exc_info=True)
        return 1, {}


def parse_test_output(stdout: str, stderr: str, exit_code: int) -> dict:
    """Parse test output to extract metrics.
    
    Args:
        stdout: Standard output from pytest
        stderr: Standard error from pytest
        exit_code: Exit code from pytest
        
    Returns:
        Dictionary with test metrics
    """
    results = {
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
    infra_results: dict,
    project_results: dict,
    repo_root: Path
) -> dict:
    """Generate structured test report.
    
    Args:
        infra_results: Infrastructure test results
        project_results: Project test results
        repo_root: Repository root path
        
    Returns:
        Complete test report dictionary
    """
    report = {
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


def save_test_report(report: dict, repo_root: Path) -> None:
    """Save test report to JSON and generate summary.
    
    Args:
        report: Test report dictionary
        repo_root: Repository root path
    """
    output_dir = repo_root / "project" / "output" / "reports"
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


def report_results(
    infra_exit: int,
    project_exit: int,
    infra_results: dict,
    project_results: dict
) -> None:
    """Report test execution results.
    
    Args:
        infra_exit: Infrastructure test exit code
        project_exit: Project test exit code
        infra_results: Infrastructure test results
        project_results: Project test results
    """
    log_header("Test Execution Summary", logger)
    
    # Infrastructure summary
    if infra_exit == 0:
        passed = infra_results.get('passed', 0)
        total = infra_results.get('total', 0)
        coverage = infra_results.get('coverage_percent', 0)
        log_success(
            f"Infrastructure tests: PASSED ({passed}/{total} tests, {coverage:.1f}% coverage)",
            logger
        )
    else:
        failed = infra_results.get('failed', 0)
        logger.error(f"Infrastructure tests: FAILED ({failed} test(s) failed)")
    
    # Project summary
    if project_exit == 0:
        passed = project_results.get('passed', 0)
        total = project_results.get('total', 0)
        coverage = project_results.get('coverage_percent', 0)
        log_success(
            f"Project tests: PASSED ({passed}/{total} tests, {coverage:.1f}% coverage)",
            logger
        )
    else:
        failed = project_results.get('failed', 0)
        logger.error(f"Project tests: FAILED ({failed} test(s) failed)")
    
    # Overall summary
    if infra_exit == 0 and project_exit == 0:
        total_passed = infra_results.get('passed', 0) + project_results.get('passed', 0)
        total_tests = infra_results.get('total', 0) + project_results.get('total', 0)
        log_success(f"All tests passed ({total_passed}/{total_tests}) - ready for analysis", logger)
    else:
        logger.error("Some tests failed - fix issues and try again")


def main() -> int:
    """Execute test suite orchestration.
    
    Runs both infrastructure and project tests in sequence.
    
    Returns:
        Exit code (0=all tests passed, 1=any test failed)
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run test suite")
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show individual test names (default: quiet mode)'
    )
    args = parser.parse_args()
    
    quiet = not args.verbose
    
    log_header("STAGE 01: Run Tests", logger)
    
    repo_root = Path(__file__).parent.parent
    
    # Run infrastructure tests first
    infra_exit, infra_results = run_infrastructure_tests(repo_root, quiet=quiet)
    
    # Run project tests (even if infrastructure tests fail, for complete reporting)
    project_exit, project_results = run_project_tests(repo_root, quiet=quiet)
    
    # Generate and save test report
    report = generate_test_report(infra_results, project_results, repo_root)
    save_test_report(report, repo_root)
    
    # Report combined results
    report_results(infra_exit, project_exit, infra_results, project_results)
    
    # Return failure if any test suite failed
    if infra_exit != 0 or project_exit != 0:
        return 1
    return 0


if __name__ == "__main__":
    exit(main())

