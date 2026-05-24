"""Smoke import test for the consistency_lint facade (check families live under consistency/)."""

from infrastructure.validation.docs import consistency_lint


def test_consistency_lint_facade_exports_check_functions() -> None:
    for name in (
        "check_module_count_claims",
        "check_no_ghost_projects",
        "check_command_conventions",
        "check_doc_imports_resolve",
        "check_readme_files_list",
        "check_canonical_count_singularity",
        "check_stale_shell_contracts",
    ):
        assert hasattr(consistency_lint, name)
