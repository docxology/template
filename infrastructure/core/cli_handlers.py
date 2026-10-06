"""CLI command handlers for core infrastructure operations.

Each handler receives parsed arguments and returns an exit code (0 for success,
1 for failure). Handlers are dispatched from the main entry point in cli.py.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""

import argparse
import json
from collections.abc import Sequence

from infrastructure.core.files.inventory import FileInventoryManager
from infrastructure.core.logging.utils import get_logger
from infrastructure.core.errors import (
    DISCOVER_FAILED,
    INVENTORY_FAILED,
    MULTI_PROJECT_FAILED,
    NO_PROJECTS_FOUND,
)
from infrastructure.core.pipeline.multi_project import (
    MultiProjectConfig,
    MultiProjectOrchestrator,
    MultiProjectResult,
    format_multi_project_outcome_lines,
)
from infrastructure.project.discovery import discover_projects
from infrastructure.project.project_info import ProjectInfo
from infrastructure.orchestration.discovery import validate_project_slug
from infrastructure.orchestration.pipeline_runner import PipelineInvocation, PipelineRunner

logger = get_logger(__name__)


def _emit_multi_project_outcome(
    log_obj: object,
    ordered_projects: Sequence[ProjectInfo],
    result: MultiProjectResult,
) -> None:
    """Log per-project outcomes (mirrors PipelineRunner banner detail)."""
    lines = format_multi_project_outcome_lines(ordered_projects, result)
    section: str | None = None
    for line in lines:
        if line == "Succeeded:":
            section = "succeeded"
            log_obj.info(line)  # type: ignore[attr-defined]
        elif line == "Failed:":
            section = "failed"
            log_obj.error(line)  # type: ignore[attr-defined]
        elif line.startswith("  - "):
            if section == "failed":
                log_obj.error(line)  # type: ignore[attr-defined]
            else:
                log_obj.info(line)  # type: ignore[attr-defined]
        else:
            log_obj.error(line)  # type: ignore[attr-defined]


def handle_pipeline_command(args: argparse.Namespace) -> int:
    """Delegate to the canonical orchestration consumer and expected-stage result."""
    return PipelineRunner(args.repo_root).run(
        PipelineInvocation(
            args.project,
            mode=args.mode,
            skip_infra=args.skip_infra,
            resume=args.resume,
        )
    )


def handle_multi_project_command(args: argparse.Namespace) -> int:
    """Run an explicit canonical project selection with shared verification once."""
    projects = discover_projects(args.repo_root)
    if not projects:
        logger.error(NO_PROJECTS_FOUND.format())
        return 1
    if args.projects:
        selected = tuple(validate_project_slug(name, args.repo_root, projects=projects) for name in args.projects)
        if len(selected) != len(set(selected)):
            raise ValueError("Duplicate selected project identities")
        indexed = {project.qualified_name: project for project in projects}
        if any(name not in indexed for name in selected):
            raise ValueError("Selected projects must belong to the discovered render set")
        projects = [indexed[name] for name in selected]
    config = MultiProjectConfig(
        args.repo_root, projects, run_infra_tests=not args.skip_infra, mode=args.mode, resume=args.resume
    )
    try:
        result = MultiProjectOrchestrator(config).execute_all_projects()
        _emit_multi_project_outcome(logger, projects, result)
        logger.info(
            "Multi-project execution: %s succeeded, %s failed", result.successful_projects, result.failed_projects
        )
        return result.exit_code
    except TimeoutError as exc:
        logger.error("Multi-project deadline expired: %s", exc)
        return 124
    except KeyboardInterrupt:
        return 130
    except ValueError:
        raise
    except Exception as exc:
        logger.error(MULTI_PROJECT_FAILED.format(error=f"{type(exc).__name__}: {exc}"))
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

    except (OSError, ValueError) as e:
        logger.error(INVENTORY_FAILED.format(error=e))
        return 1


def handle_discover_command(args: argparse.Namespace) -> int:
    """Handle project discovery command."""
    logger.info("Discovering available projects")

    try:
        projects = discover_projects(args.repo_root)

        if args.format == "json":
            project_data = [
                {
                    "name": p.name,
                    "path": str(p.path),
                    "has_src": p.has_src,
                    "has_tests": p.has_tests,
                    "has_scripts": p.has_scripts,
                    "has_manuscript": p.has_manuscript,
                    "metadata": p.metadata,
                    "is_valid": p.is_valid,
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

    except (OSError, ValueError) as e:
        logger.error(DISCOVER_FAILED.format(error=e))
        return 1
