"""Manuscript metrics computation and chapter variable injection for the
template meta-project: live-repo metric dictionaries, JSON persistence, and
``${variable}`` substitution across the numbered manuscript chapters."""

from .inject_metrics import (
    load_metrics,
    render_all_chapters,
    render_chapter,
    validate_all_resolved,
)
from .metrics import (
    build_manuscript_metrics_dict,
    build_module_inventory_table,
    count_docs_markdown_files,
    count_docs_subdirs,
    count_prompt_templates,
    count_test_functions,
    format_count,
    save_metrics_json,
)

__all__ = [
    "build_manuscript_metrics_dict",
    "build_module_inventory_table",
    "count_docs_markdown_files",
    "count_docs_subdirs",
    "count_prompt_templates",
    "count_test_functions",
    "format_count",
    "load_metrics",
    "render_all_chapters",
    "render_chapter",
    "save_metrics_json",
    "validate_all_resolved",
]
