"""Tests for infrastructure.reporting._executive_health."""

from infrastructure.reporting._executive_health import (
    _score_tier,
    _COVERAGE_TIERS,
    _WORD_TIERS,
    _OUTPUT_TIERS,
    calculate_project_health_score,
    generate_recommendations,
)
from infrastructure.reporting._executive_models import (
    CodebaseMetrics,
    ManuscriptMetrics,
    OutputMetrics,
    PipelineMetrics,
    ProjectMetrics,
    TestMetrics,
)


def _make_project(
    name="proj1",
    coverage=90.0,
    total_tests=100,
    failed=0,
    words=2000,
    pdf_files=5,
    figures=3,
    slides=1,
    web_outputs=2,
    bottleneck_percent=30.0,
    bottleneck_stage="Build",
    classes=10,
    methods=30,
):
    return ProjectMetrics(
        name=name,
        manuscript=ManuscriptMetrics(total_words=words),
        codebase=CodebaseMetrics(classes=classes, methods=methods),
        tests=TestMetrics(
            coverage_percent=coverage,
            total_tests=total_tests,
            failed=failed,
            passed=total_tests - failed,
        ),
        outputs=OutputMetrics(
            pdf_files=pdf_files,
            figures=figures,
            slides=slides,
            web_outputs=web_outputs,
        ),
        pipeline=PipelineMetrics(
            bottleneck_percent=bottleneck_percent,
            bottleneck_stage=bottleneck_stage,
        ),
    )


class TestScoreTier:
    def test_coverage_excellent(self):
        result = _score_tier(_COVERAGE_TIERS, 95)
        assert result["grade"] == "A"
        assert result["score"] == 40

    def test_coverage_good(self):
        result = _score_tier(_COVERAGE_TIERS, 85)
        assert result["grade"] == "B"

    def test_coverage_adequate(self):
        result = _score_tier(_COVERAGE_TIERS, 75)
        assert result["grade"] == "C"

    def test_coverage_poor(self):
        result = _score_tier(_COVERAGE_TIERS, 50)
        assert result["grade"] == "F"
        assert result["score"] == 0

    def test_word_tiers(self):
        assert _score_tier(_WORD_TIERS, 3000)["grade"] == "A"
        assert _score_tier(_WORD_TIERS, 1500)["grade"] == "B"
        assert _score_tier(_WORD_TIERS, 700)["grade"] == "C"
        assert _score_tier(_WORD_TIERS, 100)["grade"] == "F"

    def test_output_tiers(self):
        assert _score_tier(_OUTPUT_TIERS, 15)["grade"] == "A"
        assert _score_tier(_OUTPUT_TIERS, 7)["grade"] == "B"
        assert _score_tier(_OUTPUT_TIERS, 3)["grade"] == "C"
        assert _score_tier(_OUTPUT_TIERS, 1)["grade"] == "F"

    def test_label_substitution(self):
        result = _score_tier(_WORD_TIERS, 3000, label="3000")
        assert "3000" in result["reason"]


class TestCalculateProjectHealthScore:
    def test_perfect_project(self):
        p = _make_project(coverage=95, total_tests=200, failed=0, words=5000, pdf_files=5, figures=5, slides=2, web_outputs=2)
        score = calculate_project_health_score(p)
        assert score["score"] == 100  # 40 + 30 + 20 + 10
        assert score["grade"] == "A"
        assert score["status"] == "Excellent"

    def test_poor_project(self):
        p = _make_project(coverage=50, total_tests=10, failed=5, words=100, pdf_files=0, figures=0, slides=0, web_outputs=0)
        score = calculate_project_health_score(p)
        assert score["grade"] == "F"
        assert score["score"] == 0

    def test_no_tests(self):
        p = _make_project(total_tests=0, failed=0)
        score = calculate_project_health_score(p)
        assert score["factors"]["test_failures"]["grade"] == "F"

    def test_low_failure_rate(self):
        p = _make_project(total_tests=100, failed=3)
        score = calculate_project_health_score(p)
        assert score["factors"]["test_failures"]["grade"] == "B"

    def test_moderate_failure_rate(self):
        p = _make_project(total_tests=100, failed=8)
        score = calculate_project_health_score(p)
        assert score["factors"]["test_failures"]["grade"] == "C"

    def test_high_failure_rate(self):
        p = _make_project(total_tests=100, failed=20)
        score = calculate_project_health_score(p)
        assert score["factors"]["test_failures"]["grade"] == "F"

    def test_grade_boundaries(self):
        # Test D grade (60-70)
        p = _make_project(coverage=75, total_tests=100, failed=5, words=600, pdf_files=1, figures=1, slides=0, web_outputs=0)
        score = calculate_project_health_score(p)
        assert score["grade"] in ("A", "B", "C", "D", "F")

    def test_has_all_factors(self):
        p = _make_project()
        score = calculate_project_health_score(p)
        assert "test_coverage" in score["factors"]
        assert "test_failures" in score["factors"]
        assert "manuscript_size" in score["factors"]
        assert "outputs" in score["factors"]
        assert "percentage" in score
        assert "max_score" in score


class TestGenerateRecommendations:
    def test_healthy_projects(self):
        projects = [_make_project("a", coverage=95), _make_project("b", coverage=92)]
        recs = generate_recommendations(projects)
        assert isinstance(recs, list)
        assert len(recs) > 0
        # Should have portfolio health
        assert any("Portfolio Health" in r for r in recs)

    def test_low_coverage_projects(self):
        projects = [_make_project("low_cov", coverage=60)]
        recs = generate_recommendations(projects)
        assert any("Test Coverage" in r for r in recs)

    def test_failing_tests_critical(self):
        projects = [_make_project("failing", total_tests=10, failed=5)]
        recs = generate_recommendations(projects)
        assert any("Critical Test Failures" in r for r in recs)

    def test_failing_tests_minor(self):
        projects = [_make_project("minor_fail", total_tests=100, failed=2)]
        recs = generate_recommendations(projects)
        assert any("Test Failures" in r for r in recs)

    def test_no_test_failures(self):
        projects = [_make_project("clean")]
        recs = generate_recommendations(projects)
        assert any("Test Integrity" in r for r in recs)

    def test_slow_pdf_rendering(self):
        projects = [_make_project("slow", bottleneck_percent=60, bottleneck_stage="PDF Rendering")]
        recs = generate_recommendations(projects)
        assert any("PDF Performance" in r for r in recs)

    def test_slow_infra_tests(self):
        projects = [_make_project("slow", bottleneck_percent=55, bottleneck_stage="Infrastructure Tests")]
        recs = generate_recommendations(projects)
        assert any("Test Performance" in r for r in recs)

    def test_slow_analysis(self):
        projects = [_make_project("slow", bottleneck_percent=55, bottleneck_stage="Project Analysis")]
        recs = generate_recommendations(projects)
        assert any("Analysis Performance" in r for r in recs)

    def test_slow_other_stage(self):
        projects = [_make_project("slow", bottleneck_percent=55, bottleneck_stage="Setup")]
        recs = generate_recommendations(projects)
        assert any("Performance" in r for r in recs)

    def test_short_manuscript(self):
        projects = [_make_project("short", words=300)]
        recs = generate_recommendations(projects)
        assert any("Manuscript Completeness" in r for r in recs)

    def test_medium_manuscript(self):
        projects = [_make_project("medium", words=700)]
        recs = generate_recommendations(projects)
        assert any("Manuscript Completeness" in r for r in recs)

    def test_poor_outputs(self):
        projects = [_make_project("bare", pdf_files=0, figures=1, slides=0, web_outputs=0)]
        recs = generate_recommendations(projects)
        assert any("Output Richness" in r for r in recs)

    def test_multi_project_comparison(self):
        projects = [
            _make_project("best", coverage=98),
            _make_project("worst", coverage=75),
        ]
        recs = generate_recommendations(projects)
        assert any("Best Practice" in r for r in recs)

    def test_comprehensive_manuscript(self):
        projects = [
            _make_project("a", words=3000),
            _make_project("b", words=500),
        ]
        recs = generate_recommendations(projects)
        assert any("Comprehensive Research" in r for r in recs)

    def test_low_methods_per_class(self):
        projects = [_make_project("sparse", classes=20, methods=10)]
        recs = generate_recommendations(projects)
        assert any("Code Structure" in r for r in recs)

    def test_portfolio_excellent(self):
        projects = [_make_project("a", coverage=95), _make_project("b", coverage=95)]
        recs = generate_recommendations(projects)
        assert any("Excellent" in r for r in recs)

    def test_portfolio_poor(self):
        projects = [_make_project("a", coverage=50, words=100, total_tests=10, failed=5,
                                  pdf_files=0, figures=0, slides=0, web_outputs=0)]
        recs = generate_recommendations(projects)
        assert any("requires attention" in r for r in recs)
