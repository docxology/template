"""Multi-keyword deep search and its CLI orchestration: fan-out search
with per-paper LLM notes, coverage invariants, and thin CLI bodies."""

from template_search_project.search.deep_search import (
    DeepSearchArtifacts,
    KeywordResult,
    build_rich_paper_block,
    run_deep_search,
    safe_id,
    slugify,
    write_aggregate_report,
    write_keyword_report,
    write_per_paper_note,
)
from template_search_project.search.deep_search_cli import run_deep_search_cli
from template_search_project.search.search_invariants import (
    InvariantResult,
    all_invariants,
)
from template_search_project.search.search_pipeline_cli import run_search_pipeline_cli

__all__ = [
    "DeepSearchArtifacts",
    "KeywordResult",
    "build_rich_paper_block",
    "run_deep_search",
    "safe_id",
    "slugify",
    "write_aggregate_report",
    "write_keyword_report",
    "write_per_paper_note",
    "run_deep_search_cli",
    "InvariantResult",
    "all_invariants",
    "run_search_pipeline_cli",
]
