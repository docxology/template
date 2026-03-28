"""Health scoring and recommendations for executive reporting.

Provides project health score calculation and actionable recommendation
generation based on comprehensive project metrics analysis.
"""

from __future__ import annotations

from typing import Any

from ._executive_models import ProjectMetrics
from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

# Data-driven tier tables for health score calculation.
# Each entry: (min_value, score, grade, reason_template).
# Evaluated top-to-bottom; first matching tier wins.
_COVERAGE_TIERS = [
    (90, 40, "A", "Excellent coverage ≥90%"),
    (80, 30, "B", "Good coverage ≥80%"),
    (70, 20, "C", "Adequate coverage ≥70%"),
    (0,   0, "F", "Poor coverage <70%"),
]
_WORD_TIERS = [
    (2000, 20, "A", "Comprehensive manuscript ({} words)"),
    (1000, 15, "B", "Good manuscript ({} words)"),
    (500,  10, "C", "Basic manuscript ({} words)"),
    (0,     0, "F", "Insufficient manuscript ({} words)"),
]
_OUTPUT_TIERS = [
    (10, 10, "A", "Rich outputs ({} files)"),
    (5,   7, "B", "Good outputs ({} files)"),
    (2,   4, "C", "Basic outputs ({} files)"),
    (0,   0, "F", "Limited outputs ({} files)"),
]
_GRADE_TIERS = [
    (90, "A", "Excellent"),
    (80, "B", "Good"),
    (70, "C", "Fair"),
    (60, "D", "Poor"),
    (0,  "F", "Critical"),
]


def _score_tier(tiers: list[tuple], value: float, label: str | None = None) -> dict[str, Any]:
    """Return the factor dict for the first tier whose threshold the value meets.

    All tier tables must include a catch-all entry at threshold 0 so this
    function always returns on the first match and never falls through.
    """
    for threshold, pts, grade, reason_tpl in tiers:
        if value >= threshold:
            reason = reason_tpl.format(label if label is not None else value)
            return {"score": pts, "grade": grade, "reason": reason}
    # Unreachable: all tier tables have a (0, ...) catch-all entry.
    return {"score": 0, "grade": "F", "reason": "No tier matched"}


def calculate_project_health_score(project: ProjectMetrics) -> dict[str, Any]:
    """Calculate a health score for a project based on its metrics.

    Args:
        project: ProjectMetrics instance

    Returns:
        Dictionary with health score and breakdown
    """
    factors: dict[str, Any] = {}
    score = 0

    # Test coverage (40% weight)
    cov = _score_tier(_COVERAGE_TIERS, project.tests.coverage_percent)
    factors["test_coverage"] = cov
    score += cov["score"]

    # Test failure rate (30% weight)
    if project.tests.total_tests > 0:
        failure_rate = project.tests.failed / project.tests.total_tests
        # Tier sentinels: None threshold = exact-zero check; invert rate for ≤ comparison
        if failure_rate == 0:
            fac = {"score": 30, "grade": "A", "reason": "No test failures"}
        elif failure_rate <= 0.05:
            fac = {"score": 25, "grade": "B", "reason": f"Low failure rate {failure_rate:.1%}"}
        elif failure_rate <= 0.10:
            fac = {"score": 20, "grade": "C", "reason": f"Moderate failure rate {failure_rate:.1%}"}
        else:
            fac = {"score": 0, "grade": "F", "reason": f"High failure rate {failure_rate:.1%}"}
        factors["test_failures"] = fac
        score += fac["score"]
    else:
        factors["test_failures"] = {"score": 0, "grade": "F", "reason": "No tests found"}

    # Manuscript completeness (20% weight)
    words = project.manuscript.total_words
    ms = _score_tier(_WORD_TIERS, words, label=str(words))
    factors["manuscript_size"] = ms
    score += ms["score"]

    # Output generation (10% weight)
    outputs_generated = (
        project.outputs.pdf_files
        + project.outputs.figures
        + project.outputs.slides
        + project.outputs.web_outputs
    )
    out = _score_tier(_OUTPUT_TIERS, outputs_generated, label=str(outputs_generated))
    factors["outputs"] = out
    score += out["score"]

    max_score = 100  # 40 + 30 + 20 + 10
    percentage = score / max_score * 100
    _, grade, status = next(t for t in _GRADE_TIERS if percentage >= t[0])

    return {
        "score": score,
        "max_score": max_score,
        "percentage": percentage,
        "grade": grade,
        "status": status,
        "factors": factors,
    }


def generate_recommendations(projects: list[ProjectMetrics]) -> list[str]:
    """Generate actionable recommendations based on comprehensive project metrics analysis.

    Args:
        projects: List of ProjectMetrics

    Returns:
        List of detailed, actionable recommendation strings
    """
    recommendations = []

    # Calculate health scores for projects
    health_scores = [(p.name, calculate_project_health_score(p)) for p in projects]
    health_scores.sort(key=lambda x: x[1]["score"], reverse=True)

    # Overall portfolio health
    avg_health = sum(score["percentage"] for _, score in health_scores) / len(health_scores)
    if avg_health >= 85:
        recommendations.append(
            "🎉 **Portfolio Health**: Excellent overall project health across all metrics."
        )
    elif avg_health >= 70:
        recommendations.append(
            "✅ **Portfolio Health**: Good overall project health with room for improvement."
        )
    else:
        recommendations.append(
            "⚠️ **Portfolio Health**: Portfolio requires attention to improve overall health."
        )

    # Critical issues (F grades)
    critical_projects = [name for name, score in health_scores if score["grade"] == "F"]
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
        project_names = ", ".join(p.name for p in low_coverage)
        recommendations.append(
            f"📊 **Test Coverage**: {project_names} below 90% threshold (lowest: {worst_coverage:.1f}%). "  # noqa: E501
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
                    "Action: Check for complex equations or large figures. Consider using lighter LaTeX packages "  # noqa: E501
                    "or optimizing figure resolution."
                )
            elif stage == "Infrastructure Tests":
                recommendations.append(
                    f"⏱️ **Test Performance**: {p.name} slow test execution. "
                    "Action: Optimize slow tests, consider parallel execution, review computationally intensive tests."  # noqa: E501
                )
            elif stage == "Project Analysis":
                recommendations.append(
                    f"⏱️ **Analysis Performance**: {p.name} slow analysis scripts. "
                    "Action: Profile analysis_pipeline.py, optimize data processing, cache intermediate results."  # noqa: E501
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
            manuscript_issues.append(
                f"{p.name} (only {p.manuscript.total_words} words - critically insufficient)"
            )
        elif p.manuscript.total_words < 1000:
            manuscript_issues.append(
                f"{p.name} ({p.manuscript.total_words} words - needs expansion)"
            )

    if manuscript_issues:
        recommendations.append(
            "📝 **Manuscript Completeness**: " + "; ".join(manuscript_issues) + ". "
            "Action: Expand content to meet academic standards (target: 1000+ words). "
            "Add methodology details, results discussion, and conclusion sections."
        )

    # Output richness analysis
    output_poor = []
    for p in projects:
        total_outputs = (
            p.outputs.pdf_files + p.outputs.figures + p.outputs.slides + p.outputs.web_outputs
        )
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
                f"🏆 **Best Practice**: {best_project} demonstrates excellent test coverage ({best_coverage:.1f}%). "  # noqa: E501
                "Action: Study this project's testing approach and apply lessons to other projects."
            )

        # Manuscript size comparison
        largest_manuscript = max(p.manuscript.total_words for p in projects)
        largest_project = next(
            p.name for p in projects if p.manuscript.total_words == largest_manuscript
        )

        if largest_manuscript > 2000:
            recommendations.append(
                f"📚 **Comprehensive Research**: {largest_project} has extensive manuscript ({largest_manuscript:,} words). "  # noqa: E501
                "Consider if other projects could benefit from similar depth."
            )

    # Code quality insights
    total_classes = sum(p.codebase.classes for p in projects)
    total_methods = sum(p.codebase.methods for p in projects)
    if total_classes > 0 and total_methods > 0:
        avg_methods_per_class = total_methods / total_classes
        if avg_methods_per_class < 3:
            recommendations.append(
                f"🏗️ **Code Structure**: Low average methods per class ({avg_methods_per_class:.1f}). "  # noqa: E501
                "Action: Consider refactoring to improve encapsulation and modularity."
            )

    return recommendations
