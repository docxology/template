"""Infrastructure layer - Modular build, validation, and development tools.

This package contains reusable infrastructure modules for building, validating, and
managing research projects. Organized by functionality into submodules.

Modules:
    config: Repository templates (.env.template, secure_config.yaml); see config/SKILL.md
    core: Foundation utilities (config, logging, exceptions, progress, checkpoint)
    docker: Dockerfile and docker-compose for container runs; see docker/SKILL.md
    validation: Quality & validation tools (PDF, Markdown, integrity)
    documentation: Documentation & figure management
    scientific: Scientific computing utilities
    llm: Local LLM integration for research assistance
    rendering: Multi-format output generation
    publishing: Academic publishing & dissemination
    reporting: Pipeline reporting & error aggregation
    project: Multi-project management and discovery
    skills: SKILL.md discovery and Cursor manifest (.cursor/skill_manifest.json); see skills/SKILL.md
    steganography: Optional secure PDF post-processing (overlays, barcodes, hashing)

Each subpackage includes SKILL.md (YAML frontmatter) for agent-oriented discovery in Cursor, Claude Code, and similar tools; start at infrastructure/SKILL.md.

Runtime note: Python may create __pycache__/ directories under each subpackage; they are bytecode caches, gitignored, and not part of the public API.
"""

from __future__ import annotations

__version__ = "2.0.0"
__layer__ = "infrastructure"

# Core utilities — always available, used throughout the codebase
try:
    from .core.exceptions import (
        BuildError,
        ConfigurationError,
        TemplateError,
        ValidationError,
    )
    from .core.config.loader import load_config
    from .core.logging.utils import get_logger
except ImportError as _core_e:
    raise RuntimeError(f"infrastructure core import failed: {_core_e}") from _core_e

# All other symbols should be imported from their subpackages directly:
#   from infrastructure.reporting import generate_pipeline_report
#   from infrastructure.validation import validate_pdf_rendering
#   from infrastructure.documentation import FigureManager

__all__ = [
    "TemplateError",
    "ConfigurationError",
    "ValidationError",
    "BuildError",
    "load_config",
    "get_logger",
]
