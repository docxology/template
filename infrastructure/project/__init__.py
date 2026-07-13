"""Project management infrastructure.

Provides project discovery, validation, metadata extraction, and the
optional per-project ``setup_hook`` runner used during pipeline bootstrap.

Usage::

    from infrastructure.project import (
        ProjectInfo,
        discover_projects,
        find_setup_hook,
        get_project_metadata,
        preflight_setup_hook,
        resolve_project_root,
        run_project_setup_hook,
        validate_project_structure,
    )
"""

from typing import TYPE_CHECKING, Any

from infrastructure.project.discovery import discover_projects, resolve_project_root
from infrastructure.project.metadata import get_project_metadata
from infrastructure.project.project_info import ProjectInfo
from infrastructure.project.setup_hook import (
    find_setup_hook,
    preflight_setup_hook,
    run_project_setup_hook,
)
from infrastructure.project.validation import validate_project_structure

if TYPE_CHECKING:
    from infrastructure.project.codegraph import (
        CodeGraphCommand,
        build_codegraph_files_command,
        build_codegraph_init_command,
        build_scope_check_command,
        verify_codegraph_scope_payload,
    )
    from infrastructure.project.public_scope import (
        PUBLIC_PROJECT_NAMES,
        public_ci_source_paths,
        public_project_infos,
        public_project_names,
    )
    from infrastructure.project.copy_exemplar import (
        CopyResult,
        ExportManifest,
        copy_exemplar,
        export_exemplar,
        plan_copy,
    )

_PUBLIC_SCOPE_EXPORTS = {
    "PUBLIC_PROJECT_NAMES",
    "public_ci_source_paths",
    "public_project_infos",
    "public_project_names",
}
_CODEGRAPH_EXPORTS = {
    "CodeGraphCommand",
    "build_codegraph_files_command",
    "build_codegraph_init_command",
    "build_scope_check_command",
    "verify_codegraph_scope_payload",
}
_COPY_EXEMPLAR_EXPORTS = {
    "CopyResult",
    "ExportManifest",
    "copy_exemplar",
    "export_exemplar",
    "plan_copy",
}


def __getattr__(name: str) -> Any:
    """Lazily expose public-scope helpers without preloading the CLI module."""
    if name in _PUBLIC_SCOPE_EXPORTS:
        from importlib import import_module

        public_scope = import_module("infrastructure.project.public_scope")
        return getattr(public_scope, name)
    if name in _CODEGRAPH_EXPORTS:
        from importlib import import_module

        codegraph = import_module("infrastructure.project.codegraph")
        return getattr(codegraph, name)
    if name in _COPY_EXEMPLAR_EXPORTS:
        from importlib import import_module

        copy_exemplar_mod = import_module("infrastructure.project.copy_exemplar")
        return getattr(copy_exemplar_mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "ProjectInfo",
    "PUBLIC_PROJECT_NAMES",
    "CodeGraphCommand",
    "CopyResult",
    "ExportManifest",
    "build_codegraph_files_command",
    "build_codegraph_init_command",
    "build_scope_check_command",
    "copy_exemplar",
    "export_exemplar",
    "discover_projects",
    "find_setup_hook",
    "get_project_metadata",
    "plan_copy",
    "preflight_setup_hook",
    "public_ci_source_paths",
    "public_project_infos",
    "public_project_names",
    "resolve_project_root",
    "run_project_setup_hook",
    "validate_project_structure",
    "verify_codegraph_scope_payload",
]
