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

        # Enhanced result reporting
        total_projects = len(projects)
        success_rate = (result.successful_projects / total_projects * 100) if total_projects > 0 else 0

        print(f"\n{'='*60}")
        print(f"MULTI-PROJECT EXECUTION RESULTS")
        print(f"{'='*60}")
        print(f"Operation: {operation_desc}")
        print(f"Total Projects: {total_projects}")
        print(f"Successful: {result.successful_projects}")
        failed_projects = total_projects - result.successful_projects
        print(f"Failed: {failed_projects}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Total Duration: {result.total_duration:.1f}s")
        print(f"Average per Project: {result.total_duration/total_projects:.1f}s" if total_projects > 0 else "")

        if run_infra_tests and result.infra_test_duration > 0:
            infra_percentage = (result.infra_test_duration / result.total_duration * 100)
            print(f"Infrastructure Tests: {result.infra_test_duration:.1f}s ({infra_percentage:.1f}%)")

        # Show project status summary
        if hasattr(result, 'project_results') and result.project_results:
            print(f"\nProject Status:")
            if isinstance(result.project_results, dict):
                for proj_name in sorted(result.project_results.keys()):
                    proj_result = result.project_results[proj_name]
                    if isinstance(proj_result, list) and proj_result:
                        # Check if all stages succeeded
                        all_success = all(stage.success for stage in proj_result if hasattr(stage, 'success'))
                        duration = sum(stage.duration for stage in proj_result if hasattr(stage, 'duration'))
                        status = "✅" if all_success else "❌"
                        print(f"  {status} {proj_name}: {len(proj_result)} stages, {duration:.1f}s")
                    else:
                        print(f"  ❓ {proj_name}: Unknown status")
            else:
                print(f"  ⚠ project_results format unexpected")

        print(f"{'='*60}")

        # Generate comprehensive final summary
        try:
            from infrastructure.reporting.pipeline_reporter import generate_multi_project_summary_report
            summary_output_dir = repo_root / "output" / "multi_project_summary"
            summary_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate and save comprehensive summary
            summary_files = generate_multi_project_summary_report(
                result=result,
                projects=projects,
                output_dir=summary_output_dir
            )
            
            logger.info("Multi-project summary reports generated:")
            for fmt, path in summary_files.items():
                logger.info(f"  • {fmt.upper()}: {path}")
                
        except ImportError:
            logger.warning("Multi-project summary generation not available")
        except Exception as e:
            logger.warning(f"Failed to generate multi-project summary: {e}")

        if result.successful_projects == len(projects):
            print("🎉 All projects completed successfully!")
            return 0
        else:
            print("❌ Some projects failed")
            # List failed projects
            if hasattr(result, 'project_results') and result.project_results:
                failed = []
                for name, results_list in result.project_results.items():
                    if isinstance(results_list, list) and results_list:
                        # Check if all stages for this project succeeded
                        all_stages_success = all(result.success for result in results_list)
                        if not all_stages_success:
                            failed.append(name)
                    elif not results_list:
                        # Empty results list means project failed
                        failed.append(name)

                if failed:
                    print("   Failed projects:")
                    for proj_name in failed:
                        print(f"     - {proj_name}")
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