"""Ollama utility functions for model discovery and server management.

Provides utilities for:
- Discovering available local Ollama models
- Selecting the best model based on preferences
- Checking Ollama server status
- Starting Ollama server if needed
- Model preloading with retry logic
- Connection health checks

Model Selection:
    Override the default model via environment variable:
        export OLLAMA_MODEL="gemma3:4b"    # For quality reviews
        export OLLAMA_MODEL="smollm2"      # For fast testing (default)

    Or set preferences programmatically:
        select_best_model(["llama3-gradient", "gemma3:4b"])

Note:
    This module re-exports from ``server`` and ``models`` sub-modules.
    All existing imports continue to work unchanged.
"""

from __future__ import annotations

from infrastructure.llm.utils.models import (
    DEFAULT_MODEL_PREFERENCES,
    check_model_loaded,
    get_available_model_info,
    get_model_info,
    get_model_names,
    preload_model,
    select_best_model,
    select_small_fast_model,
)
from infrastructure.llm.utils.server import (
    ensure_ollama_ready,
    is_ollama_running,
    start_ollama_server,
)

__all__ = [
    "DEFAULT_MODEL_PREFERENCES",
    "check_model_loaded",
    "ensure_ollama_ready",
    "get_available_model_info",
    "get_model_info",
    "get_model_names",
    "is_ollama_running",
    "preload_model",
    "select_best_model",
    "select_small_fast_model",
    "start_ollama_server",
]
