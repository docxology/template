"""Dashboard chart helpers — health and test coverage charts."""

from __future__ import annotations

from typing import Any

try:
    import matplotlib.pyplot as plt
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    Axes = Any  # type: ignore[misc, assignment]
    Figure = Any  # type: ignore[misc, assignment]

from infrastructure.core.logging.utils import get_logger
from infrastructure.reporting._dashboard_constants import COLORS
from infrastructure.reporting.executive_reporter import (
    ProjectMetrics,
)

logger = get_logger(__name__)


def draw_test_count_on_axes(
    ax: Axes,
    projects: list[ProjectMetrics],
    *,
    include_failed: bool = True,
    title: str = "Test Counts by Project",
) -> None:
    """Plot test count bars on ``ax``."""
    project_names = [p.name for p in projects]
    total_tests = [p.tests.total_tests for p in projects]
    passed_tests = [p.tests.passed for p in projects]
    failed_tests = [p.tests.failed for p in projects]
    x = range(len(projects))
    width = 0.25

    ax.bar(
        [i - width for i in x],
        total_tests,
        width,
        label="Total",
        color=COLORS["primary"],
        alpha=0.8,
    )
    ax.bar(x, passed_tests, width, label="Passed", color=COLORS["success"], alpha=0.8)
    if include_failed:
        ax.bar(
            [i + width for i in x],
            failed_tests,
            width,
            label="Failed",
            color=COLORS["danger"],
            alpha=0.8,
        )

    ax.set_xlabel("Project", fontweight="bold")
    ax.set_ylabel("Test Count", fontweight="bold")
    ax.set_title(title, fontweight="bold")
    ax.set_xticks(list(x))
    ax.set_xticklabels(project_names, rotation=45, ha="right")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)


def draw_coverage_on_axes(
    ax: Axes,
    projects: list[ProjectMetrics],
    *,
    title: str = "Test Coverage by Project",
    compact: bool = False,
) -> None:
    """Plot coverage bars on ``ax``."""
    project_names = [p.name for p in projects]
    coverage = [p.tests.coverage_percent for p in projects]
    x = range(len(projects))

    if compact:
        ax.bar(x, coverage, color=COLORS["primary"], alpha=0.8)
        ax.axhline(y=90, color=COLORS["success"], linestyle="--", linewidth=2, label="Excellent (90%)")
        ax.axhline(y=70, color=COLORS["warning"], linestyle="--", linewidth=2, label="Adequate (70%)")
    else:
        colors = []
        for cov in coverage:
            if cov >= 95:
                colors.append(COLORS["success"])
            elif cov >= 90:
                colors.append(COLORS["warning"])
            else:
                colors.append(COLORS["danger"])
        ax.bar(x, coverage, color=colors)
        ax.axhline(y=90, color=COLORS["danger"], linestyle="--", linewidth=2, label="90% Threshold")
        for i, cov in enumerate(coverage):
            ax.text(i, cov + 1, f"{cov:.1f}%", ha="center", fontweight="bold")

    ax.set_xlabel("Project", fontweight="bold")
    ax.set_ylabel("Coverage (%)", fontweight="bold")
    ax.set_title(title, fontweight="bold")
    ax.set_xticks(list(x))
    ax.set_xticklabels(project_names, rotation=45, ha="right")
    ax.set_ylim(0, 105)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)


def create_test_count_chart(
    projects: list[ProjectMetrics],
    *,
    ax: Axes | None = None,
) -> Figure | None:
    """Create bar chart showing test counts by project."""
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))
        draw_test_count_on_axes(ax, projects)
        ax.set_title("Test Counts by Project", fontweight="bold", fontsize=14)
        plt.tight_layout()
        return fig
    draw_test_count_on_axes(ax, projects, include_failed=False, title="Test Results by Project")
    return None


def create_coverage_chart(
    projects: list[ProjectMetrics],
    *,
    ax: Axes | None = None,
) -> Figure | None:
    """Create bar chart showing coverage percentages by project."""
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))
        draw_coverage_on_axes(ax, projects)
        ax.set_title("Test Coverage by Project", fontweight="bold", fontsize=14)
        plt.tight_layout()
        return fig
    draw_coverage_on_axes(ax, projects, compact=True)
    return None
