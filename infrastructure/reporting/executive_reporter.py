"""Executive reporter for cross-project metrics and summary generation.

This module collects comprehensive metrics across all projects and generates
executive summaries with aggregates, comparisons, and recommendations.

Part of the infrastructure reporting layer (Layer 1) - reusable across projects.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from infrastructure.core.logging_utils import get_logger
from infrastructure.reporting.output_organizer import OutputOrganizer, FileType

logger = get_logger(__name__)


@dataclass
class ManuscriptMetrics:
    """Manuscript metrics for a single project."""
    sections: int = 0
    total_words: int = 0
    total_lines: int = 0
    markdown_files: List[str] = field(default_factory=list)
    equations: int = 0
    figures: int = 0
    references: int = 0


@dataclass
class CodebaseMetrics:
    """Codebase metrics for a single project."""
    source_files: int = 0
    source_lines: int = 0
    scripts: int = 0
    script_lines: int = 0
    methods: int = 0
    classes: int = 0


@dataclass
class TestMetrics:
    """Test metrics for a single project."""
    test_files: int = 0
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    coverage_percent: float = 0.0
    execution_time: float = 0.0


@dataclass
class OutputMetrics:
    """Output metrics for a single project."""
    pdf_files: int = 0
    pdf_size_mb: float = 0.0
    figures: int = 0
    data_files: int = 0
    slides: int = 0
    web_outputs: int = 0
    total_outputs: int = 0


@dataclass
class PipelineMetrics:
    """Pipeline metrics for a single project."""
    total_duration: float = 0.0
    stages_passed: int = 0
    stages_failed: int = 0
    bottleneck_stage: str = ""
    bottleneck_duration: float = 0.0
    bottleneck_percent: float = 0.0


@dataclass
class ProjectMetrics:
    """Complete metrics for a single project."""
    name: str
    manuscript: ManuscriptMetrics
    codebase: CodebaseMetrics
    tests: TestMetrics
    outputs: OutputMetrics
    pipeline: PipelineMetrics


@dataclass
class ExecutiveSummary:
    """Executive summary aggregating all project metrics."""
    timestamp: str
    total_projects: int
    aggregate_metrics: Dict[str, Any]
    project_metrics: List[ProjectMetrics]
    health_scores: Dict[str, Any]  # Project health scores by project name
    comparative_tables: Dict[str, Any]
    recommendations: List[str]


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
            content = md_file.read_text(encoding='utf-8')
            
            # Count words (excluding code blocks and front matter)
            words = re.findall(r'\b\w+\b', content)
            metrics.total_words += len(words)
            
            # Count lines
            metrics.total_lines += len(content.splitlines())
            
            # Count equations ($$...$$ and \\[...\\])
            equations = re.findall(r'\$\$.*?\$\$', content, re.DOTALL)
            equations += re.findall(r'\\\[.*?\\\]', content, re.DOTALL)
            metrics.equations += len(equations)
            
            # Count figures (![...](...)
            figures = re.findall(r'!\[.*?\]\(.*?\)', content)
            metrics.figures += len(figures)
            
            # Count citations (@cite{...}, \\cite{...})
            citations = re.findall(r'@\w+|\\cite\{.*?\}', content)
            metrics.references += len(citations)
            
        except Exception as e:
            logger.warning(f"Error processing {md_file.name}: {e}")
    
    return metrics


def collect_codebase_metrics(src_dir: Path, scripts_dir: Optional[Path] = None) -> CodebaseMetrics:
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
                content = py_file.read_text(encoding='utf-8')
                
                # Count non-empty, non-comment lines
                lines = [l.strip() for l in content.splitlines()]
                code_lines = [l for l in lines if l and not l.startswith('#')]
                metrics.source_lines += len(code_lines)
                
                # Parse AST for methods and classes
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            metrics.methods += 1
                        elif isinstance(node, ast.ClassDef):
                            metrics.classes += 1
                except SyntaxError:
                    pass  # Skip files with syntax errors
                    
            except Exception as e:
                logger.warning(f"Error processing {py_file.name}: {e}")
    
    # Process script files
    if scripts_dir and scripts_dir.exists():
        script_files = list(scripts_dir.glob("*.py"))
        metrics.scripts = len(script_files)
        
        for script_file in script_files:
            try:
                content = script_file.read_text(encoding='utf-8')
                lines = [l.strip() for l in content.splitlines()]
                code_lines = [l for l in lines if l and not l.startswith('#')]
                metrics.script_lines += len(code_lines)
            except Exception as e:
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

    # Enhanced logging for debugging
    logger.debug(f"Checking for test results at: {test_report_path}")
    logger.debug(f"Reports directory exists: {reports_dir.exists()}")
    if reports_dir.exists():
        logger.debug(f"Reports directory contents: {list(reports_dir.iterdir())}")
    else:
        logger.warning(f"Reports directory does not exist: {reports_dir}")

    if not test_report_path.exists():
        logger.warning(f"Test report not found: {test_report_path} - test metrics will show as unavailable")
        logger.info(f"Expected test report location: {test_report_path}")
        # Set a flag to indicate data is unavailable (using negative values to distinguish from actual 0s)
        metrics.total_tests = -1  # Special value to indicate "unavailable"
        return metrics
    
    try:
        # Log successful file discovery
        file_size = test_report_path.stat().st_size
        logger.debug(f"Found test report: {test_report_path} ({file_size} bytes)")

        with open(test_report_path) as f:
            report = json.load(f)

        logger.debug(f"Successfully loaded test report JSON")

        # Extract project test metrics
        project_tests = report.get('project', {})
        metrics.total_tests = project_tests.get('total', 0)
        metrics.passed = project_tests.get('passed', 0)
        metrics.failed = project_tests.get('failed', 0)
        metrics.skipped = project_tests.get('skipped', 0)
        metrics.coverage_percent = project_tests.get('coverage_percent', 0.0)

        # Execution time from summary
        summary = report.get('summary', {})
        metrics.execution_time = summary.get('total_execution_time', 0.0)

        # Count test files (estimate from tests/total ratio)
        if metrics.total_tests > 0:
            metrics.test_files = max(1, metrics.total_tests // 10)  # Rough estimate

        logger.debug(f"Successfully extracted test metrics: {metrics.total_tests} tests, {metrics.coverage_percent:.1f}% coverage")

    except Exception as e:
        logger.warning(f"Error loading test report: {e}")
        logger.debug(f"Exception details", exc_info=True)
    
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
    metrics.total_outputs = (metrics.pdf_files + metrics.figures + 
                            metrics.data_files + metrics.slides + metrics.web_outputs)
    
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
        
        metrics.total_duration = report.get('total_duration', 0.0)
        
        # Count stages
        stages = report.get('stages', [])
        metrics.stages_passed = sum(1 for s in stages if s.get('status') == 'passed')
        metrics.stages_failed = sum(1 for s in stages if s.get('status') == 'failed')
        
        # Find bottleneck (slowest stage)
        if stages:
            slowest = max(stages, key=lambda s: s.get('duration', 0))
            metrics.bottleneck_stage = slowest.get('name', '')
            metrics.bottleneck_duration = slowest.get('duration', 0.0)
            if metrics.total_duration > 0:
                metrics.bottleneck_percent = (metrics.bottleneck_duration / 
                                             metrics.total_duration * 100)
        
    except Exception as e:
        logger.warning(f"Error loading pipeline report: {e}")
    
    return metrics


def collect_project_metrics(repo_root: Path, project_name: str) -> ProjectMetrics:
    """Collect all metrics for a single project.
    
    Args:
        repo_root: Repository root path
        project_name: Name of the project
        
    Returns:
        ProjectMetrics instance
    """
    project_root = repo_root / "projects" / project_name
    
    logger.info(f"Collecting metrics for project: {project_name}")
    
    # Collect all metrics
    manuscript = collect_manuscript_metrics(project_root / "manuscript")
    codebase = collect_codebase_metrics(
        project_root / "src",
        project_root / "scripts"
    )
    tests = collect_test_metrics(project_root / "output" / "reports")
    outputs = collect_output_metrics(repo_root / "output" / project_name)
    pipeline = collect_pipeline_metrics(project_root / "output" / "reports")
    
    return ProjectMetrics(
        name=project_name,
        manuscript=manuscript,
        codebase=codebase,
        tests=tests,
        outputs=outputs,
        pipeline=pipeline
    )


def generate_aggregate_metrics(projects: List[ProjectMetrics]) -> Dict[str, Any]:
    """Generate aggregate metrics across all projects.

    Args:
        projects: List of ProjectMetrics

    Returns:
        Dictionary of aggregate metrics with totals, averages, and min/max statistics
    """
    if not projects:
        return {}

    # Helper function to calculate statistics
    def calculate_stats(values: List[float]) -> Dict[str, float]:
        """Calculate min, max, median, and average for a list of values."""
        if not values:
            return {'min': 0.0, 'max': 0.0, 'median': 0.0, 'avg': 0.0}

        sorted_values = sorted(values)
        n = len(sorted_values)
        median = sorted_values[n // 2] if n % 2 == 1 else (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2

        return {
            'min': min(values),
            'max': max(values),
            'median': median,
            'avg': sum(values) / len(values)
        }

    # Collect values for statistics
    manuscript_words = [p.manuscript.total_words for p in projects]

    # Filter out projects with unavailable test data (total_tests = -1)
    available_test_projects = [p for p in projects if p.tests.total_tests >= 0]
    test_coverage = [p.tests.coverage_percent for p in available_test_projects] if available_test_projects else [0.0]
    pipeline_durations = [p.pipeline.total_duration for p in projects]

    aggregates = {
        'manuscript': {
            'total_words': sum(manuscript_words),
            'total_sections': sum(p.manuscript.sections for p in projects),
            'total_equations': sum(p.manuscript.equations for p in projects),
            'total_figures': sum(p.manuscript.figures for p in projects),
            'total_references': sum(p.manuscript.references for p in projects),
            'words_stats': calculate_stats(manuscript_words),
        },
        'codebase': {
            'total_source_lines': sum(p.codebase.source_lines for p in projects),
            'total_methods': sum(p.codebase.methods for p in projects),
            'total_classes': sum(p.codebase.classes for p in projects),
            'total_scripts': sum(p.codebase.scripts for p in projects),
        },
        'tests': {
            'total_tests': sum(p.tests.total_tests for p in available_test_projects) if available_test_projects else 0,
            'total_passed': sum(p.tests.passed for p in available_test_projects) if available_test_projects else 0,
            'total_failed': sum(p.tests.failed for p in available_test_projects) if available_test_projects else 0,
            'average_coverage': sum(test_coverage) / len(available_test_projects) if available_test_projects else 0.0,
            'coverage_stats': calculate_stats(test_coverage),
            'total_execution_time': sum(p.tests.execution_time for p in available_test_projects) if available_test_projects else 0.0,
            'projects_with_test_data': len(available_test_projects),
            'total_projects': len(projects),
        },
        'outputs': {
            'total_pdfs': sum(p.outputs.pdf_files for p in projects),
            'total_size_mb': sum(p.outputs.pdf_size_mb for p in projects),
            'total_figures': sum(p.outputs.figures for p in projects),
            'total_slides': sum(p.outputs.slides for p in projects),
            'total_web': sum(p.outputs.web_outputs for p in projects),
        },
        'pipeline': {
            'total_duration': sum(pipeline_durations),
            'average_duration': sum(pipeline_durations) / len(projects),
            'duration_stats': calculate_stats(pipeline_durations),
            'total_stages_passed': sum(p.pipeline.stages_passed for p in projects),
            'total_stages_failed': sum(p.pipeline.stages_failed for p in projects),
        }
    }

    return aggregates


def calculate_project_health_score(project: ProjectMetrics) -> Dict[str, Any]:
    """Calculate a health score for a project based on its metrics.

    Args:
        project: ProjectMetrics instance

    Returns:
        Dictionary with health score and breakdown
    """
    score = 0
    max_score = 0
    factors = {}

    # Test coverage (40% weight)
    if project.tests.coverage_percent >= 90:
        factors['test_coverage'] = {'score': 40, 'grade': 'A', 'reason': 'Excellent coverage ≥90%'}
        score += 40
    elif project.tests.coverage_percent >= 80:
        factors['test_coverage'] = {'score': 30, 'grade': 'B', 'reason': 'Good coverage ≥80%'}
        score += 30
    elif project.tests.coverage_percent >= 70:
        factors['test_coverage'] = {'score': 20, 'grade': 'C', 'reason': 'Adequate coverage ≥70%'}
        score += 20
    else:
        factors['test_coverage'] = {'score': 0, 'grade': 'F', 'reason': 'Poor coverage <70%'}
        score += 0
    max_score += 40

    # Test failure rate (30% weight)
    if project.tests.total_tests > 0:
        failure_rate = project.tests.failed / project.tests.total_tests
        if failure_rate == 0:
            factors['test_failures'] = {'score': 30, 'grade': 'A', 'reason': 'No test failures'}
            score += 30
        elif failure_rate <= 0.05:
            factors['test_failures'] = {'score': 25, 'grade': 'B', 'reason': f'Low failure rate {failure_rate:.1%}'}
            score += 25
        elif failure_rate <= 0.10:
            factors['test_failures'] = {'score': 20, 'grade': 'C', 'reason': f'Moderate failure rate {failure_rate:.1%}'}
            score += 20
        else:
            factors['test_failures'] = {'score': 0, 'grade': 'F', 'reason': f'High failure rate {failure_rate:.1%}'}
            score += 0
    else:
        factors['test_failures'] = {'score': 0, 'grade': 'F', 'reason': 'No tests found'}
    max_score += 30

    # Manuscript completeness (20% weight)
    if project.manuscript.total_words >= 2000:
        factors['manuscript_size'] = {'score': 20, 'grade': 'A', 'reason': f'Comprehensive manuscript ({project.manuscript.total_words} words)'}
        score += 20
    elif project.manuscript.total_words >= 1000:
        factors['manuscript_size'] = {'score': 15, 'grade': 'B', 'reason': f'Good manuscript ({project.manuscript.total_words} words)'}
        score += 15
    elif project.manuscript.total_words >= 500:
        factors['manuscript_size'] = {'score': 10, 'grade': 'C', 'reason': f'Basic manuscript ({project.manuscript.total_words} words)'}
        score += 10
    else:
        factors['manuscript_size'] = {'score': 0, 'grade': 'F', 'reason': f'Insufficient manuscript ({project.manuscript.total_words} words)'}
        score += 0
    max_score += 20

    # Output generation (10% weight)
    outputs_generated = (project.outputs.pdf_files + project.outputs.figures +
                        project.outputs.slides + project.outputs.web_outputs)
    if outputs_generated >= 10:
        factors['outputs'] = {'score': 10, 'grade': 'A', 'reason': f'Rich outputs ({outputs_generated} files)'}
        score += 10
    elif outputs_generated >= 5:
        factors['outputs'] = {'score': 7, 'grade': 'B', 'reason': f'Good outputs ({outputs_generated} files)'}
        score += 7
    elif outputs_generated >= 2:
        factors['outputs'] = {'score': 4, 'grade': 'C', 'reason': f'Basic outputs ({outputs_generated} files)'}
        score += 4
    else:
        factors['outputs'] = {'score': 0, 'grade': 'F', 'reason': f'Limited outputs ({outputs_generated} files)'}
        score += 0
    max_score += 10

    # Calculate overall grade
    percentage = (score / max_score * 100) if max_score > 0 else 0
    if percentage >= 90:
        grade = 'A'
        status = 'Excellent'
    elif percentage >= 80:
        grade = 'B'
        status = 'Good'
    elif percentage >= 70:
        grade = 'C'
        status = 'Fair'
    elif percentage >= 60:
        grade = 'D'
        status = 'Poor'
    else:
        grade = 'F'
        status = 'Critical'

    return {
        'score': score,
        'max_score': max_score,
        'percentage': percentage,
        'grade': grade,
        'status': status,
        'factors': factors
    }


def generate_comparative_tables(projects: List[ProjectMetrics]) -> Dict[str, Any]:
    """Generate comparative tables for all projects.
    
    Args:
        projects: List of ProjectMetrics
        
    Returns:
        Dictionary of comparative tables
    """
    tables = {
        'manuscript_comparison': [
            {
                'project': p.name,
                'words': p.manuscript.total_words,
                'sections': p.manuscript.sections,
                'equations': p.manuscript.equations,
                'figures': p.manuscript.figures,
            }
            for p in projects
        ],
        'test_comparison': [
            {
                'project': p.name,
                'tests': p.tests.total_tests,
                'passed': p.tests.passed,
                'coverage': f"{p.tests.coverage_percent:.1f}%",
                'time': f"{p.tests.execution_time:.1f}s",
            }
            for p in projects
        ],
        'output_comparison': [
            {
                'project': p.name,
                'pdfs': p.outputs.pdf_files,
                'size_mb': f"{p.outputs.pdf_size_mb:.1f}",
                'figures': p.outputs.figures,
                'slides': p.outputs.slides,
            }
            for p in projects
        ],
        'pipeline_comparison': [
            {
                'project': p.name,
                'duration': f"{p.pipeline.total_duration:.0f}s",
                'bottleneck': p.pipeline.bottleneck_stage,
                'bottleneck_pct': f"{p.pipeline.bottleneck_percent:.0f}%",
            }
            for p in projects
        ]
    }
    
    return tables


def generate_recommendations(projects: List[ProjectMetrics]) -> List[str]:
    """Generate actionable recommendations based on comprehensive project metrics analysis.

    Args:
        projects: List of ProjectMetrics

    Returns:
        List of detailed, actionable recommendation strings
    """
    recommendations = []

    # Calculate health scores for projects
    health_scores = [(p.name, calculate_project_health_score(p)) for p in projects]
    health_scores.sort(key=lambda x: x[1]['score'], reverse=True)

    # Overall portfolio health
    avg_health = sum(score['percentage'] for _, score in health_scores) / len(health_scores)
    if avg_health >= 85:
        recommendations.append("🎉 **Portfolio Health**: Excellent overall project health across all metrics.")
    elif avg_health >= 70:
        recommendations.append("✅ **Portfolio Health**: Good overall project health with room for improvement.")
    else:
        recommendations.append("⚠️ **Portfolio Health**: Portfolio requires attention to improve overall health.")

    # Critical issues (F grades)
    critical_projects = [name for name, score in health_scores if score['grade'] == 'F']
    if critical_projects:
        recommendations.append(
            f"🚨 **Critical Issues**: {', '.join(critical_projects)} require immediate attention. "
            "Review failing tests, missing manuscripts, and incomplete outputs."
        )

    # Test coverage analysis with specific recommendations
    coverage_stats = [p.tests.coverage_percent for p in projects]
    low_coverage = [p for p in projects if p.tests.coverage_percent < 90]
    if low_coverage:
        worst_coverage = min(coverage_stats)
        project_names = ', '.join(p.name for p in low_coverage)
        recommendations.append(
            f"📊 **Test Coverage**: {project_names} below 90% threshold (lowest: {worst_coverage:.1f}%). "
            "Action: Add unit tests for uncovered functions, especially in `src/` modules. "
            "Target: Aim for 95%+ coverage for critical functionality."
        )
    else:
        recommendations.append(
            "✅ **Test Coverage**: All projects meet or exceed 90% coverage threshold. "
            "Maintain this standard with comprehensive test suites."
        )

    # Test failure analysis with specific guidance
    failed_tests = [p for p in projects if p.tests.failed > 0]
    if failed_tests:
        for p in failed_tests:
            failure_rate = p.tests.failed / p.tests.total_tests if p.tests.total_tests > 0 else 1.0
            if failure_rate > 0.1:
                recommendations.append(
                    f"❌ **Critical Test Failures**: {p.name} has {failure_rate:.1%} failure rate "
                    f"({p.tests.failed}/{p.tests.total_tests} tests). "
                    "Action: Stop development and fix failing tests immediately. "
                    "Check test logs and fix assertion failures or runtime errors."
                )
            else:
                recommendations.append(
                    f"⚠️ **Test Failures**: {p.name} has {p.tests.failed} failing test(s). "
                    "Action: Review test output for details and fix failures before release."
                )
    else:
        recommendations.append("✅ **Test Integrity**: All tests passing across all projects.")

    # Performance bottlenecks with specific recommendations
    slow_projects = [p for p in projects if p.pipeline.bottleneck_percent > 50]
    if slow_projects:
        for p in slow_projects:
            stage = p.pipeline.bottleneck_stage
            if stage == "PDF Rendering":
                recommendations.append(
                    f"⏱️ **PDF Performance**: {p.name} bottleneck in LaTeX compilation. "
                    "Action: Check for complex equations or large figures. Consider using lighter LaTeX packages "
                    "or optimizing figure resolution."
                )
            elif stage == "Infrastructure Tests":
                recommendations.append(
                    f"⏱️ **Test Performance**: {p.name} slow test execution. "
                    "Action: Optimize slow tests, consider parallel execution, review computationally intensive tests."
                )
            elif stage == "Project Analysis":
                recommendations.append(
                    f"⏱️ **Analysis Performance**: {p.name} slow analysis scripts. "
                    "Action: Profile analysis_pipeline.py, optimize data processing, cache intermediate results."
                )
            else:
                recommendations.append(
                    f"⏱️ **Performance**: {p.name} bottleneck in {stage} "
                    f"({p.pipeline.bottleneck_percent:.0f}% of time). "
                    "Action: Review and optimize the slowest stage."
                )

    # Manuscript quality analysis
    manuscript_issues = []
    for p in projects:
        if p.manuscript.total_words < 500:
            manuscript_issues.append(f"{p.name} (only {p.manuscript.total_words} words - critically insufficient)")
        elif p.manuscript.total_words < 1000:
            manuscript_issues.append(f"{p.name} ({p.manuscript.total_words} words - needs expansion)")

    if manuscript_issues:
        recommendations.append(
            "📝 **Manuscript Completeness**: " + "; ".join(manuscript_issues) + ". "
            "Action: Expand content to meet academic standards (target: 1000+ words). "
            "Add methodology details, results discussion, and conclusion sections."
        )

    # Output richness analysis
    output_poor = []
    for p in projects:
        total_outputs = (p.outputs.pdf_files + p.outputs.figures +
                        p.outputs.slides + p.outputs.web_outputs)
        if total_outputs < 3:
            output_poor.append(f"{p.name} ({total_outputs} outputs)")

    if output_poor:
        recommendations.append(
            "🎨 **Output Richness**: " + ", ".join(output_poor) + " have limited outputs. "
            "Action: Generate more visual outputs (figures, slides, web versions). "
            "Enhance analysis_pipeline.py to produce comprehensive results."
        )

    # Best practices and optimization opportunities
    if len(projects) > 1:
        # Compare projects and suggest improvements
        best_coverage = max(p.tests.coverage_percent for p in projects)
        best_project = next(p.name for p in projects if p.tests.coverage_percent == best_coverage)

        if best_coverage > 95:
            recommendations.append(
                f"🏆 **Best Practice**: {best_project} demonstrates excellent test coverage ({best_coverage:.1f}%). "
                "Action: Study this project's testing approach and apply lessons to other projects."
            )

        # Manuscript size comparison
        largest_manuscript = max(p.manuscript.total_words for p in projects)
        largest_project = next(p.name for p in projects if p.manuscript.total_words == largest_manuscript)

        if largest_manuscript > 2000:
            recommendations.append(
                f"📚 **Comprehensive Research**: {largest_project} has extensive manuscript ({largest_manuscript:,} words). "
                "Consider if other projects could benefit from similar depth."
            )

    # Code quality insights
    total_classes = sum(p.codebase.classes for p in projects)
    total_methods = sum(p.codebase.methods for p in projects)
    if total_classes > 0 and total_methods > 0:
        avg_methods_per_class = total_methods / total_classes
        if avg_methods_per_class < 3:
            recommendations.append(
                f"🏗️ **Code Structure**: Low average methods per class ({avg_methods_per_class:.1f}). "
                "Action: Consider refactoring to improve encapsulation and modularity."
            )

    return recommendations


def generate_executive_summary(repo_root: Path, project_names: List[str]) -> ExecutiveSummary:
    """Generate complete executive summary for all projects.
    
    Args:
        repo_root: Repository root path
        project_names: List of project names to include
        
    Returns:
        ExecutiveSummary instance
    """
    logger.info(f"Generating executive summary for {len(project_names)} project(s)")
    
    # Collect metrics for all projects
    project_metrics = []
    for project_name in project_names:
        try:
            metrics = collect_project_metrics(repo_root, project_name)
            project_metrics.append(metrics)
        except Exception as e:
            logger.error(f"Error collecting metrics for {project_name}: {e}")
    
    # Generate aggregates, comparisons, recommendations
    aggregates = generate_aggregate_metrics(project_metrics)
    comparatives = generate_comparative_tables(project_metrics)
    recommendations = generate_recommendations(project_metrics)

    # Calculate health scores for all projects
    health_scores = {p.name: calculate_project_health_score(p) for p in project_metrics}

    summary = ExecutiveSummary(
        timestamp=datetime.now().isoformat(),
        total_projects=len(project_metrics),
        aggregate_metrics=aggregates,
        project_metrics=project_metrics,
        health_scores=health_scores,
        comparative_tables=comparatives,
        recommendations=recommendations
    )
    
    logger.info("Executive summary generated successfully")
    return summary


def save_executive_summary(summary: ExecutiveSummary, output_dir: Path) -> Dict[str, Path]:
    """Save executive summary in multiple formats.
    
    Args:
        summary: ExecutiveSummary instance
        output_dir: Output directory path
        
    Returns:
        Dictionary mapping format to saved file path
    """
    organizer = OutputOrganizer()
    organizer.ensure_directory_structure(output_dir)
    saved_files = {}

    # Save JSON (machine-readable)
    json_path = organizer.get_output_path("consolidated_report.json", output_dir, FileType.JSON)
    with open(json_path, 'w') as f:
        json.dump(asdict(summary), f, indent=2, default=str)
    saved_files['json'] = json_path
    logger.info(f"Saved JSON report: {json_path}")

    # Save Markdown (human-readable)
    md_path = organizer.get_output_path("consolidated_report.md", output_dir, FileType.MARKDOWN)
    md_content = _generate_markdown_report(summary)
    md_path.write_text(md_content)
    saved_files['markdown'] = md_path
    logger.info(f"Saved Markdown report: {md_path}")

    # Save HTML (styled)
    html_path = organizer.get_output_path("consolidated_report.html", output_dir, FileType.HTML)
    html_content = _generate_html_report(summary)
    html_path.write_text(html_content)
    saved_files['html'] = html_path
    logger.info(f"Saved HTML report: {html_path}")
    
    return saved_files


def _generate_markdown_report(summary: ExecutiveSummary) -> str:
    """Generate Markdown format executive report."""
    lines = [
        "# Executive Summary - All Projects",
        "",
        f"**Generated**: {summary.timestamp}",
        f"**Total Projects**: {summary.total_projects}",
        "",
        "## Executive Overview",
        "",
    ]

    # Generate key insights
    manuscript_words = summary.aggregate_metrics['manuscript']['total_words']
    total_projects = summary.total_projects
    avg_project_size = manuscript_words / total_projects if total_projects > 0 else 0

    # Identify best and worst performers
    projects_by_size = sorted(summary.project_metrics, key=lambda p: p.manuscript.total_words, reverse=True)
    largest_project = projects_by_size[0] if projects_by_size else None
    smallest_project = projects_by_size[-1] if len(projects_by_size) > 1 else None

    projects_by_efficiency = sorted(summary.project_metrics,
                                   key=lambda p: p.outputs.total_outputs / max(p.pipeline.total_duration, 1))
    most_efficient = projects_by_efficiency[-1] if projects_by_efficiency else None

    lines.extend([
        "### Key Findings",
        f"- **Portfolio Size**: {manuscript_words:,} total manuscript words across {total_projects} projects",
        f"- **Average Project**: {avg_project_size:,.0f} words per project",
    ])

    if largest_project:
        lines.append(f"- **Largest Project**: {largest_project.name} ({largest_project.manuscript.total_words:,} words)")

    if smallest_project and smallest_project != largest_project:
        lines.append(f"- **Smallest Project**: {smallest_project.name} ({smallest_project.manuscript.total_words:,} words)")

    if most_efficient:
        efficiency = most_efficient.outputs.total_outputs / max(most_efficient.pipeline.total_duration, 1)
        lines.append(f"- **Most Efficient**: {most_efficient.name} ({efficiency:.2f} outputs/second)")

    # Health assessment
    failing_projects = [p.name for p in summary.project_metrics
                       if summary.health_scores.get(p.name, {}).get('percentage', 0) < 70]
    if failing_projects:
        lines.extend([
            "",
            "### Critical Issues",
            f"⚠️ **{len(failing_projects)} projects** require immediate attention:",
        ])
        for project in failing_projects:
            health = summary.health_scores.get(project, {})
            grade = health.get('grade', 'Unknown')
            lines.append(f"- **{project}**: {grade} health grade")
    else:
        lines.append("\n### Health Status\n✅ **All projects** are in good health")

    lines.extend([
        "",
        "## Aggregate Metrics",
        "",
        "### Manuscript",
        f"- **Total Words**: {summary.aggregate_metrics['manuscript']['total_words']:,}",
        f"- **Total Sections**: {summary.aggregate_metrics['manuscript']['total_sections']}",
        f"- **Total Equations**: {summary.aggregate_metrics['manuscript']['total_equations']}",
        f"- **Total Figures**: {summary.aggregate_metrics['manuscript']['total_figures']}",
        f"- **Total References**: {summary.aggregate_metrics['manuscript']['total_references']}",
        "",
        "### Codebase",
        f"- **Source Lines**: {summary.aggregate_metrics['codebase']['total_source_lines']:,}",
        f"- **Methods**: {summary.aggregate_metrics['codebase']['total_methods']}",
        f"- **Classes**: {summary.aggregate_metrics['codebase']['total_classes']}",
        f"- **Scripts**: {summary.aggregate_metrics['codebase']['total_scripts']}",
        "",
        "### Testing",
    ])

    test_metrics = summary.aggregate_metrics['tests']
    projects_with_data = test_metrics.get('projects_with_test_data', 0)
    total_projects = test_metrics.get('total_projects', summary.total_projects)

    if projects_with_data > 0:
        lines.extend([
            f"- **Total Tests**: {test_metrics['total_tests']} ({test_metrics['total_passed']} passed)",
            f"- **Average Coverage**: {test_metrics['average_coverage']:.1f}%",
            f"- **Total Execution Time**: {test_metrics['total_execution_time']:.1f}s",
            f"- **Projects with Test Data**: {projects_with_data}/{total_projects}",
            "",
        ])
    else:
        lines.extend([
            f"- **Test Data**: Unavailable for all {total_projects} projects",
            f"- **Note**: Run test stage first to generate test metrics",
            "",
        ])

    lines.extend([
        "",
        "### Outputs",
        f"- **PDFs**: {summary.aggregate_metrics['outputs']['total_pdfs']} files ({summary.aggregate_metrics['outputs']['total_size_mb']:.1f} MB)",
        f"- **Figures**: {summary.aggregate_metrics['outputs']['total_figures']}",
        f"- **Slides**: {summary.aggregate_metrics['outputs']['total_slides']}",
        f"- **Web Pages**: {summary.aggregate_metrics['outputs']['total_web']}",
        "",
        "### Pipeline",
        f"- **Total Duration**: {summary.aggregate_metrics['pipeline']['total_duration']:.0f}s",
        f"- **Average Duration**: {summary.aggregate_metrics['pipeline']['average_duration']:.0f}s",
        f"- **Stages Passed**: {summary.aggregate_metrics['pipeline']['total_stages_passed']}",
        "",
        "## Project Comparison",
        "",
        "| Project | Words | Tests | Coverage | Duration | PDF Size |",
        "|---------|-------|-------|----------|----------|----------|",
    ])
    
    for p in summary.project_metrics:
        lines.append(
            f"| {p.name} | {p.manuscript.total_words:,} | {p.tests.total_tests} | "
            f"{p.tests.coverage_percent:.1f}% | {p.pipeline.total_duration:.0f}s | "
            f"{p.outputs.pdf_size_mb:.1f} MB |"
        )
    
    # Add totals row
    lines.append(
        f"| **TOTAL** | **{summary.aggregate_metrics['manuscript']['total_words']:,}** | "
        f"**{summary.aggregate_metrics['tests']['total_tests']}** | "
        f"**{summary.aggregate_metrics['tests']['average_coverage']:.1f}%** | "
        f"**{summary.aggregate_metrics['pipeline']['total_duration']:.0f}s** | "
        f"**{summary.aggregate_metrics['outputs']['total_size_mb']:.1f} MB** |"
    )
    
    # Enhanced recommendations with prioritization
    lines.extend(["", "## Actionable Recommendations", ""])

    # Categorize and prioritize recommendations
    high_priority = []
    medium_priority = []
    low_priority = []

    for rec in summary.recommendations:
        if any(keyword in rec.lower() for keyword in ['critical', 'immediate', 'failing', 'broken']):
            high_priority.append(f"🚨 **HIGH**: {rec}")
        elif any(keyword in rec.lower() for keyword in ['below', 'improve', 'consider']):
            medium_priority.append(f"⚠️ **MEDIUM**: {rec}")
        else:
            low_priority.append(f"ℹ️ **LOW**: {rec}")

    if high_priority:
        lines.extend(["### High Priority", ""] + high_priority + [""])

    if medium_priority:
        lines.extend(["### Medium Priority", ""] + medium_priority + [""])

    if low_priority:
        lines.extend(["### Low Priority", ""] + low_priority + [""])

    # Add visual dashboard references
    lines.extend([
        "",
        "## Visual Dashboards",
        "",
        "Comprehensive visual analysis is available in the executive_summary directory:",
        "",
        "### Health & Quality",
        "- `health_scores_radar.png/pdf` - Multi-dimensional health analysis",
        "- `health_scores_comparison.png/pdf` - Health score breakdown by factor",
        "",
        "### Project Details",
        "- `project_dashboard_{name}.png/pdf` - Individual project overviews",
        "- `consolidated_report.html` - Interactive web report",
        "",
        "### Performance Analysis",
        "- `pipeline_efficiency.png/pdf` - Pipeline performance metrics",
        "- `pipeline_bottlenecks.png/pdf` - Bottleneck identification",
        "",
        "### Output Analysis",
        "- `output_distribution.png/pdf` - Output generation analysis",
        "- `output_comparison.png/pdf` - Cross-project output comparison",
        "",
        "### Codebase Analysis",
        "- `codebase_complexity.png/pdf` - Code complexity metrics",
        "- `codebase_comparison.png/pdf` - Codebase structure comparison"
    ])
    
    return "\n".join(lines)


def _generate_html_report(summary: ExecutiveSummary) -> str:
    """Generate HTML format executive report."""
    from infrastructure.reporting.html_templates import (
        get_base_html_template, render_summary_cards, render_table
    )

    # Generate header content
    header_html = f"""        <h1>Executive Summary - All Projects</h1>
        <p><strong>Generated:</strong> {summary.timestamp}</p>
        <p><strong>Total Projects:</strong> {summary.total_projects}</p>"""

    # Generate summary cards
    test_metrics = summary.aggregate_metrics['tests']
    projects_with_data = test_metrics.get('projects_with_test_data', 0)

    cards = [
        {"title": "Total Projects", "value": str(summary.total_projects)},
        {"title": "Total Manuscript Words", "value": f"{summary.aggregate_metrics['manuscript']['total_words']:,}"},
    ]

    if projects_with_data > 0:
        cards.extend([
            {"title": "Total Tests", "value": f"{test_metrics['total_tests']}"},
            {"title": "Average Coverage", "value": f"{test_metrics['average_coverage']:.1f}%"}
        ])
    else:
        cards.extend([
            {"title": "Test Data", "value": "Unavailable"},
            {"title": "Coverage", "value": "N/A"}
        ])
    summary_cards_html = render_summary_cards(cards)

    # Generate comparative table
    headers = ["Project", "Words", "Tests", "Coverage", "Duration", "PDF Size"]
    rows = []
    for project in summary.project_metrics:
        rows.append([
            project.name,
            f"{project.manuscript.total_words:,}",
            str(project.tests.total_tests),
            f"{project.tests.coverage_percent:.1f}%",
            f"{project.pipeline.total_duration:.0f}s",
            ".2f"
        ])

    comparison_table_html = render_table(headers, rows)

    # Convert recommendations to HTML list
    recommendations_html = "<ul>\n"
    for rec in summary.recommendations:
        recommendations_html += f"        <li>{rec}</li>\n"
    recommendations_html += "    </ul>"

    # Generate executive overview
    manuscript_words = summary.aggregate_metrics['manuscript']['total_words']
    avg_project_size = manuscript_words / summary.total_projects if summary.total_projects > 0 else 0

    # Find best/worst performers
    projects_by_size = sorted(summary.project_metrics, key=lambda p: p.manuscript.total_words, reverse=True)
    largest_project = projects_by_size[0] if projects_by_size else None

    overview_html = f"""
        <div class="section">
            <h2>Executive Overview</h2>
            <div class="summary-grid">
                <div class="summary-card">
                    <h3>Total Portfolio</h3>
                    <div class="value">{manuscript_words:,} words</div>
                </div>
                <div class="summary-card">
                    <h3>Average Project</h3>
                    <div class="value">{avg_project_size:,.0f} words</div>
                </div>
                <div class="summary-card">
                    <h3>Projects Analyzed</h3>
                    <div class="value">{summary.total_projects}</div>
                </div>
    """

    if largest_project:
        overview_html += f"""
                <div class="summary-card">
                    <h3>Largest Project</h3>
                    <div class="value">{largest_project.name}</div>
                </div>
        """

    overview_html += "        </div>\n        </div>"

    # Enhanced recommendations with prioritization
    high_priority = []
    medium_priority = []
    low_priority = []

    for rec in summary.recommendations:
        if any(keyword in rec.lower() for keyword in ['critical', 'immediate', 'failing', 'broken']):
            high_priority.append(f'<li class="status-failed">{rec}</li>')
        elif any(keyword in rec.lower() for keyword in ['below', 'improve', 'consider']):
            medium_priority.append(f'<li class="status-warning">{rec}</li>')
        else:
            low_priority.append(f'<li class="status-passed">{rec}</li>')

    recommendations_html = '<div class="section"><h2>Actionable Recommendations</h2>'

    if high_priority:
        recommendations_html += '<h3>🚨 High Priority</h3><ul>' + ''.join(high_priority) + '</ul>'

    if medium_priority:
        recommendations_html += '<h3>⚠️ Medium Priority</h3><ul>' + ''.join(medium_priority) + '</ul>'

    if low_priority:
        recommendations_html += '<h3>ℹ️ Low Priority</h3><ul>' + ''.join(low_priority) + '</ul>'

    recommendations_html += '</div>'

    # Add visual dashboard section
    dashboard_html = """
        <div class="section">
            <h2>Visual Dashboards</h2>
            <p>Comprehensive visual analysis is available:</p>
            <ul>
                <li><strong>Health & Quality:</strong> health_scores_radar.png/pdf, health_scores_comparison.png/pdf</li>
                <li><strong>Project Details:</strong> project_dashboard_{name}.png/pdf, consolidated_report.html</li>
                <li><strong>Performance:</strong> pipeline_efficiency.png/pdf, pipeline_bottlenecks.png/pdf</li>
                <li><strong>Outputs:</strong> output_distribution.png/pdf, output_comparison.png/pdf</li>
                <li><strong>Codebase:</strong> codebase_complexity.png/pdf, codebase_comparison.png/pdf</li>
            </ul>
        </div>
    """

    # Generate main content
    content_html = f"""
        {overview_html}

        <div class="section">
            <h2>Key Metrics</h2>
            {summary_cards_html}
        </div>

        <div class="section">
            <h2>Project Comparison</h2>
            {comparison_table_html}
        </div>

        {recommendations_html}

        {dashboard_html}
    """

    # Generate footer content
    footer_html = f"""        <p>Generated by Research Template Executive Reporter</p>
        <p>Timestamp: {summary.timestamp}</p>"""

    # Get base template and fill placeholders
    html = get_base_html_template()
    html = html.replace("{title}", "Executive Summary - All Projects")
    html = html.replace("{header}", header_html)
    html = html.replace("{content}", content_html)
    html = html.replace("{footer}", footer_html)

    return html
