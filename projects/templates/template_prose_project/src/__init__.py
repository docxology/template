"""template_prose_project — domain logic for prose review.

All business logic for the project lives here; scripts/ are thin
orchestrators.

* :mod:`template_prose_project.config` — typed YAML loader.
* :mod:`template_prose_project.pipeline` — pure orchestration: read
  manuscript, run prose analysis, validate citation keys against the
  bibliography, write the prose report.
* :mod:`template_prose_project.figures` — matplotlib renderers for the
  readability dashboard, per-section word counts, citation density.
* :mod:`template_prose_project.manuscript_variables` — substitution
  variables for the abstract.
* :mod:`template_prose_project.report` — assembles the final reading
  report (markdown).
"""

from __future__ import annotations

from .config import ProjectConfig, load_project_config
from .figures import (
    generate_all_figures,
    plot_citation_density,
    plot_readability_metrics,
    plot_section_word_counts,
)
from .manuscript_variables import (
    ManuscriptVariables,
    compute_variables,
    substitute_in_text,
    write_variables,
)
from .pipeline import ProseRunArtifacts, run_prose_pipeline
from .report import write_review_report

__all__ = [
    # Config
    "ProjectConfig",
    "load_project_config",
    # Pipeline
    "ProseRunArtifacts",
    "run_prose_pipeline",
    # Figures
    "generate_all_figures",
    "plot_readability_metrics",
    "plot_section_word_counts",
    "plot_citation_density",
    # Manuscript variables
    "ManuscriptVariables",
    "compute_variables",
    "substitute_in_text",
    "write_variables",
    # Report
    "write_review_report",
]
