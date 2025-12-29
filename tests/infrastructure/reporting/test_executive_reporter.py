"""Tests for executive reporter module.

Tests comprehensive metrics collection across projects and executive summary generation.
"""
import json
import tempfile
from pathlib import Path

import pytest

from infrastructure.reporting.executive_reporter import (
    ManuscriptMetrics,
    CodebaseMetrics,
    TestMetrics,
    OutputMetrics,
    PipelineMetrics,
    ProjectMetrics,
    ExecutiveSummary,
    collect_manuscript_metrics,
    collect_codebase_metrics,
    collect_test_metrics,
    collect_output_metrics,
    collect_pipeline_metrics,
    collect_project_metrics,
    generate_aggregate_metrics,
    generate_comparative_tables,
    generate_recommendations,
    generate_executive_summary,
    save_executive_summary,
)


@pytest.fixture
def temp_manuscript_dir(tmp_path):
    """Create temporary manuscript directory with test files."""
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    
    # Create test markdown files
    (manuscript_dir / "01_intro.md").write_text(
        "# Introduction\n\nThis is a test manuscript with 15 words in it for testing purposes.\n\n"
        "$$\n\\alpha = \\beta\n$$\n\n"
        "![Test Figure](figures/test.png)\n\n"
        "@cite{ref1}\n"
    )
    
    (manuscript_dir / "02_methods.md").write_text(
        "# Methods\n\nAnother section with 10 words for testing metrics collection.\n\n"
        "\\[x = y + z\\]\n"
    )
    
    return manuscript_dir


@pytest.fixture
def temp_src_dir(tmp_path):
    """Create temporary source directory with test files."""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    
    # Create test Python files
    (src_dir / "module1.py").write_text(
        "class TestClass:\n"
        "    def method1(self):\n"
        "        pass\n"
        "\n"
        "def function1():\n"
        "    pass\n"
    )
    
    (src_dir / "module2.py").write_text(
        "# Comment\n"
        "\n"
        "def function2():\n"
        "    return 42\n"
    )
    
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "script1.py").write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        "print('test')\n"
    )
    
    return src_dir, scripts_dir


@pytest.fixture
def temp_reports_dir(tmp_path):
    """Create temporary reports directory with test reports."""
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    
    # Create test report
    test_report = {
        "project": {
            "total": 100,
            "passed": 95,
            "failed": 5,
            "skipped": 0,
            "coverage_percent": 92.5,
        },
        "summary": {
            "total_execution_time": 45.2,
        }
    }
    
    (reports_dir / "test_results.json").write_text(json.dumps(test_report, indent=2))
    
    # Create pipeline report
    pipeline_report = {
        "total_duration": 120.5,
        "stages": [
            {"name": "setup", "status": "passed", "duration": 5.0},
            {"name": "tests", "status": "passed", "duration": 45.2},
            {"name": "analysis", "status": "passed", "duration": 30.3},
            {"name": "render", "status": "passed", "duration": 40.0},
        ]
    }
    
    (reports_dir / "pipeline_report.json").write_text(json.dumps(pipeline_report, indent=2))
    
    return reports_dir


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory with test outputs."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Create PDF directory
    pdf_dir = output_dir / "pdf"
    pdf_dir.mkdir()
    (pdf_dir / "test1.pdf").write_text("PDF content")
    (pdf_dir / "test2.pdf").write_text("PDF content")
    
    # Create figures directory
    figures_dir = output_dir / "figures"
    figures_dir.mkdir()
    (figures_dir / "fig1.png").write_text("PNG content")
    
    # Create data directory
    data_dir = output_dir / "data"
    data_dir.mkdir()
    (data_dir / "data1.csv").write_text("CSV content")
    
    # Create slides directory
    slides_dir = output_dir / "slides"
    slides_dir.mkdir()
    (slides_dir / "slide1.pdf").write_text("Slide content")
    (slides_dir / "slide2.pdf").write_text("Slide content")
    
    # Create web directory
    web_dir = output_dir / "web"
    web_dir.mkdir()
    (web_dir / "page1.html").write_text("<html>Test</html>")
    
    return output_dir


class TestManuscriptMetrics:
    """Test manuscript metrics collection."""
    
    def test_collect_manuscript_metrics(self, temp_manuscript_dir):
        """Test collecting metrics from manuscript directory."""
        metrics = collect_manuscript_metrics(temp_manuscript_dir)
        
        assert metrics.sections == 2
        assert metrics.total_words > 20  # Approximate word count
        assert metrics.total_lines > 10
        assert len(metrics.markdown_files) == 2
        assert metrics.equations == 2  # One $$ and one \[ \]
        assert metrics.figures == 1
        assert metrics.references >= 1
    
    def test_collect_manuscript_metrics_empty(self, tmp_path):
        """Test collecting metrics from empty/nonexistent directory."""
        metrics = collect_manuscript_metrics(tmp_path / "nonexistent")
        
        assert metrics.sections == 0
        assert metrics.total_words == 0
        assert len(metrics.markdown_files) == 0


class TestCodebaseMetrics:
    """Test codebase metrics collection."""
    
    def test_collect_codebase_metrics(self, temp_src_dir):
        """Test collecting metrics from source directory."""
        src_dir, scripts_dir = temp_src_dir
        metrics = collect_codebase_metrics(src_dir, scripts_dir)
        
        assert metrics.source_files == 2
        assert metrics.source_lines > 5  # At least some code lines
        assert metrics.methods >= 2  # method1 and method2
        assert metrics.classes >= 1  # TestClass
        assert metrics.scripts == 1
        assert metrics.script_lines > 0
    
    def test_collect_codebase_metrics_no_scripts(self, temp_src_dir):
        """Test collecting metrics without scripts directory."""
        src_dir, _ = temp_src_dir
        metrics = collect_codebase_metrics(src_dir, None)
        
        assert metrics.source_files == 2
        assert metrics.scripts == 0
        assert metrics.script_lines == 0


class TestTestMetrics:
    """Test test metrics collection."""
    
    def test_collect_test_metrics(self, temp_reports_dir):
        """Test collecting metrics from test reports."""
        metrics = collect_test_metrics(temp_reports_dir)
        
        assert metrics.total_tests == 100
        assert metrics.passed == 95
        assert metrics.failed == 5
        assert metrics.skipped == 0
        assert metrics.coverage_percent == 92.5
        assert metrics.execution_time == 45.2
        assert metrics.test_files > 0  # Estimated
    
    def test_collect_test_metrics_missing_report(self, tmp_path):
        """Test collecting metrics when report doesn't exist."""
        metrics = collect_test_metrics(tmp_path)

        assert metrics.total_tests == -1  # Special value indicating "unavailable"
        assert metrics.passed == 0
        assert metrics.coverage_percent == 0.0


class TestOutputMetrics:
    """Test output metrics collection."""
    
    def test_collect_output_metrics(self, temp_output_dir):
        """Test collecting metrics from output directory."""
        metrics = collect_output_metrics(temp_output_dir)
        
        assert metrics.pdf_files == 2
        assert metrics.pdf_size_mb > 0
        assert metrics.figures == 1
        assert metrics.data_files == 1
        assert metrics.slides == 2
        assert metrics.web_outputs == 1
        assert metrics.total_outputs == 7  # Sum of all
    
    def test_collect_output_metrics_empty(self, tmp_path):
        """Test collecting metrics from empty output directory."""
        metrics = collect_output_metrics(tmp_path / "nonexistent")
        
        assert metrics.pdf_files == 0
        assert metrics.total_outputs == 0


class TestPipelineMetrics:
    """Test pipeline metrics collection."""
    
    def test_collect_pipeline_metrics(self, temp_reports_dir):
        """Test collecting metrics from pipeline report."""
        metrics = collect_pipeline_metrics(temp_reports_dir)
        
        assert metrics.total_duration == 120.5
        assert metrics.stages_passed == 4
        assert metrics.stages_failed == 0
        assert metrics.bottleneck_stage == "tests"  # Longest duration (45.2s)
        assert metrics.bottleneck_duration == 45.2
        assert metrics.bottleneck_percent > 0
    
    def test_collect_pipeline_metrics_missing_report(self, tmp_path):
        """Test collecting metrics when report doesn't exist."""
        metrics = collect_pipeline_metrics(tmp_path)
        
        assert metrics.total_duration == 0.0
        assert metrics.stages_passed == 0


class TestProjectMetrics:
    """Test complete project metrics collection."""
    
    def test_collect_project_metrics(self, tmp_path):
        """Test collecting all metrics for a project."""
        # Set up project structure
        project_root = tmp_path / "projects" / "test_project"
        project_root.mkdir(parents=True)
        
        # Create minimal structure
        manuscript_dir = project_root / "manuscript"
        manuscript_dir.mkdir()
        (manuscript_dir / "01_intro.md").write_text("# Test\n\nTest content with 5 words.\n")
        
        src_dir = project_root / "src"
        src_dir.mkdir()
        (src_dir / "test.py").write_text("def test():\n    pass\n")
        
        reports_dir = project_root / "output" / "reports"
        reports_dir.mkdir(parents=True)
        
        test_report = {"project": {"total": 10, "passed": 10, "failed": 0, "skipped": 0, "coverage_percent": 100.0}, "summary": {"total_execution_time": 1.0}}
        (reports_dir / "test_results.json").write_text(json.dumps(test_report))
        
        pipeline_report = {"total_duration": 60.0, "stages": [{"name": "test", "status": "passed", "duration": 60.0}]}
        (reports_dir / "pipeline_report.json").write_text(json.dumps(pipeline_report))
        
        output_dir = tmp_path / "output" / "test_project"
        output_dir.mkdir(parents=True)
        
        # Collect metrics
        metrics = collect_project_metrics(tmp_path, "test_project")
        
        assert metrics.name == "test_project"
        assert metrics.manuscript.sections >= 1
        assert metrics.codebase.source_files >= 1
        assert metrics.tests.total_tests == 10
        assert metrics.pipeline.total_duration == 60.0


class TestAggregateMetrics:
    """Test aggregate metrics generation."""
    
    def test_generate_aggregate_metrics(self):
        """Test generating aggregate metrics from multiple projects."""
        # Create mock project metrics
        project1 = ProjectMetrics(
            name="project1",
            manuscript=ManuscriptMetrics(total_words=1000, sections=4, equations=10, figures=5, references=20),
            codebase=CodebaseMetrics(source_lines=500, methods=25, classes=5, scripts=3),
            tests=TestMetrics(total_tests=100, passed=100, failed=0, coverage_percent=95.0, execution_time=10.0),
            outputs=OutputMetrics(pdf_files=5, pdf_size_mb=2.0, figures=5, data_files=3, slides=10, web_outputs=2, total_outputs=25),
            pipeline=PipelineMetrics(total_duration=120.0, stages_passed=6, stages_failed=0, bottleneck_stage="tests", bottleneck_duration=45.0, bottleneck_percent=37.5)
        )
        
        project2 = ProjectMetrics(
            name="project2",
            manuscript=ManuscriptMetrics(total_words=800, sections=3, equations=8, figures=4, references=15),
            codebase=CodebaseMetrics(source_lines=400, methods=20, classes=4, scripts=2),
            tests=TestMetrics(total_tests=80, passed=80, failed=0, coverage_percent=92.0, execution_time=8.0),
            outputs=OutputMetrics(pdf_files=4, pdf_size_mb=1.5, figures=4, data_files=2, slides=8, web_outputs=1, total_outputs=19),
            pipeline=PipelineMetrics(total_duration=100.0, stages_passed=6, stages_failed=0, bottleneck_stage="render", bottleneck_duration=40.0, bottleneck_percent=40.0)
        )
        
        projects = [project1, project2]
        aggregates = generate_aggregate_metrics(projects)
        
        # Check manuscript aggregates
        assert aggregates['manuscript']['total_words'] == 1800
        assert aggregates['manuscript']['total_sections'] == 7
        assert aggregates['manuscript']['total_equations'] == 18
        
        # Check test aggregates
        assert aggregates['tests']['total_tests'] == 180
        assert aggregates['tests']['total_passed'] == 180
        assert aggregates['tests']['average_coverage'] == 93.5
        
        # Check pipeline aggregates
        assert aggregates['pipeline']['total_duration'] == 220.0
        assert aggregates['pipeline']['average_duration'] == 110.0


class TestComparativeTables:
    """Test comparative table generation."""
    
    def test_generate_comparative_tables(self):
        """Test generating comparative tables."""
        project1 = ProjectMetrics(
            name="project1",
            manuscript=ManuscriptMetrics(total_words=1000, sections=4),
            codebase=CodebaseMetrics(),
            tests=TestMetrics(total_tests=100, passed=100, coverage_percent=95.0, execution_time=10.0),
            outputs=OutputMetrics(pdf_files=5, pdf_size_mb=2.0, figures=5, slides=10),
            pipeline=PipelineMetrics(total_duration=120.0, bottleneck_stage="tests", bottleneck_percent=37.5)
        )
        
        project2 = ProjectMetrics(
            name="project2",
            manuscript=ManuscriptMetrics(total_words=800, sections=3),
            codebase=CodebaseMetrics(),
            tests=TestMetrics(total_tests=80, passed=80, coverage_percent=92.0, execution_time=8.0),
            outputs=OutputMetrics(pdf_files=4, pdf_size_mb=1.5, figures=4, slides=8),
            pipeline=PipelineMetrics(total_duration=100.0, bottleneck_stage="render", bottleneck_percent=40.0)
        )
        
        projects = [project1, project2]
        tables = generate_comparative_tables(projects)
        
        assert 'manuscript_comparison' in tables
        assert 'test_comparison' in tables
        assert 'output_comparison' in tables
        assert 'pipeline_comparison' in tables
        
        # Check manuscript comparison
        assert len(tables['manuscript_comparison']) == 2
        assert tables['manuscript_comparison'][0]['project'] == 'project1'
        assert tables['manuscript_comparison'][0]['words'] == 1000


class TestRecommendations:
    """Test recommendation generation."""
    
    def test_generate_recommendations_all_good(self):
        """Test recommendations when all metrics are good."""
        project = ProjectMetrics(
            name="good_project",
            manuscript=ManuscriptMetrics(total_words=2000),
            codebase=CodebaseMetrics(),
            tests=TestMetrics(total_tests=100, passed=100, failed=0, coverage_percent=95.0),
            outputs=OutputMetrics(),
            pipeline=PipelineMetrics(bottleneck_percent=30.0)
        )
        
        recommendations = generate_recommendations([project])
        
        # Should have positive recommendations
        assert any("coverage" in rec.lower() for rec in recommendations)
        assert any("pass" in rec.lower() for rec in recommendations)
    
    def test_generate_recommendations_low_coverage(self):
        """Test recommendations with low coverage."""
        project = ProjectMetrics(
            name="low_coverage_project",
            manuscript=ManuscriptMetrics(total_words=2000),
            codebase=CodebaseMetrics(),
            tests=TestMetrics(total_tests=100, passed=100, failed=0, coverage_percent=75.0),
            outputs=OutputMetrics(),
            pipeline=PipelineMetrics()
        )
        
        recommendations = generate_recommendations([project])
        
        # Should recommend improving coverage
        assert any("coverage" in rec.lower() and "90%" in rec for rec in recommendations)
    
    def test_generate_recommendations_failed_tests(self):
        """Test recommendations with failed tests."""
        project = ProjectMetrics(
            name="failed_tests_project",
            manuscript=ManuscriptMetrics(total_words=2000),
            codebase=CodebaseMetrics(),
            tests=TestMetrics(total_tests=100, passed=90, failed=10, coverage_percent=95.0),
            outputs=OutputMetrics(),
            pipeline=PipelineMetrics()
        )
        
        recommendations = generate_recommendations([project])
        
        # Should recommend fixing failures
        assert any("fail" in rec.lower() for rec in recommendations)


class TestExecutiveSummary:
    """Test executive summary generation."""
    
    def test_save_executive_summary(self, tmp_path):
        """Test saving executive summary in multiple formats."""
        summary = ExecutiveSummary(
            timestamp="2025-12-28T10:00:00",
            total_projects=2,
            aggregate_metrics={
                'manuscript': {
                    'total_words': 1000,
                    'total_sections': 5,
                    'total_equations': 2,
                    'total_figures': 1,
                    'total_references': 3,
                },
                'codebase': {
                    'total_source_lines': 500,
                    'total_methods': 10,
                    'total_classes': 2,
                    'total_scripts': 1,
                },
                'tests': {
                    'total_tests': 50,
                    'total_passed': 48,
                    'total_failed': 2,
                    'average_coverage': 85.0,
                    'total_execution_time': 10.0,
                },
                'outputs': {
                    'total_pdfs': 2,
                    'total_size_mb': 1.5,
                    'total_figures': 5,
                    'total_slides': 1,
                    'total_web': 1,
                },
                'pipeline': {
                    'total_duration': 120.0,
                    'average_duration': 60.0,
                    'total_stages_passed': 4,
                    'total_stages_failed': 0,
                }
            },
            project_metrics=[],
            health_scores={},
            comparative_tables={},
            recommendations=["Test recommendation"]
        )
        
        saved_files = save_executive_summary(summary, tmp_path)
        
        assert 'json' in saved_files
        assert 'markdown' in saved_files
        assert 'html' in saved_files
        
        # Verify files exist
        assert saved_files['json'].exists()
        assert saved_files['markdown'].exists()
        assert saved_files['html'].exists()
        
        # Verify JSON content
        with open(saved_files['json']) as f:
            data = json.load(f)
        assert data['total_projects'] == 2
        assert data['timestamp'] == "2025-12-28T10:00:00"


class TestIntegration:
    """Integration tests for executive reporter."""
    
    def test_full_workflow(self, tmp_path):
        """Test complete workflow from metrics collection to report generation."""
        # This test would require a more complete project structure
        # For now, we'll test that the function can be called without errors
        summary = ExecutiveSummary(
            timestamp="2025-12-28T10:00:00",
            total_projects=1,
            aggregate_metrics={
                'manuscript': {
                    'total_words': 0,
                    'total_sections': 0,
                    'total_equations': 0,
                    'total_figures': 0,
                    'total_references': 0,
                },
                'codebase': {
                    'total_source_lines': 0,
                    'total_methods': 0,
                    'total_classes': 0,
                    'total_scripts': 0,
                },
                'tests': {
                    'total_tests': 0,
                    'total_passed': 0,
                    'total_failed': 0,
                    'average_coverage': 0.0,
                    'total_execution_time': 0.0,
                },
                'outputs': {
                    'total_pdfs': 0,
                    'total_size_mb': 0.0,
                    'total_figures': 0,
                    'total_slides': 0,
                    'total_web': 0,
                },
                'pipeline': {
                    'total_duration': 0.0,
                    'average_duration': 0.0,
                    'total_stages_passed': 0,
                    'total_stages_failed': 0,
                }
            },
            project_metrics=[],
            health_scores={},
            comparative_tables={},
            recommendations=[]
        )
        
        # Should be able to save without errors
        saved_files = save_executive_summary(summary, tmp_path)
        assert len(saved_files) == 3
