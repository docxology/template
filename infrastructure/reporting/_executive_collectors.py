"""Metric collectors for executive reporting.

Each ``collect_*`` function gathers metrics from a specific domain
(manuscript, codebase, tests, outputs, pipeline) by reading files and
reports from disk.  ``collect_project_metrics`` orchestrates all of them
for a single project.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from infrastructure.core.logging.utils import get_logger

from ._executive_models import (
    CodebaseMetrics,
    ManuscriptMetrics,
    OutputMetrics,
    PipelineMetrics,
    ProjectMetrics,
    TestMetrics,
)

logger = get_logger(__name__)


def collect_manuscript_metrics(manuscript_dir: Path) -> ManuscriptMetrics:
    """Collect manuscript metrics from markdown files.

    Args:
        manuscript_dir: Path to manuscript directory

    Returns:
        ManuscriptMetrics instance
    """
    metrics = ManuscriptMetrics()

    if not manuscript_dir.exists():
        logger.warning(f"Manuscript directory not found: {manuscript_dir}")
        return metrics

    md_files = list(manuscript_dir.glob("*.md"))
    metrics.markdown_files = [f.name for f in md_files]
    metrics.sections = len(md_files)

    for md_file in md_files:
        try:
            content = md_file.read_text(encoding="utf-8")

            # Count words (excluding code blocks and front matter)
            words = re.findall(r"\b\w+\b", content)
            metrics.total_words += len(words)

            # Count lines
            metrics.total_lines += len(content.splitlines())

            # Count equations ($$...$$ and \\[...\\])
            equations = re.findall(r"\$\$.*?\$\$", content, re.DOTALL)
            equations += re.findall(r"\\\[.*?\\\]", content, re.DOTALL)
            metrics.equations += len(equations)

            # Count figures (![...](...)
            figures = re.findall(r"!\[.*?\]\(.*?\)", content)
            metrics.figures += len(figures)

            # Count citations (@cite{...}, \\cite{...})
            citations = re.findall(r"@\w+|\\cite\{.*?\}", content)
            metrics.references += len(citations)

        except (OSError, UnicodeDecodeError) as e:  # noqa: BLE001 — best-effort; skip unreadable files
            logger.warning(f"Error processing {md_file.name}: {e}")

    return metrics


def collect_codebase_metrics(src_dir: Path, scripts_dir: Path | None = None) -> CodebaseMetrics:
    """Collect codebase metrics from source and script files.

    Args:
        src_dir: Path to source directory
        scripts_dir: Optional path to scripts directory

    Returns:
        CodebaseMetrics instance
    """
    import ast

    metrics = CodebaseMetrics()

    # Process source files
    if src_dir.exists():
        py_files = list(src_dir.glob("**/*.py"))
        metrics.source_files = len(py_files)

        for py_file in py_files:
            try:
                content = py_file.read_text(encoding="utf-8")

                # Count non-empty, non-comment lines
                lines = [l.strip() for l in content.splitlines()]
                code_lines = [l for l in lines if l and not l.startswith("#")]
                metrics.source_lines += len(code_lines)

                # Parse AST for methods and classes
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            metrics.methods += 1
                        elif isinstance(node, ast.ClassDef):
                            metrics.classes += 1
                except SyntaxError as e:
                    logger.debug(f"Syntax error parsing {py_file.name} for metrics: {e}")

            except (OSError, UnicodeDecodeError) as e:  # noqa: BLE001 — skip unreadable files in loop
                logger.warning(f"Error processing {py_file.name}: {e}")

    # Process script files
    if scripts_dir and scripts_dir.exists():
        script_files = list(scripts_dir.glob("*.py"))
        metrics.scripts = len(script_files)

        for script_file in script_files:
            try:
                content = script_file.read_text(encoding="utf-8")
                lines = [l.strip() for l in content.splitlines()]
                code_lines = [l for l in lines if l and not l.startswith("#")]
                metrics.script_lines += len(code_lines)
            except (OSError, UnicodeDecodeError) as e:  # noqa: BLE001 — skip unreadable files in loop
                logger.warning(f"Error processing {script_file.name}: {e}")

    return metrics


def collect_test_metrics(reports_dir: Path) -> TestMetrics:
    """Collect test metrics from test reports.

    Args:
        reports_dir: Path to reports directory

    Returns:
        TestMetrics instance
    """
    metrics = TestMetrics()

    test_report_path = reports_dir / "test_results.json"

    if not test_report_path.exists():
        logger.warning(
            f"Test report not found: {test_report_path} - test metrics will show as unavailable"
        )
        logger.info(f"Expected test report location: {test_report_path}")
        # Set a flag to indicate data is unavailable (using negative values to distinguish from actual 0s)  # noqa: E501
        metrics.total_tests = -1  # Special value to indicate "unavailable"
        return metrics

    try:
        # Log successful file discovery
        file_size = test_report_path.stat().st_size
        logger.debug(f"Found test report: {test_report_path} ({file_size} bytes)")

        with open(test_report_path) as f:
            report = json.load(f)

        logger.debug("Successfully loaded test report JSON")

        # Extract project test metrics
        project_tests = report.get("project", {})
        metrics.total_tests = project_tests.get("total", 0)
        metrics.passed = project_tests.get("passed", 0)
        metrics.failed = project_tests.get("failed", 0)
        metrics.skipped = project_tests.get("skipped", 0)
        metrics.coverage_percent = project_tests.get("coverage_percent", 0.0)

        # Execution time from summary
        summary = report.get("summary", {})
        metrics.execution_time = summary.get("total_execution_time", 0.0)

        # Count test files (estimate from tests/total ratio)
        if metrics.total_tests > 0:
            metrics.test_files = max(1, metrics.total_tests // 10)  # Rough estimate

        logger.debug(
            f"Successfully extracted test metrics: {metrics.total_tests} tests, {metrics.coverage_percent:.1f}% coverage"  # noqa: E501
        )

    except (OSError, json.JSONDecodeError, KeyError, ValueError) as e:  # noqa: BLE001 — return empty metrics if report absent
        logger.warning(f"Error loading test report: {e}")
        logger.debug("Exception details", exc_info=True)

    return metrics


def collect_output_metrics(output_dir: Path) -> OutputMetrics:
    """Collect output metrics from output directory.

    Args:
        output_dir: Path to output directory

    Returns:
        OutputMetrics instance
    """
    metrics = OutputMetrics()

    if not output_dir.exists():
        logger.warning(f"Output directory not found: {output_dir}")
        return metrics

    # Count PDFs
    pdf_dir = output_dir / "pdf"
    if pdf_dir.exists():
        pdf_files = list(pdf_dir.glob("*.pdf"))
        metrics.pdf_files = len(pdf_files)
        metrics.pdf_size_mb = sum(f.stat().st_size for f in pdf_files) / (1024 * 1024)

    # Count figures
    figures_dir = output_dir / "figures"
    if figures_dir.exists():
        figure_files = list(figures_dir.glob("*.png")) + list(figures_dir.glob("*.pdf"))
        metrics.figures = len(figure_files)

    # Count data files
    data_dir = output_dir / "data"
    if data_dir.exists():
        data_files = list(data_dir.glob("*"))
        metrics.data_files = len([f for f in data_files if f.is_file()])

    # Count slides
    slides_dir = output_dir / "slides"
    if slides_dir.exists():
        slide_files = list(slides_dir.glob("*.pdf"))
        metrics.slides = len(slide_files)

    # Count web outputs
    web_dir = output_dir / "web"
    if web_dir.exists():
        web_files = list(web_dir.glob("*.html"))
        metrics.web_outputs = len(web_files)

    # Total outputs
    metrics.total_outputs = (
        metrics.pdf_files
        + metrics.figures
        + metrics.data_files
        + metrics.slides
        + metrics.web_outputs
    )

    return metrics


def collect_pipeline_metrics(reports_dir: Path) -> PipelineMetrics:
    """Collect pipeline metrics from pipeline report.

    Args:
        reports_dir: Path to reports directory

    Returns:
        PipelineMetrics instance
    """
    metrics = PipelineMetrics()

    pipeline_report_path = reports_dir / "pipeline_report.json"
    if not pipeline_report_path.exists():
        logger.warning(f"Pipeline report not found: {pipeline_report_path}")
        return metrics

    try:
        with open(pipeline_report_path) as f:
            report = json.load(f)

        metrics.total_duration = report.get("total_duration", 0.0)

        # Count stages
        stages = report.get("stages", [])
        metrics.stages_passed = sum(1 for s in stages if s.get("status") == "passed")
        metrics.stages_failed = sum(1 for s in stages if s.get("status") == "failed")

        # Find bottleneck (slowest stage)
        if stages:
            slowest = max(stages, key=lambda s: s.get("duration", 0))
            metrics.bottleneck_stage = slowest.get("name", "")
            metrics.bottleneck_duration = slowest.get("duration", 0.0)
            if metrics.total_duration > 0:
                metrics.bottleneck_percent = (
                    metrics.bottleneck_duration / metrics.total_duration * 100
                )

    except (OSError, json.JSONDecodeError, KeyError, ValueError) as e:  # noqa: BLE001 — return empty metrics if report absent
        logger.warning(f"Error loading pipeline report: {e}")

    return metrics


def collect_project_metrics(
    repo_root: Path,
    project_name: str,
    project_dir: Path | None = None,
) -> ProjectMetrics:
    """Collect all metrics for a single project.

    Args:
        repo_root: Repository root path.
        project_name: Name of the project.
        project_dir: Absolute path to the project directory. When provided,
            overrides ``repo_root / 'projects' / project_name``.

    Returns:
        ProjectMetrics instance
    """
    project_root = project_dir if project_dir is not None else repo_root / "projects" / project_name

    logger.info(f"Collecting metrics for project: {project_name}")

    # Collect all metrics
    manuscript = collect_manuscript_metrics(project_root / "manuscript")
    codebase = collect_codebase_metrics(project_root / "src", project_root / "scripts")
    tests = collect_test_metrics(project_root / "output" / "reports")
    outputs = collect_output_metrics(repo_root / "output" / project_name)
    pipeline = collect_pipeline_metrics(project_root / "output" / "reports")

    return ProjectMetrics(
        name=project_name,
        manuscript=manuscript,
        codebase=codebase,
        tests=tests,
        outputs=outputs,
        pipeline=pipeline,
    )
