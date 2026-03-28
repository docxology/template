"""Executive reporter for cross-project metrics and summary generation.

This module re-exports public API from the executive reporting split modules.
All implementation lives in the _executive_* submodules:
  - _executive_models.py      — dataclasses (ProjectMetrics, ExecutiveSummary, …)
  - _executive_collectors.py  — metric collection from project directories
  - _executive_analysis.py    — aggregation and comparative tables
  - _executive_health.py      — health scoring and recommendations
  - _executive_renderers.py   — generate_executive_summary / save_executive_summary
  - _executive_report_formats.py — markdown and HTML serialisation

Part of the infrastructure reporting layer (Layer 1) - reusable across projects.
"""

from __future__ import annotations

from infrastructure.reporting._executive_analysis import (  # noqa: F401 — re-exported
    generate_aggregate_metrics,
    generate_comparative_tables,
)
from infrastructure.reporting._executive_collectors import (  # noqa: F401 — re-exported
    collect_codebase_metrics,
    collect_manuscript_metrics,
    collect_output_metrics,
    collect_pipeline_metrics,
    collect_project_metrics,
    collect_test_metrics,
)
from infrastructure.reporting._executive_health import (  # noqa: F401 — re-exported
    calculate_project_health_score,
    generate_recommendations,
)
from infrastructure.reporting._executive_models import (  # noqa: F401 — re-exported
    CodebaseMetrics,
    ExecutiveSummary,
    ManuscriptMetrics,
    OutputMetrics,
    PipelineMetrics,
    ProjectMetrics,
    TestMetrics,
)
from infrastructure.reporting._executive_renderers import (  # noqa: F401 — re-exported
    generate_executive_summary,
    save_executive_summary,
)
from infrastructure.reporting._executive_report_formats import (  # noqa: F401 — re-exported
    generate_html_report,
    generate_markdown_report,
)
