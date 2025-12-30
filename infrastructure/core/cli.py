"""CLI interface for core infrastructure modules.

This module provides command-line interfaces for core pipeline functionality,
extracted from bash scripts into testable Python CLI.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from infrastructure.core.logging_utils import get_logger, setup_logger
from infrastructure.core.pipeline import PipelineConfig, PipelineExecutor
from infrastructure.core.multi_project import MultiProjectConfig, MultiProjectOrchestrator
from infrastructure.core.file_inventory import FileInventoryManager
from infrastructure.core.pipeline_summary import PipelineSummaryGenerator
from infrastructure.project.discovery import discover_projects

logger = get_logger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser for core CLI commands."""
    parser = argparse.ArgumentParser(
        description="Core infrastructure CLI for pipeline operations",
        prog="python -m infrastructure.core.cli"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Pipeline execution command
    pipeline_parser = subparsers.add_parser(
        "pipeline",
        help="Execute pipeline for a project"
    )
    pipeline_parser.add_argument(
        "pipeline_type",
        choices=["full", "core"],
        help="Type of pipeline to execute"
    )
    pipeline_parser.add_argument(
        "--project",
        required=True,
        help="Project name to execute pipeline for"
    )
    pipeline_parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root directory"
    )
    pipeline_parser.add_argument(
        "--skip-infra",
        action="store_true",
        help="Skip infrastructure tests (already run)"
    )
    pipeline_parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume pipeline from checkpoint"
    )

    # Multi-project execution command
    multi_parser = subparsers.add_parser(
        "multi-project",
        help="Execute pipeline across multiple projects"
    )
    multi_parser.add_argument(
        "execution_type",
        choices=["full", "core", "full-no-infra", "core-no-infra"],
        help="Type of multi-project execution"
    )
    multi_parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root directory"
    )
    multi_parser.add_argument(
        "--projects",
        nargs="+",
        help="Specific projects to execute (default: all)"
    )

    # File inventory command
    inventory_parser = subparsers.add_parser(
        "inventory",
        help="Generate file inventory report"
    )
    inventory_parser.add_argument(
        "output_dir",
        type=Path,
        help="Output directory to scan"
    )
    inventory_parser.add_argument(
        "--format",
        choices=["text", "json", "html"],
        default="text",
        help="Output format"
    )
    inventory_parser.add_argument(
        "--categories",
        nargs="+",
        help="Categories to scan (default: all)"
    )

    # Summary command
    summary_parser = subparsers.add_parser(
        "summary",
        help="Generate pipeline summary (for testing)"
    )
    summary_parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Output directory"
    )
    summary_parser.add_argument(
        "--format",
        choices=["text", "json", "html"],
        default="text",
        help="Output format"
    )
    summary_parser.add_argument(
        "--log-file",
        type=Path,
        help="Pipeline log file"
    )
    summary_parser.add_argument(
        "--skip-infra",
        action="store_true",
        help="Whether infrastructure tests were skipped"
    )

    # Project discovery command
    discover_parser = subparsers.add_parser(
        "discover",
        help="Discover available projects"
    )
    discover_parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root directory"
    )
    discover_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format"
    )

    return parser


def main() -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        setup_logger("infrastructure.core.cli")

        if args.command == "pipeline":
            return handle_pipeline_command(args)
        elif args.command == "multi-project":
            return handle_multi_project_command(args)
        elif args.command == "inventory":
            return handle_inventory_command(args)
        elif args.command == "summary":
            return handle_summary_command(args)
        elif args.command == "discover":
            return handle_discover_command(args)
        else:
            logger.error(f"Unknown command: {args.command}")
            return 1

    except Exception as e:
        logger.error(f"CLI command failed: {e}")
        return 1


def handle_pipeline_command(args: argparse.Namespace) -> int:
    """Handle pipeline execution command."""
    logger.info(f"Executing {args.pipeline_type} pipeline for project '{args.project}'")

    # Create pipeline configuration
    config = PipelineConfig(
        project_name=args.project,
        repo_root=args.repo_root,
        skip_infra=args.skip_infra,
        skip_llm=(args.pipeline_type == "core"),
        resume=args.resume,
        total_stages=7 if args.pipeline_type == "core" else 9
    )

    # Execute pipeline
    executor = PipelineExecutor(config)

    try:
        if args.pipeline_type == "full":
            results = executor.execute_full_pipeline()
        else:  # core
            results = executor.execute_core_pipeline()

        # Report results
        successful_stages = sum(1 for r in results if r.success)
        total_stages = len(results)

        logger.info(f"Pipeline completed: {successful_stages}/{total_stages} stages successful")

        if all(r.success for r in results):
            logger.info("✅ All pipeline stages completed successfully")
            return 0
        else:
            logger.error("❌ Some pipeline stages failed")
            for result in results:
                if not result.success:
                    logger.error(f"  - Stage {result.stage_num}: {result.stage_name} - {result.error_message}")
            return 1

    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        return 1


def handle_multi_project_command(args: argparse.Namespace) -> int:
    """Handle multi-project execution command."""
    logger.info(f"Executing {args.execution_type} pipeline across multiple projects")

    # Discover projects
    projects = discover_projects(args.repo_root)
    if not projects:
        logger.error("No valid projects found")
        return 1

    # Filter projects if specified
    if args.projects:
        project_names = {p.name for p in projects}
        requested_names = set(args.projects)
        invalid_projects = requested_names - project_names

        if invalid_projects:
            logger.error(f"Invalid projects: {', '.join(invalid_projects)}")
            logger.info(f"Available projects: {', '.join(project_names)}")
            return 1

        projects = [p for p in projects if p.name in requested_names]

    if not projects:
        logger.error("No projects to execute")
        return 1

    logger.info(f"Found {len(projects)} projects: {', '.join(p.name for p in projects)}")

    # Create multi-project configuration
    run_infra_tests = "no-infra" not in args.execution_type
    run_llm = "core" not in args.execution_type

    config = MultiProjectConfig(
        repo_root=args.repo_root,
        projects=projects,
        run_infra_tests=run_infra_tests,
        run_llm=run_llm,
        run_executive_report=True
    )

    # Execute multi-project pipeline
    orchestrator = MultiProjectOrchestrator(config)

    try:
        if args.execution_type == "full":
            result = orchestrator.execute_all_projects_full()
        elif args.execution_type == "core":
            result = orchestrator.execute_all_projects_core()
        elif args.execution_type == "full-no-infra":
            result = orchestrator.execute_all_projects_full_no_infra()
        elif args.execution_type == "core-no-infra":
            result = orchestrator.execute_all_projects_core_no_infra()
        else:
            logger.error(f"Unknown execution type: {args.execution_type}")
            return 1

        # Report results
        logger.info(f"Multi-project execution completed:")
        logger.info(f"  - Successful projects: {result.successful_projects}")
        logger.info(f"  - Failed projects: {result.failed_projects}")
        logger.info(f"  - Total duration: {result.total_duration:.1f}s")

        if result.infra_test_duration > 0:
            logger.info(f"  - Infrastructure tests: {result.infra_test_duration:.1f}s")

        if result.successful_projects == len(projects):
            logger.info("✅ All projects completed successfully")
            return 0
        else:
            logger.error("❌ Some projects failed")
            return 1

    except Exception as e:
        logger.error(f"Multi-project execution failed: {e}")
        return 1


def handle_inventory_command(args: argparse.Namespace) -> int:
    """Handle file inventory command."""
    logger.info(f"Generating file inventory for {args.output_dir}")

    try:
        manager = FileInventoryManager()
        entries = manager.collect_output_files(args.output_dir, args.categories)

        if not entries:
            logger.info("No files found in output directory")
            return 0

        report = manager.generate_inventory_report(entries, args.format, args.output_dir)
        print(report)
        return 0

    except Exception as e:
        logger.error(f"Failed to generate inventory: {e}")
        return 1


def handle_summary_command(args: argparse.Namespace) -> int:
    """Handle summary generation command."""
    logger.info("Generating pipeline summary (for testing)")

    try:
        # For testing purposes, create a mock summary
        # In real usage, this would be called with actual stage results
        generator = PipelineSummaryGenerator()

        # Create mock stage results for demonstration
        from infrastructure.core.pipeline import PipelineStageResult
        mock_results = [
            PipelineStageResult(1, "Environment Setup", True, 2.5),
            PipelineStageResult(2, "Infrastructure Tests", True, 15.3),
            PipelineStageResult(3, "Project Tests", True, 8.7),
            PipelineStageResult(4, "Project Analysis", True, 12.1),
            PipelineStageResult(5, "PDF Rendering", True, 45.2),
            PipelineStageResult(6, "Output Validation", True, 3.8),
            PipelineStageResult(7, "Copy Outputs", True, 1.2),
        ]

        summary = generator.generate_summary(
            mock_results,
            sum(r.duration for r in mock_results),
            args.output_dir,
            args.log_file,
            args.skip_infra
        )

        formatted = generator.format_summary(summary, args.format)
        print(formatted)
        return 0

    except Exception as e:
        logger.error(f"Failed to generate summary: {e}")
        return 1


def handle_discover_command(args: argparse.Namespace) -> int:
    """Handle project discovery command."""
    logger.info("Discovering available projects")

    try:
        projects = discover_projects(args.repo_root)

        if args.format == "json":
            import json
            project_data = [
                {
                    "name": p.name,
                    "path": str(p.path),
                    "has_src": p.has_src,
                    "has_tests": p.has_tests,
                    "has_scripts": p.has_scripts,
                    "has_manuscript": p.has_manuscript,
                    "metadata": p.metadata,
                    "is_valid": p.is_valid
                }
                for p in projects
            ]
            print(json.dumps(project_data, indent=2))
        else:  # text format
            if not projects:
                print("No valid projects found")
                return 0

            print(f"Found {len(projects)} projects:")
            print()

            for project in projects:
                status = "✅ Valid" if project.is_valid else "❌ Invalid"
                print(f"  {status} {project.name}")
                print(f"    Path: {project.path}")

                components = []
                if project.has_src:
                    components.append("src")
                if project.has_tests:
                    components.append("tests")
                if project.has_scripts:
                    components.append("scripts")
                if project.has_manuscript:
                    components.append("manuscript")

                if components:
                    print(f"    Components: {', '.join(components)}")

                if project.metadata.get("description"):
                    print(f"    Description: {project.metadata['description']}")

                print()

        return 0

    except Exception as e:
        logger.error(f"Failed to discover projects: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())