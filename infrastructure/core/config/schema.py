"""Configuration schema types for manuscript metadata.

Defines TypedDict and dataclass types used across the config subsystem.
These are pure data definitions with no I/O or logic dependencies.

Type selection rationale:
- ``TypedDict``: used for external/YAML-sourced shapes where partial keys are
  normal (``total=False``) and dict compatibility matters (e.g., subscript access
  after ``yaml.safe_load``).
- ``@dataclass(frozen=True)``: used for internally-resolved value objects where
  all fields have defaults, immutability is required, and attribute access is
  preferred over dict subscript.

Per-project schema extensions
-----------------------------
Projects may register additional valid top-level keys via
:func:`register_project_schema_extension`. Once registered for a project,
those keys are accepted by :func:`infrastructure.core.config.loader.validate_config_keys`
without emitting "unknown config key" warnings. The registry is process-local
(a module-level dict) and is not persisted to disk; tests that mutate it
should call :func:`clear_project_schema_extensions` in a fixture.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""

from dataclasses import dataclass
from typing import Any, Mapping, TypedDict


class AuthorConfig(TypedDict, total=False):
    """Configuration for a manuscript author."""

    name: str
    corresponding: bool
    orcid: str
    email: str


class PaperConfig(TypedDict, total=False):
    """Configuration for a paper's base metadata."""

    title: str


class PublicationConfig(TypedDict, total=False):
    """Configuration for a paper's publication details."""

    doi: str


class TranslationsConfig(TypedDict, total=False):
    """Configuration for LLM translation settings."""

    enabled: bool
    languages: list[str]


class ReviewsConfig(TypedDict, total=False):
    """Configuration for LLM review settings."""

    enabled: bool
    types: list[str]


class LLMYAMLConfig(TypedDict, total=False):
    """YAML config schema for the ``llm:`` section of config.yaml."""

    translations: TranslationsConfig
    reviews: ReviewsConfig


class TestingConfig(TypedDict, total=False):
    """Configuration for test thresholds and coverage."""

    max_test_failures: int
    max_infra_test_failures: int
    max_project_test_failures: int
    infra_coverage_threshold: int
    project_coverage_threshold: int


class SteganographyConfigYAML(TypedDict, total=False):
    """YAML schema for the steganography config section."""

    enabled: bool
    overlays: bool
    overlays_enabled: bool
    barcodes: bool
    barcodes_enabled: bool
    metadata: bool
    metadata_enabled: bool
    hashing: bool
    hashing_enabled: bool
    encryption: bool
    encryption_enabled: bool
    overlay_text: str
    overlay_opacity: float
    pdf_password: str
    pdf_encryption_algorithm: str
    kmyth_enabled: bool
    kmyth_required: bool
    kmyth_binary_dir: str
    kmyth_source_dir: str
    kmyth_pcrs: list[int] | str
    kmyth_cipher: str
    kmyth_seal_artifacts: list[str] | str
    kmyth_output_suffix: str
    kmyth_overwrite: bool
    kmyth_timeout_seconds: int


class RenderFormatsConfig(TypedDict, total=False):
    """YAML schema for enabled manuscript render formats."""

    pdf: bool
    html: bool
    slides: bool
    docx: bool
    epub: bool


class RenderConfig(TypedDict, total=False):
    """YAML schema for the ``render:`` section of config.yaml."""

    formats: RenderFormatsConfig


class AnalysisConfig(TypedDict, total=False):
    """YAML schema for the ``analysis:`` section of config.yaml."""

    scripts: list[str]


@dataclass(frozen=True)
class ResolvedTestingConfig:
    """Immutable, fully-resolved testing configuration with defaults applied."""

    max_test_failures: int = 0
    max_infra_test_failures: int = 0
    max_project_test_failures: int = 0
    infra_coverage_threshold: int = 60
    project_coverage_threshold: int = 90


class ManuscriptConfig(TypedDict, total=False):
    """Full manuscript configuration combining all sections."""

    paper: PaperConfig
    authors: list[AuthorConfig]
    publication: PublicationConfig
    llm: LLMYAMLConfig
    testing: TestingConfig
    steganography: SteganographyConfigYAML
    render: RenderConfig
    analysis: AnalysisConfig
    manuscript_dir: str
    prose: dict[str, Any]
    bibliography: dict[str, Any]
    report: dict[str, Any]
    book: dict[str, Any]
    layout: dict[str, Any]
    typography: dict[str, Any]
    front_matter: dict[str, Any]
    rendering: dict[str, Any]
    units: list[dict[str, Any]]
    appendices: dict[str, Any]
    accessibility: dict[str, Any]
    content_notes: dict[str, Any]
    chapter_metadata: dict[str, Any]
    export: dict[str, Any]
    keywords: list[str]
    metadata: dict[str, str]
    project_config: dict[str, Any]  # passthrough for project-specific config sections
    experiment: dict[str, Any]  # passthrough for project experimental parameters
    sheaf: dict[str, Any]  # manifest-indexed manuscript composition configuration


def generate_manuscript_config_schema(
    project_name: str = "",
    *,
    include_registered_extensions: bool = True,
) -> dict[str, Any]:
    """Return a JSON Schema for top-level manuscript config keys.

    The schema is intentionally permissive inside each known block because
    projects can add domain-specific knobs. Strictness is applied at the
    top-level key boundary, where misspellings are easiest to catch.
    """
    properties: dict[str, Any] = {
        "paper": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
            },
            "additionalProperties": True,
        },
        "authors": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "corresponding": {"type": "boolean"},
                    "orcid": {"type": "string"},
                    "email": {"type": "string"},
                },
                "additionalProperties": True,
            },
        },
        "publication": {
            "type": "object",
            "properties": {
                "doi": {"type": "string"},
            },
            "additionalProperties": True,
        },
        "llm": {"type": "object", "additionalProperties": True},
        "testing": {"type": "object", "additionalProperties": True},
        "steganography": {"type": "object", "additionalProperties": True},
        "render": {
            "type": "object",
            "properties": {
                "formats": {
                    "type": "object",
                    "properties": {
                        "pdf": {"type": "boolean"},
                        "html": {"type": "boolean"},
                        "slides": {"type": "boolean"},
                        "docx": {"type": "boolean"},
                        "epub": {"type": "boolean"},
                    },
                    "additionalProperties": False,
                },
            },
            "additionalProperties": True,
        },
        "analysis": {
            "type": "object",
            "properties": {
                "scripts": {"type": "array", "items": {"type": "string"}},
            },
            "additionalProperties": True,
        },
        "manuscript_dir": {"type": "string"},
        "prose": {"type": "object", "additionalProperties": True},
        "bibliography": {"type": "object", "additionalProperties": True},
        "report": {"type": "object", "additionalProperties": True},
        "book": {"type": "object", "additionalProperties": True},
        "layout": {"type": "object", "additionalProperties": True},
        "typography": {"type": "object", "additionalProperties": True},
        "front_matter": {"type": "object", "additionalProperties": True},
        "rendering": {"type": "object", "additionalProperties": True},
        "units": {"type": "array", "items": {"type": "object", "additionalProperties": True}},
        "appendices": {"type": "object", "additionalProperties": True},
        "accessibility": {"type": "object", "additionalProperties": True},
        "content_notes": {"type": "object", "additionalProperties": True},
        "chapter_metadata": {"type": "object", "additionalProperties": True},
        "export": {"type": "object", "additionalProperties": True},
        "keywords": {"type": "array", "items": {"type": "string"}},
        "metadata": {"type": "object", "additionalProperties": {"type": "string"}},
        "project_config": {"type": "object", "additionalProperties": True},
        "experiment": {"type": "object", "additionalProperties": True},
        "sheaf": {"type": "object", "additionalProperties": True},
    }
    if include_registered_extensions:
        extensions = {}
        extensions.update(get_project_schema_extensions(""))
        if project_name:
            extensions.update(get_project_schema_extensions(project_name))
        for key in extensions:
            properties.setdefault(key, {"description": "Registered project-specific extension"})

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://docxology.github.io/template/manuscript-config.schema.json",
        "title": "Research Template Manuscript Config",
        "type": "object",
        "properties": properties,
        "additionalProperties": False,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Per-project schema extensions
#
# Projects can register additional valid top-level keys without disabling
# global validation. The registry is module-local (process-scoped); tests must
# use ``clear_project_schema_extensions()`` in a fixture to avoid leakage.
# ─────────────────────────────────────────────────────────────────────────────

_PROJECT_SCHEMA_EXTENSIONS: dict[str, dict[str, Any]] = {}


def register_project_schema_extension(project_name: str, schema: Mapping[str, Any]) -> None:
    """Register additional valid top-level config keys for a project.

    Keys present in ``schema`` are accepted as valid top-level keys in
    ``manuscript/config.yaml`` for the named project; the validator
    won't warn on them. Schema values describe the expected type
    (e.g. ``dict``, ``list``, ``str``) — they are recorded for
    documentation purposes and not currently enforced beyond
    membership.

    Calling this function twice for the same ``project_name`` merges
    the new mapping into the existing one (later keys override
    earlier ones with the same name).

    Args:
        project_name: Name of the project (matches the directory name
            under ``projects/``). Empty string registers a global
            extension that applies to all projects.
        schema: Mapping of extra top-level key name to a type or
            description. Stored as-is.
    """
    if not isinstance(project_name, str):
        raise TypeError(f"project_name must be str, got {type(project_name).__name__}")
    bucket = _PROJECT_SCHEMA_EXTENSIONS.setdefault(project_name, {})
    bucket.update(dict(schema))


def get_project_schema_extensions(project_name: str) -> Mapping[str, Any]:
    """Return registered extensions for a project (or empty mapping).

    Args:
        project_name: Name of the project to look up.

    Returns:
        A read-only view of the per-project extension mapping. Empty
        mapping if nothing has been registered for the project.
    """
    return dict(_PROJECT_SCHEMA_EXTENSIONS.get(project_name, {}))


def clear_project_schema_extensions() -> None:
    """Test helper. Clears the registry.

    Use in a pytest fixture (autouse or explicit) to keep registry
    state from leaking between tests.
    """
    _PROJECT_SCHEMA_EXTENSIONS.clear()


__all__ = [
    "AnalysisConfig",
    "AuthorConfig",
    "LLMYAMLConfig",
    "ManuscriptConfig",
    "PaperConfig",
    "PublicationConfig",
    "RenderConfig",
    "RenderFormatsConfig",
    "ResolvedTestingConfig",
    "ReviewsConfig",
    "SteganographyConfigYAML",
    "TestingConfig",
    "TranslationsConfig",
    "clear_project_schema_extensions",
    "generate_manuscript_config_schema",
    "get_project_schema_extensions",
    "register_project_schema_extension",
]
