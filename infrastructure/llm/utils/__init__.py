"""Utility functions for LLM operations."""

from __future__ import annotations

from infrastructure.llm.utils.heartbeat import StreamHeartbeatMonitor
from infrastructure.llm.utils.ollama import (
    SMALL_FAST_MODEL_PREFERENCES,
    check_model_loaded,
    ensure_ollama_ready,
    get_available_model_info,
    get_model_info,
    get_model_names,
    is_ollama_running,
    preload_model,
    pull_ollama_model,
    select_best_model,
    select_small_fast_model,
    small_fast_preference_matches,
    start_ollama_server,
)

__all__ = [
    "SMALL_FAST_MODEL_PREFERENCES",
    "is_ollama_running",
    "start_ollama_server",
    "get_available_model_info",
    "get_model_names",
    "select_best_model",
    "select_small_fast_model",
    "small_fast_preference_matches",
    "ensure_ollama_ready",
    "get_model_info",
    "check_model_loaded",
    "preload_model",
    "pull_ollama_model",
    "StreamHeartbeatMonitor",
]
