"""Core config subpackage — YAML/env configuration loading, queries, and CLI.

Re-exports primary symbols for ``from infrastructure.core.config import …`` usage.
"""

from __future__ import annotations

from infrastructure.core.config.loader import (
    YAML_AVAILABLE,
    find_config_file,
    get_config_as_dict,
    load_config,
)
from infrastructure.core.config.queries import (
    get_review_types,
    get_translation_languages,
)
from infrastructure.core.config.schema import (
    clear_project_schema_extensions,
    get_project_schema_extensions,
    register_project_schema_extension,
)

__all__ = [
    "YAML_AVAILABLE",
    "clear_project_schema_extensions",
    "find_config_file",
    "get_config_as_dict",
    "get_project_schema_extensions",
    "get_review_types",
    "get_translation_languages",
    "load_config",
    "register_project_schema_extension",
]
