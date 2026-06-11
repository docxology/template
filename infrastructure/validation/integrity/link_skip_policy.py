"""Path-skip policy tables for markdown link and code-block path validation."""

from __future__ import annotations

import re

PATH_SKIP_SUBSTRINGS: frozenset[str] = frozenset(
    {
        # Template/placeholder paths
        "projects/{name}/",
        "projects/{project_name}",
        "{name}/manuscript/config.yaml.example",
        "your_project_name",
        "path/to/",
        "example.com",
        "your-domain.com",
        # Generic/example infrastructure paths
        "infrastructure/<module>",
        "infrastructure/example",
        "infrastructure/test_<module>",
        "infrastructure/example_module",
        "infrastructure/module/",
        "infrastructure/new_module/",
        "infrastructure/my_module/",
        "infrastructure/utils/",
        "infrastructure/helpers/",
        "infrastructure/common/",
        "infrastructure/shared/",
        "infrastructure/core.py",
        "infrastructure/test_core/",
        "infrastructure/test_specific.py",
        # Malformed markdown artifacts
        "infrastructure/AGENTS.md)",
        "infrastructure/AGENTS.md](../",
        "scripts/)",
        "scripts/`",
        # Example scripts/docs/tests
        "scripts/custom_check.py",
        "scripts/extra_checks.py",
        "scripts/my_script.py",
        "scripts/process_data.py",
        "scripts/optimization_analysis.py",
        "projects/my_project/",
        "projects/new_project/",
        "docs/my_guide.md",
        "docs/new_feature.md",
        "tests/test_my_feature.py",
        "tests/test_new_function.py",
        # Template examples in code blocks
        "project/tests/",
        "project/manuscript/",
        "project/src/",
    }
)

PATH_SKIP_KEYWORDS: frozenset[str] = frozenset(
    {
        "placeholder",
        "template",
        "example",
        "your_",
        "sample",
        "my_",
        "myproject",
        "myresearch",
        "new_",
        "test_new_",
        "test_example",
        "test_my",
        "analysis.py",
        "analyze",
        "pipeline",
        "generate_",
        "custom_",
        "train_models",
        "evaluate_models",
        "external_simulation",
        "auto_document",
        "literature_",
        "statistics_",
        "correlation_",
        "batch_",
        "optimizer_",
        "capture_",
        "assess_",
        "scientific_",
        "mymodule",
        "*[module",
        "output/pdf/*",
        "test.sh",
        "view_results.sh",
        "setup.sh",
        "run_",
        "clean.sh",
        "docs_build.sh",
        "biology_analysis.py",
        "_quality_report.py",
        "scripts/*",
        "00_*",
        "01_*",
        "07_*",
        "ml_build.sh",
        "scripts/│",
        "scripts/tests",
        "projects/templates/template_code_project/:",
        "scripts/03_render_pdf.py;",
        "data_quality",
        "infrastructure/[module_name",
        "06_fulltext_assessment",
        "serve_app.py",
        "projects/cognitive_case_diagrams/:",
        "sync_docs_notebooks.sh",
        "docs_serve.sh",
        "docs_sync_and_serve.sh",
        "module_name.py",
        "module.py",
        "bash_utils.sh.",
    }
)


def should_validate_path(path_ref: str) -> bool:
    """Return whether a path reference should be checked against the filesystem."""
    if any(pattern in path_ref for pattern in PATH_SKIP_SUBSTRINGS):
        return False

    if "{" in path_ref or "}" in path_ref or "<" in path_ref or ">" in path_ref or "*" in path_ref:
        return False

    if "://" in path_ref or "@" in path_ref:
        return False

    path_lower = path_ref.lower()
    if any(kw in path_lower for kw in PATH_SKIP_KEYWORDS):
        return False

    if any(char in path_ref for char in ("`", ")", "]", "}", "|", "\n", "\r")):
        path_stripped = path_ref.rstrip()
        if path_stripped.endswith((")", "]", "}", "`", "|", "\\n")) or "\n" in path_ref or "\r" in path_ref:
            return False
        if re.search(r"/\s*\n\s*[A-Z]", path_ref):
            return False

    return True
