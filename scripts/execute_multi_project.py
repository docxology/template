#!/usr/bin/env python3
"""Execute multi-project orchestration.

This script provides multi-project pipeline execution functionality extracted
from run.sh into testable Python code following the thin orchestrator pattern.
"""

import sys
from pathlib import Path

# Add repo root to Python path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from infrastructure.core.logging_utils import get_logger
from infrastructure.core.multi_project import MultiProjectConfig, MultiProjectOrchestrator
from infrastructure.project.discovery import discover_projects

logger = get_logger(__name__)


def execute_multi_project(
    repo_root: Path,
    run_infra_tests: bool = True,
    run_llm: bool = True,
    run_executive_report: bool = True,
    skip_infra: bool = False
) -> int:
    """Execute multi-project orchestration.

    Args:
        repo_root: Repository root path
        run_infra_tests: Whether to run infrastructure tests
        run_llm: Whether to run LLM stages
        run_executive_report: Whether to generate executive report
        skip_infra: Whether to skip infrastructure tests (for individual projects)

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Discover projects
        projects = discover_projects(repo_root)
        if not projects:
            logger.error("No valid projects found")
            return 1

        logger.info(f"Found {len(projects)} projects: {', '.join([p.name for p in projects])}")

        # Create multi-project configuration
        config = MultiProjectConfig(
            repo_root=repo_root,
            projects=projects,
            run_infra_tests=run_infra_tests,
            run_llm=run_llm,
            run_executive_report=run_executive_report
        )

        # Execute multi-project pipeline
        orchestrator = MultiProjectOrchestrator(config)

        if skip_infra:
            result = orchestrator.execute_all_projects_full_no_infra()
            operation_desc = "multi-project execution (no infra)"
        elif run_llm and run_infra_tests:
            result = orchestrator.execute_all_projects_full()
            operation_desc = "multi-project full execution"
        elif not run_llm and run_infra_tests:
            result = orchestrator.execute_all_projects_core()
            operation_desc = "multi-project core execution"
        elif not run_llm and not run_infra_tests:
            result = orchestrator.execute_all_projects_core_no_infra()
            operation_desc = "multi-project core execution (no infra)"
        else:
            result = orchestrator.execute_all_projects_core()
            operation_desc = "multi-project core execution"

        # Report results
        print(f"✅ {operation_desc.capitalize()} completed")
        print(f"   Successful projects: {result.successful_projects}")
        print(f"   Failed projects: {result.failed_projects}")
        print(f"   Total duration: {result.total_duration:.1f}s")

        if run_infra_tests and result.infra_test_duration > 0:
            print(f"   Infrastructure tests: {result.infra_test_duration:.1f}s")

        if result.successful_projects == len(projects):
            print("🎉 All projects completed successfully!")
            return 0
        else:
            print("❌ Some projects failed")
            return 1

    except Exception as e:
        logger.error(f"Multi-project execution failed: {e}")
        return 1


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Execute multi-project orchestration")
    parser.add_argument("--no-infra-tests", action="store_true", help="Skip infrastructure tests")
    parser.add_argument("--no-llm", action="store_true", help="Skip LLM stages")
    parser.add_argument("--no-executive-report", action="store_true", help="Skip executive report")
    parser.add_argument("--skip-infra", action="store_true", help="Skip infra tests for individual projects")

    args = parser.parse_args()

    return execute_multi_project(
        repo_root=repo_root,
        run_infra_tests=not args.no_infra_tests,
        run_llm=not args.no_llm,
        run_executive_report=not args.no_executive_report,
        skip_infra=args.skip_infra
    )


if __name__ == "__main__":
    sys.exit(main())