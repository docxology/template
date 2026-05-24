"""Documentation consistency check registry."""

from infrastructure.validation.docs.consistency._shared import Inconsistency
from infrastructure.validation.docs.consistency.ghost_paths import check_no_ghost_projects, is_placeholder_name
from infrastructure.validation.docs.consistency.import_resolution import check_doc_imports_resolve
from infrastructure.validation.docs.consistency.package_counts import (
    check_canonical_count_singularity,
    check_module_count_claims,
)
from infrastructure.validation.docs.consistency.readme_inventory import check_readme_files_list
from infrastructure.validation.docs.consistency.shell_contracts import (
    check_command_conventions,
    check_stale_shell_contracts,
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
