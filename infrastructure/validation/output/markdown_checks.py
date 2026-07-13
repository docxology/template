"""Manuscript markdown checks for the output validation pipeline."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from infrastructure.core.logging.diagnostic import DiagnosticReporter
from infrastructure.validation.content.discovery import discover_markdown_files
from infrastructure.core.logging.utils import get_logger, log_success, log_substep
from infrastructure.core.project_paths import resolve_source_manuscript_dir

logger = get_logger(__name__)


def _load_markdown_validator() -> Callable[..., tuple[list[Any], int]]:
    from infrastructure.validation.content.markdown_validator import validate_markdown

    return validate_markdown


def validate_manuscript_output_markdown(
    project_root: Path,
    repo_root: Path,
    project_name: str,
    *,
    validator: Callable[..., tuple[list[Any], int]] | None = None,
    validator_loader: Callable[[], Callable[..., tuple[list[Any], int]]] = _load_markdown_validator,
) -> bool:
    """Validate manuscript markdown for Stage 04 without failing on advisory notes."""
    log_substep("Validating markdown files...", logger)

    manuscript_dir = resolve_source_manuscript_dir(project_root)
    if not manuscript_dir.exists():
        logger.warning("Manuscript directory not found at expected location: %s", manuscript_dir)
        return True

    markdown_files = discover_markdown_files(manuscript_dir, scope="tree")
    if not markdown_files:
        logger.warning("No markdown files found")
        return True

    log_success(f"Found {len(markdown_files)} markdown file(s)", logger)

    try:
        logger.info("Running markdown validation...")
        validate_md = validator or validator_loader()
        problems, _exit_code = validate_md(manuscript_dir, repo_root, strict=False)

        if not problems:
            DiagnosticReporter(
                project_name=project_name,
                output_dir=project_root / "output",
                load_existing=False,
            ).clear_report()
            log_success("Markdown validation passed (no issues found)", logger)
            return True

        reporter = DiagnosticReporter(
            project_name=project_name,
            output_dir=project_root / "output",
            load_existing=False,
        )
        logger.info("  Found %d validation note(s):", len(problems))
        for problem in problems:
            reporter.record(problem)
        reporter.save_report()

        for problem in problems[:5]:
            loc = f"[{problem.file_path}] " if problem.file_path else ""
            logger.info("    - %s%s", loc, problem.message)
        if len(problems) > 5:
            logger.info("    ... and %d more", len(problems) - 5)
        logger.info("  (Markdown validation notes are non-critical)")
        return True
    except ImportError as exc:
        # Genuine breakage (the validator could not be loaded) must be visible
        # in the Stage-4 summary, not silently reported as PASSED. Returning
        # False surfaces it as a non-critical WARN via the pipeline summary
        # logic and reaches the "Markdown validation" recommendation branch.
        logger.warning("Could not import markdown validator: %s", exc)
        return False
    except (OSError, RuntimeError, ValueError, AttributeError) as exc:
        # A validator that raises mid-run is broken, not advisory: surface it.
        logger.warning("Markdown validation error: %s", exc)
        return False
