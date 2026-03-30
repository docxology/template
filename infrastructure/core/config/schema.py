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

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypedDict


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
    barcodes: bool
    metadata: bool
    hashing: bool
    encryption: bool
    overlay_text: str
    overlay_opacity: float
    pdf_password: str


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
    keywords: list[str]
    metadata: dict[str, str]
    project_config: dict[str, Any]  # passthrough for project-specific config sections
    experiment: dict[str, Any]      # passthrough for project experimental parameters
