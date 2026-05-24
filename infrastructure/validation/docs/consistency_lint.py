"""Documentation consistency linter.

Checks include module-count claims, ghost-project paths, command conventions,
doc import resolution, README file lists, canonical count singularity, and
stale shell-bootstrap contract drift (:func:`check_stale_shell_contracts`).

All check functions return :class:`Inconsistency` records and never mutate state.
"""

from infrastructure.validation.docs.consistency import (
    Inconsistency,
    check_canonical_count_singularity,
    check_command_conventions,
    check_doc_imports_resolve,
    check_module_count_claims,
    check_no_ghost_projects,
    check_readme_files_list,
    check_stale_shell_contracts,
    is_placeholder_name,
)

__all__ = [
    "Inconsistency",
    "check_canonical_count_singularity",
    "check_command_conventions",
    "check_doc_imports_resolve",
    "check_module_count_claims",
    "check_no_ghost_projects",
    "check_readme_files_list",
    "check_stale_shell_contracts",
    "is_placeholder_name",
]
