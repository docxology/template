"""template_search_project — domain logic for the literature workflow.

This package keeps *all* business logic for the project:

* :mod:`template_search_project.config` — typed access to ``manuscript/config.yaml``.
* :mod:`template_search_project.pipeline` — pure orchestration: search →
  enrich → export → synthesise. Imports from ``infrastructure.*``; never
  performs I/O directly.
* :mod:`template_search_project.synthesis` — turns enriched papers into
  LLM prompts and parses the LLM response back into structured records.
* :mod:`template_search_project.report` — assembles the final markdown
  reading report and BibTeX file.

Per the template's thin-orchestrator pattern, ``scripts/`` import from
this package and handle only filesystem I/O / visualisation /
orchestration.
"""

from __future__ import annotations

from .config import ProjectConfig, load_project_config
from .llm_runtime import build_llm_callable
from .figures import (
    generate_all_figures,
    load_search_result,
    plot_papers_per_source,
    plot_score_distribution,
    plot_year_histogram,
)
from .manuscript_variables import (
    ManuscriptVariables,
    compute_variables,
    substitute_in_text,
    write_variables,
)
from .pipeline import LiteratureRunArtifacts, run_literature_pipeline
from .report import write_reading_report
from .synthesis import (
    SynthesisResult,
    build_corpus_block,
    build_paper_block,
    synthesise_corpus,
    synthesise_per_paper,
)

__all__ = [
    "ProjectConfig",
    "load_project_config",
    "build_llm_callable",
    "LiteratureRunArtifacts",
    "run_literature_pipeline",
    "SynthesisResult",
    "build_paper_block",
    "build_corpus_block",
    "synthesise_per_paper",
    "synthesise_corpus",
    "write_reading_report",
    "generate_all_figures",
    "plot_papers_per_source",
    "plot_year_histogram",
    "plot_score_distribution",
    "load_search_result",
    "ManuscriptVariables",
    "compute_variables",
    "substitute_in_text",
    "write_variables",
]

from .analysis import (
    StageResult,
    validate_bibliography_completeness,
    validate_variables_resolved,
    audit_infrastructure_imports,
    check_determinism_artifacts,
    run_project_tests,
)

__all__.extend(
    [
        "StageResult",
        "validate_bibliography_completeness",
        "validate_variables_resolved",
        "audit_infrastructure_imports",
        "check_determinism_artifacts",
        "run_project_tests",
    ]
)

from .deep_search import (
    DeepSearchArtifacts,
    KeywordResult,
    build_rich_paper_block,
    run_deep_search,
    safe_id as deep_safe_id,
    slugify as deep_slugify,
    write_aggregate_report,
    write_keyword_report,
    write_per_paper_note,
)

__all__.extend(
    [
        "DeepSearchArtifacts",
        "KeywordResult",
        "build_rich_paper_block",
        "run_deep_search",
        "deep_safe_id",
        "deep_slugify",
        "write_aggregate_report",
        "write_keyword_report",
        "write_per_paper_note",
    ]
)
