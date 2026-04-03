"""Ollama utility functions for model discovery and server management.

**This is the preferred import path** for all Ollama utilities.  Import from
``infrastructure.llm.utils.ollama`` (this module) rather than from the
implementation sub-modules ``server`` or ``models`` directly — those are
internal details subject to change.

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
"""

from __future__ import annotations

from infrastructure.llm.utils.models import (
    DEFAULT_MODEL_PREFERENCES,
    SMALL_FAST_MODEL_PREFERENCES,
    check_model_loaded,
    get_available_model_info,
    get_model_info,
    get_model_names,
    preload_model,
    select_best_model,
    select_small_fast_model,
    small_fast_preference_matches,
)
from infrastructure.llm.utils.server import (
    ensure_ollama_ready,
    is_ollama_running,
    pull_ollama_model,
    start_ollama_server,
)

__all__ = [
    "DEFAULT_MODEL_PREFERENCES",
    "SMALL_FAST_MODEL_PREFERENCES",
    "check_model_loaded",
    "ensure_ollama_ready",
    "get_available_model_info",
    "get_model_info",
    "get_model_names",
    "is_ollama_running",
    "preload_model",
    "pull_ollama_model",
    "select_best_model",
    "select_small_fast_model",
    "small_fast_preference_matches",
    "start_ollama_server",
]
