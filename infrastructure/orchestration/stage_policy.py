"""CLI orchestration policy for the thin pipeline stage scripts.

Business logic extracted from ``scripts/pipeline/stage_01_test.py`` (profile
and worker defaulting, default-project fallback, mutual-exclusion validation,
and the all-projects vs single-pipeline dispatch) and from
``scripts/pipeline/stage_05_copy.py`` (output-copy orchestration), so both
stage scripts stay thin argparse-to-policy adapters — the pattern
``scripts/pipeline/stage_03_render.py`` already follows with
``infrastructure.rendering.pipeline``.

The Stage 01 argparse wiring is copied verbatim so ``--help`` output stays
byte-identical. Every policy function takes explicit parameters; none reads
module state to make a decision.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from infrastructure.core.files.cleanup import (
    clean_final_output_directory,
    clean_root_output_directory,
)
from infrastructure.core.files.operations import copy_final_deliverables
from infrastructure.core.logging.utils import get_logger, log_substep, log_success
from infrastructure.core.pipeline.artifacts import (
    STABLE_OUTPUT_INVENTORY_MODE,
    collect_stable_output_inventory,
    output_inventory_mode_for_project,
)
from infrastructure.core.testing.pytest_orchestration import (
    INFRASTRUCTURE_TEST_SCOPES,
    TEST_PROFILE_NAMES,
    InfrastructureTestScope,
    TestProfileName,
    resolve_test_profile,
    resolve_xdist_worker_config,
    validate_project_matrix_concurrency,
)
from infrastructure.core.testing.test_runner import run_per_project_pytest
from infrastructure.project.discovery import discover_projects, resolve_project_root
from infrastructure.project.public_scope import public_project_names
from infrastructure.reporting.output_statistics import (
    STAGE5_DELIVERY_INVENTORY_SCOPE,
    collect_output_statistics,
    generate_detailed_output_report,
    log_output_summary,
    write_output_statistics_reports,
)
from infrastructure.reporting.pipeline_test_runner import execute_test_pipeline
from infrastructure.validation.output.render_formats import (
    enabled_render_formats,
    load_effective_rendering_config,
    remove_disabled_render_outputs,
    render_config_manuscript_dir,
)
from infrastructure.validation.output.validator import (
    validate_copied_outputs,
    validate_output_structure,
)

logger = get_logger(__name__)


def build_stage_01_parser() -> argparse.ArgumentParser:
    """Return the Stage 01 CLI parser (wiring copied verbatim from the stage script)."""
    parser = argparse.ArgumentParser(description="Run test suite")
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress individual test names (default: verbose mode)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show individual test names (default; use --quiet to suppress)",
    )
    parser.add_argument(
        "--project",
        default="project",
        help="Project name in projects/ directory (default: project)",
    )
    parser.add_argument(
        "--non-strict",
        action="store_true",
        help="Allow configured test-failure tolerances (not recommended for CI)",
    )
    parser.add_argument(
        "--profile",
        choices=TEST_PROFILE_NAMES,
        default="quick",
        help=(
            "Central test profile. 'quick' is the bounded default lane; "
            "'release' includes slow tests for public/release validation; "
            "'exhaustive' adds long-running tests; live services and "
            "benchmarks remain explicit opt-ins."
        ),
    )
    parser.add_argument(
        "--include-slow",
        action="store_true",
        help="Include slow tests (normally skipped for faster execution)",
    )
    parser.add_argument(
        "--include-long-running",
        action="store_true",
        help=(
            "Include long-running end-to-end/deep gate tests. These are heavier "
            "than ordinary slow tests and are skipped by default."
        ),
    )
    parser.add_argument(
        "--infra-only",
        action="store_true",
        help="Run only infrastructure tests (skip project tests)",
    )
    parser.add_argument(
        "--infra-scope",
        choices=INFRASTRUCTURE_TEST_SCOPES,
        default="full",
        help=(
            "Infrastructure test scope. 'full' runs the coverage-bearing repo "
            "suite; 'pipeline-smoke' runs the focused real contract used by "
            "project pipelines."
        ),
    )
    parser.add_argument(
        "--project-only",
        action="store_true",
        help="Run only project tests (skip infrastructure tests)",
    )
    parser.add_argument(
        "--include-ollama-tests",
        action="store_true",
        help="Include Ollama-dependent tests (requires Ollama server running)",
    )
    parser.add_argument(
        "--include-bench",
        action="store_true",
        help="Include benchmark/performance-marked tests",
    )
    parser.add_argument(
        "--all-projects",
        action="store_true",
        help=(
            "When combined with --project-only, run every discovered "
            "projects/<name>/tests/ via infrastructure.core.testing.test_runner "
            "(one pytest process per project; combined coverage gate at end). "
            "This mirrors the open-coded loop in .github/workflows/ci.yml."
        ),
    )
    parser.add_argument(
        "--public-projects",
        action="store_true",
        help=(
            "When combined with --project-only --all-projects, restrict the "
            "per-project loop to infrastructure.project.public_scope. Use this "
            "for public-repo release validation in checkouts that also symlink "
            "private or rotating local projects."
        ),
    )
    parser.add_argument(
        "--project-workers",
        metavar="WORKERS",
        default=None,
        help=(
            "Outer project-matrix worker count for --project-only --all-projects. "
            "Use 'auto', 'serial', or a positive integer. Quick all-projects runs "
            "default to bounded auto parallelism; release lanes remain serial unless set."
        ),
    )
    parser.add_argument(
        "--parallel",
        "-n",
        metavar="WORKERS",
        default=None,
        help=(
            "Opt into pytest-xdist parallelism: 'auto' (one worker per core) or "
            "a positive integer. Default is serial. Also honours the "
            "PYTEST_XDIST_WORKERS env var. On loaded dev machines prefer a fixed "
            "count (e.g. -n 6) over 'auto' to avoid wall-clock timeout flakiness."
        ),
    )
    parser.add_argument(
        "--receipt",
        metavar="PATH",
        default=None,
        help=(
            "When combined with --project-only --all-projects, write a "
            "deterministic public-matrix receipt (roster revision, profile, "
            "per-project floor/exit/timeout/coverage/output-isolation) to this "
            "path after the run."
        ),
    )
    return parser


@dataclass(frozen=True)
class TestStageOptions:
    """Validated Stage 01 CLI policy result consumed by :func:`execute_test_stage`."""

    profile: str
    include_slow: bool
    include_long_running: bool
    include_ollama_tests: bool
    include_bench: bool
    infra_only: bool
    project_only: bool
    all_projects: bool
    public_projects: bool
    infra_scope: str
    quiet: bool
    strict: bool
    project_workers: str | None
    parallel: str | None
    receipt_path: str | None


def resolve_effective_project_workers(
    *,
    project_only: bool,
    all_projects: bool,
    project_workers: str | None,
    profile: str,
) -> str | None:
    """Apply the all-projects worker defaulting policy.

    Quick all-projects runs default to bounded ``auto`` parallelism; release and
    exhaustive lanes remain serial unless workers are set explicitly.
    """
    if project_only and all_projects and project_workers is None and profile == "quick":
        return "auto"
    return project_workers


def resolve_test_stage_options(
    *,
    profile: str,
    include_slow: bool,
    include_long_running: bool,
    include_ollama_tests: bool,
    include_bench: bool,
    infra_only: bool,
    project_only: bool,
    all_projects: bool,
    public_projects: bool,
    infra_scope: str,
    quiet: bool,
    strict: bool,
    project_workers: str | None,
    parallel: str | None,
    receipt_path: str | None,
) -> TestStageOptions:
    """Validate Stage 01 flags and apply the profile/worker defaulting policy.

    Raises:
        ValueError: On mutually exclusive flags or an invalid profile/worker
            configuration. Stage scripts surface the message via
            ``parser.error`` so CLI behaviour is unchanged.
    """
    if infra_only and project_only:
        raise ValueError("--infra-only and --project-only cannot be used together")
    if public_projects and not (project_only and all_projects):
        raise ValueError("--public-projects requires --project-only --all-projects")
    if project_workers is not None and not (project_only and all_projects):
        raise ValueError("--project-workers requires --project-only --all-projects")

    effective_project_workers = resolve_effective_project_workers(
        project_only=project_only,
        all_projects=all_projects,
        project_workers=project_workers,
        profile=profile,
    )

    # argparse restricts --profile to TEST_PROFILE_NAMES; resolve_test_profile
    # re-validates at runtime, so the cast below is guarded.
    profile_name = cast(TestProfileName, profile)
    resolve_test_profile(
        profile_name,
        include_slow=include_slow,
        include_long_running=include_long_running,
        include_ollama_tests=include_ollama_tests,
        include_bench=include_bench,
    )
    resolve_xdist_worker_config(parallel, strict=parallel is not None)
    validate_project_matrix_concurrency(
        effective_project_workers,
        parallel,
        strict_parallel=parallel is not None,
    )

    return TestStageOptions(
        profile=profile,
        include_slow=include_slow,
        include_long_running=include_long_running,
        include_ollama_tests=include_ollama_tests,
        include_bench=include_bench,
        infra_only=infra_only,
        project_only=project_only,
        all_projects=all_projects,
        public_projects=public_projects,
        infra_scope=infra_scope,
        quiet=quiet,
        strict=strict,
        project_workers=effective_project_workers,
        parallel=parallel,
        receipt_path=receipt_path,
    )


@dataclass(frozen=True)
class DefaultProjectResolution:
    """Result of the Stage 01 default-project fallback policy."""

    project: str
    fallback_applied: bool
    discovery_error: str | None


def resolve_default_project(repo_root: Path, project: str) -> DefaultProjectResolution:
    """Resolve the Stage 01 project, falling back when the placeholder is not runnable.

    ``--project`` defaults to the ``project`` placeholder. When that placeholder
    resolves to a directory without ``src/``/``tests/``, the first discovered
    runnable project is used instead. Discovery failures degrade to the
    ``discovery_error`` payload; they never fail the stage.
    """
    project_root = resolve_project_root(repo_root, project)
    if project != "project" or ((project_root / "src").exists() and (project_root / "tests").exists()):
        return DefaultProjectResolution(project=project, fallback_applied=False, discovery_error=None)
    try:
        discovered = discover_projects(repo_root)
        runnable = [
            candidate
            for candidate in discovered
            if (candidate.path / "src").exists() and (candidate.path / "tests").exists()
        ]
        if runnable:
            return DefaultProjectResolution(project=runnable[0].name, fallback_applied=True, discovery_error=None)
    except Exception as exc:  # noqa: BLE001 — degrade to a warning payload, never fail the stage
        return DefaultProjectResolution(project=project, fallback_applied=False, discovery_error=str(exc))
    return DefaultProjectResolution(project=project, fallback_applied=False, discovery_error=None)


def execute_test_stage(options: TestStageOptions, project: str, repo_root: Path) -> int:
    """Dispatch the resolved Stage 01 options: per-project loop or single pipeline."""
    resolution = resolve_default_project(repo_root, project)
    if resolution.fallback_applied:
        log_substep(f"Default project placeholder is not runnable; using '{resolution.project}' instead.", logger)
    if resolution.discovery_error is not None:
        logger.warning("Project discovery failed; continuing with project=%s (%s)", project, resolution.discovery_error)

    # --project-only --all-projects dispatches to the per-project runner
    # (one pytest process per project, combined coverage gate at end).
    # This is the local mirror of the bash loop in .github/workflows/ci.yml.
    if options.project_only and options.all_projects:
        projects: list[str] | None = None
        if options.public_projects:
            projects = public_project_names(repo_root)
            log_substep(
                "Restricting all-projects test run to public scope: " + ", ".join(projects),
                logger,
            )
        return run_per_project_pytest(
            repo_root,
            projects=projects,
            profile=cast(TestProfileName, options.profile),
            include_slow=options.include_slow,
            include_long_running=options.include_long_running,
            include_ollama_tests=options.include_ollama_tests,
            include_bench=options.include_bench,
            project_workers=options.project_workers,
            parallel=options.parallel,
            receipt_path=options.receipt_path,
        )

    return execute_test_pipeline(
        project_name=resolution.project,
        repo_root=repo_root,
        run_infra=not options.project_only,
        run_project=not options.infra_only,
        quiet=options.quiet,
        profile=cast(TestProfileName, options.profile),
        include_slow=options.include_slow,
        include_long_running=options.include_long_running,
        include_bench=options.include_bench,
        include_ollama_tests=options.include_ollama_tests,
        strict=options.strict,
        infra_scope=cast(InfrastructureTestScope, options.infra_scope),
        parallel=options.parallel,
    )


def execute_copy_stage(project_name: str, *, repo_root: Path) -> int:
    """Copy and validate one already-resolved project using real files."""

    project_root = resolve_project_root(repo_root, project_name)
    output_dir = repo_root / "output" / project_name
    inventory_mode = output_inventory_mode_for_project(repo_root, project_root)

    try:
        render_config = load_effective_rendering_config(project_root)
    except (OSError, TypeError, ValueError) as exc:
        logger.error("Could not determine enabled render formats: %s", exc)
        return 1
    formats = enabled_render_formats(render_config)
    manuscript_dir = render_config_manuscript_dir(project_root)

    try:
        # Step 1: Clean root-level directories from output/ (keep only project folders)
        projects = discover_projects(repo_root)
        project_names = sorted({p.qualified_name for p in projects} | {project_name})
        if not clean_root_output_directory(repo_root, project_names):
            logger.error("Failed to clean root output directory")
            return 1

        # Step 2: Clean project-specific output directory
        clean_final_output_directory(output_dir)

        # Step 2: Copy final deliverables
        stats = copy_final_deliverables(repo_root, output_dir, project_name, project_dir=project_root)

        # Step 3: Filter stale artifacts for formats disabled in this run.
        # The source project tree is preserved; only the freshly cleaned copy
        # is narrowed to the effective publication-format contract.
        remove_disabled_render_outputs(output_dir, project_name, formats)

        # Refresh copy counts after format filtering so the console summary
        # describes the deliverables that actually remain.
        stats["pdf_files"] = sum(1 for path in (output_dir / "pdf").rglob("*") if path.is_file())
        stats["web_files"] = sum(1 for path in (output_dir / "web").rglob("*") if path.is_file())
        stats["slides_files"] = sum(1 for path in (output_dir / "slides").rglob("*") if path.is_file())
        stats["docx_files"] = sum(1 for path in (output_dir / "docx").rglob("*") if path.is_file())
        stats["epub_files"] = sum(1 for path in (output_dir / "epub").rglob("*") if path.is_file())
        stats["combined_pdf"] = int((output_dir / f"{Path(project_name).name}_combined.pdf").is_file())
        stats["total_files"] = sum(1 for path in output_dir.rglob("*") if path.is_file())

        # The root delivery mirror is intentionally Git-ignored. Evaluate its
        # relative paths against the canonical project output tree so stable
        # publication artifacts remain visible while source-scoped ignore rules
        # still exclude runtime state and render intermediates.
        copied_inventory = collect_stable_output_inventory(
            output_dir,
            git_ignore_output_dir=project_root / "output",
            git_ignore_path_overrides={
                Path(f"{Path(project_name).name}_combined.pdf"): Path("pdf") / f"{Path(project_name).name}_combined.pdf"
            },
            inventory_mode=inventory_mode,
        )

        # Step 4: Validate copied files
        validation_passed = validate_copied_outputs(
            output_dir,
            project_name=project_name,
            enabled_formats=formats,
            manuscript_dir=manuscript_dir,
            inventory=copied_inventory,
            slides_profile=render_config.slides_profile,
        )

        # Step 4b: Validate directory structure without inventing a PDF
        # requirement for configurations that explicitly disable it.
        structure_validation = validate_output_structure(
            output_dir,
            require_pdf=render_config.enable_pdf,
            inventory=copied_inventory,
            enabled_formats=formats,
        )

        # Step 5: Collect comprehensive output statistics
        output_stats = collect_output_statistics(
            repo_root,
            project_name,
            require_pdf=render_config.enable_pdf,
            output_dir=output_dir,
            inventory=copied_inventory,
            enabled_formats=formats,
            inventory_scope=STAGE5_DELIVERY_INVENTORY_SCOPE,
        )
        detailed_report = generate_detailed_output_report(output_dir, output_stats)

        logger.info(detailed_report)

        report_file, json_file = write_output_statistics_reports(
            project_root / "output",
            output_stats,
            report_output_dir=output_dir,
        )
        copied_report_file, copied_json_file = write_output_statistics_reports(
            output_dir,
            output_stats,
            report_output_dir=output_dir,
        )
        if report_file.read_bytes() != copied_report_file.read_bytes():
            raise ValueError("source and copied output-statistics text reports differ")
        if json_file.read_bytes() != copied_json_file.read_bytes():
            raise ValueError("source and copied output-statistics JSON reports differ")
        # The reports are part of the completed physical mirror but are
        # deliberately excluded from the stable inventory to avoid recursive
        # evidence. Recount only the physical total after both receipts exist
        # so first-run and repeat-run summaries have identical semantics.
        stats["total_files"] = sum(1 for path in output_dir.rglob("*") if path.is_file())
        stats["reports_files"] = sum(1 for path in (output_dir / "reports").rglob("*") if path.is_file())
        logger.info(f"Detailed output statistics saved to: {report_file}")
        logger.info(f"Output statistics JSON saved to: {json_file}")
        logger.info(
            "Physical local mirror: %d files; %s inventory: %d files",
            stats.get("total_files", 0),
            "Git-shippable publication"
            if copied_inventory.mode == STABLE_OUTPUT_INVENTORY_MODE
            else "stable-local project-output",
            output_stats["total_files"],
        )

        # Step 6: Log copy summary for the pipeline console
        log_output_summary(output_dir, dict(stats), structure_validation)

        if stats.get("total_files", 0) > 0 and validation_passed:
            inventory_label = (
                "Git-shippable publication inventory"
                if copied_inventory.mode == STABLE_OUTPUT_INVENTORY_MODE
                else "stable-local output inventory"
            )
            log_success(
                f"\n✅ Output copying complete - local mirror ready and {inventory_label} validated!",
                logger,
            )
            return 0
        logger.error("\n❌ Output copying incomplete - check warnings above")
        return 1

    except Exception as exc:
        logger.error(f"Unexpected error during output copying: {exc}", exc_info=True)
        return 1
