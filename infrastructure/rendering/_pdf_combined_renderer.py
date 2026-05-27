"""Combined manuscript rendering helpers.

Extracted from ``PDFRenderer.render_combined()`` to reduce class size.
Public symbols are re-exported from focused submodules.
"""

from __future__ import annotations

from infrastructure.rendering._pdf_combined_bibliography import (
    discover_manuscript_bib_paths,
    inject_bibliography,
)
from infrastructure.rendering._pdf_combined_latex import (
    fix_starred_section_nameref_labels,
    postprocess_latex,
)
from infrastructure.rendering._pdf_combined_markdown import (
    CombinedMarkdownResult,
    flatten_manuscript_vars,
    preprocess_combined_markdown,
    substitute_manuscript_var_placeholders,
)
from infrastructure.rendering._pdf_combined_pandoc import (
    build_pandoc_tex_command,
    run_pandoc_conversion,
)
from infrastructure.rendering._pdf_combined_preamble import inject_latex_preamble
from infrastructure.rendering._pdf_combined_prevalidate import (
    prevalidate_markdown,
    prevalidate_source_markdown,
    verify_figure_references,
)

__all__ = [
    "CombinedMarkdownResult",
    "build_pandoc_tex_command",
    "discover_manuscript_bib_paths",
    "fix_starred_section_nameref_labels",
    "flatten_manuscript_vars",
    "inject_bibliography",
    "inject_latex_preamble",
    "postprocess_latex",
    "preprocess_combined_markdown",
    "prevalidate_markdown",
    "prevalidate_source_markdown",
    "run_pandoc_conversion",
    "substitute_manuscript_var_placeholders",
    "verify_figure_references",
]
