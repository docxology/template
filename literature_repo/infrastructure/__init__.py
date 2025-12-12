"""Infrastructure layer for Literature Search and Management System.

This package contains reusable infrastructure modules for literature search,
PDF management, reference tracking, and AI-powered summarization.

Modules:
    core: Foundation utilities (config, logging, exceptions, progress, checkpoint)
    llm: Local LLM integration for paper summarization and analysis
    literature: Literature search and reference management
"""

__version__ = "1.0.0"
__layer__ = "infrastructure"

# Import commonly-used items for convenient access
try:
    # Core
    from .core import (
        get_logger, setup_logger, log_operation, log_timing,
        TemplateError, ConfigurationError, ValidationError, BuildError,
        load_config
    )
    # LLM
    from .llm import (
        LLMClient,
        LLMConfig,
        is_ollama_running,
        select_best_model,
    )
    # Literature
    from .literature import (
        LiteratureSearch,
        LiteratureConfig,
        LiteratureWorkflow,
    )
except ImportError:
    # Graceful fallback if imports fail
    pass

__all__ = [
    # Modules
    "core",
    "llm",
    "literature",
    # Core exports
    "get_logger",
    "setup_logger",
    "log_operation",
    "log_timing",
    "TemplateError",
    "ConfigurationError",
    "ValidationError",
    "BuildError",
    "load_config",
    # LLM exports
    "LLMClient",
    "LLMConfig",
    "is_ollama_running",
    "select_best_model",
    # Literature exports
    "LiteratureSearch",
    "LiteratureConfig",
    "LiteratureWorkflow",
]

