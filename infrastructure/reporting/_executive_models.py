"""Data models for executive reporting.

Defines the dataclasses used across all executive reporting modules:
project-level metrics (manuscript, codebase, tests, outputs, pipeline)
and the top-level ExecutiveSummary container.

**Data-object strategy across infrastructure:**
- ``@dataclass`` (here, ``reporting/``): mutable domain objects that may grow methods,
  benefit from ``default_factory``, ``__post_init__``, and property descriptors.
- ``TypedDict`` (``core/config/schema.py``, ``scientific/validation.py``): config dicts
  loaded from YAML/JSON where structural typing without instantiation is preferred.
- ``NamedTuple`` (``core/runtime/eta.py``): immutable, tuple-compatible accumulator
  passed by value in a hot timing loop.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ManuscriptMetrics:
    """Manuscript metrics for a single project."""

    sections: int = 0
    total_words: int = 0
    total_lines: int = 0
    markdown_files: list[str] = field(default_factory=list)
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
    aggregate_metrics: dict[str, Any]
    project_metrics: list[ProjectMetrics]
    health_scores: dict[str, Any]  # Project health scores by project name
    comparative_tables: dict[str, Any]
    recommendations: list[str]
