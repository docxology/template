"""Ollama model discovery, selection, and preloading.

Provides utilities for:
- Discovering available local Ollama models
- Selecting the best model based on preferences
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

import time
from typing import Any

import requests
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import RequestException, Timeout

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

# =============================================================================
# Model Preferences Configuration
# =============================================================================
# Default model preferences - ordered by SPEED for fast functional testing.
# Override with OLLAMA_MODEL environment variable for quality-focused work.
#
# Speed tiers (approximate tokens/sec on Apple Silicon):
#   - Ultra fast (~100+ tok/s): smollm2:135m, deepcoder:1.5b
#   - Fast (~50-70 tok/s): gemma2:2b, qwen3-vl:2b, ministral-3:3b
#   - Medium (~20-40 tok/s): gemma3:4b, llama3.1:latest
#   - Slower (~10-20 tok/s): llama3-gradient (but 256K context)
#
# Quality tiers:
#   - Best: llama3-gradient, gemma3:4b, llama3.1
#   - Good: gemma2:2b, ministral-3:3b
#   - Basic: smollm2, deepcoder
# =============================================================================
DEFAULT_MODEL_PREFERENCES = [
    # Fast models first (for functional testing)
    "smollm2",  # Ultra fast (~100+ tok/s), 135M params, good for testing
    "deepcoder:1.5b",  # Fast (~70 tok/s), 1.5B params, decent quality
    "gemma2:2b",  # Fast (~50 tok/s), good instruction following
    "qwen3-vl:2b",  # Fast, vision capable
    "ministral-3:3b",  # Good balance of speed and quality
    # Quality models (for production reviews)
    "gemma3:4b",  # Medium speed, good quality
    "llama3.1:latest",  # Good balance, 128K context
    "llama3-gradient:latest",  # Best quality, 256K context, but slower
    "mistral:latest",  # Alternative
    # Note: qwen3 (non-vl) models use "thinking" mode which requires special handling
]


def get_available_model_info(
    base_url: str = "http://localhost:11434", timeout: float = 5.0, retries: int = 2
) -> list[dict[str, Any]]:
    """Get list of available models from Ollama with retry logic.

    Args:
        base_url: Ollama server URL
        timeout: Request timeout in seconds
        retries: Number of retry attempts on failure

    Returns:
        List of model dictionaries with 'name', 'size', etc.

    Example:
        >>> models = get_available_model_info()
        >>> print(f"Found {len(models)} models")
    """
    last_error = None

    for attempt in range(retries + 1):
        try:
            response = requests.get(f"{base_url}/api/tags", timeout=timeout)
            response.raise_for_status()
            data = response.json()
            models = data.get("models", [])

            if models:
                logger.debug(f"Retrieved {len(models)} model(s) from Ollama")
            else:
                logger.warning("Ollama returned empty model list")

            return models

        except Timeout:
            last_error = f"Timeout after {timeout}s"
            if attempt < retries:
                wait_time = (attempt + 1) * 0.5
                logger.debug(
                    f"Timeout getting models (attempt {attempt + 1}/{retries + 1}), retrying in {wait_time}s..."  # noqa: E501
                )
                time.sleep(wait_time)
            else:
                logger.warning(
                    f"Failed to get available models after {retries + 1} attempts: {last_error}"
                )

        except RequestsConnectionError as e:
            last_error = f"Connection error: {e}"
            if attempt < retries:
                wait_time = (attempt + 1) * 0.5
                logger.debug(
                    f"Connection error (attempt {attempt + 1}/{retries + 1}), retrying in {wait_time}s..."  # noqa: E501
                )
                time.sleep(wait_time)
            else:
                logger.warning(
                    f"Failed to get available models after {retries + 1} attempts: {last_error}"
                )

        except RequestException as e:
            last_error = f"Request error: {e}"
            logger.warning(f"Failed to get available models: {last_error}")
            break  # Don't retry on non-network errors

    return []


def get_model_names(base_url: str = "http://localhost:11434") -> list[str]:
    """Get list of available model names from Ollama.

    Args:
        base_url: Ollama server URL

    Returns:
        List of model names (e.g., ["llama3:latest", "mistral:7b"])
    """
    models = get_available_model_info(base_url)
    return [m["name"] for m in models]


def select_best_model(
    preferences: list[str] | None = None, base_url: str = "http://localhost:11434"
) -> str | None:
    """Select the best available model based on preferences.

    Iterates through preference list and returns first available model.
    Falls back to first available model if no preference matches.

    Args:
        preferences: Ordered list of preferred model names
        base_url: Ollama server URL

    Returns:
        Model name to use, or None if no models available
    """
    available = get_model_names(base_url)

    if not available:
        return None

    prefs = preferences or DEFAULT_MODEL_PREFERENCES

    # Try each preference in order
    for pref in prefs:
        # Check for exact match
        if pref in available:
            logger.info(f"Selected model: {pref}")
            return pref

        # Check for partial match (e.g., "llama3" matches "llama3:latest")
        for model in available:
            if pref in model or model.startswith(pref.split(":")[0]):
                logger.info(f"Selected model: {model} (matched preference: {pref})")
                return model

    # Fall back to first available
    first = available[0]
    logger.info(f"No preference matched, using first available: {first}")
    return first


# Ordered list for ``select_small_fast_model`` and test harness checks (keep in sync).
SMALL_FAST_MODEL_PREFERENCES: list[str] = [
    "smollm2",
    "gemma2:2b",
    "gemma3:4b",
    "llama2:latest",
    "mistral:latest",
]


def small_fast_preference_matches(available: list[str]) -> bool:
    """True if some installed model matches a small-fast preference (not only a generic fallback).

    Uses the same matching rules as :func:`select_best_model` for
    :data:`SMALL_FAST_MODEL_PREFERENCES`.
    """
    if not available:
        return False
    for pref in SMALL_FAST_MODEL_PREFERENCES:
        if pref in available:
            return True
        for model in available:
            if pref in model or model.startswith(pref.split(":")[0]):
                return True
    return False


def select_small_fast_model(base_url: str = "http://localhost:11434") -> str | None:
    """Select a small, fast model for testing.

    Prioritizes smaller models for faster test execution.

    Args:
        base_url: Ollama server URL

    Returns:
        Model name to use, or None if no models available
    """
    return select_best_model(SMALL_FAST_MODEL_PREFERENCES, base_url)


def get_model_info(
    model_name: str, base_url: str = "http://localhost:11434"
) -> dict[str, Any] | None:
    """Get detailed information about a specific model.

    Args:
        model_name: Name of the model
        base_url: Ollama server URL

    Returns:
        Model info dictionary or None if not found
    """
    models = get_available_model_info(base_url)
    for model in models:
        if model["name"] == model_name or model_name in model["name"]:
            return model
    return None


def check_model_loaded(
    model_name: str, base_url: str = "http://localhost:11434", timeout: float = 2.0
) -> tuple[bool, str | None]:
    """Check if a model is currently loaded in Ollama's memory.

    Uses Ollama's /api/ps endpoint to check which models are currently
    loaded in GPU/system memory.

    Args:
        model_name: Name of the model to check
        base_url: Ollama server URL
        timeout: Request timeout in seconds

    Returns:
        Tuple of (is_loaded: bool, loaded_model_name: str | None)
        - is_loaded: True if the model (or a matching model) is loaded
        - loaded_model_name: Name of the loaded model if found, None otherwise

    Example:
        >>> is_loaded, loaded_name = check_model_loaded("llama3:latest")
        >>> if is_loaded:
        ...     print(f"Model {loaded_name} is already loaded")
    """
    try:
        response = requests.get(f"{base_url}/api/ps", timeout=timeout)
        if response.status_code != 200:
            logger.debug(f"Ollama /api/ps returned status {response.status_code}")
            return (False, None)

        data = response.json()
        processes = data.get("processes", [])

        if not processes:
            logger.debug("No models currently loaded in Ollama")
            return (False, None)

        logger.debug(f"Found {len(processes)} loaded model process(es)")

        # Check for exact match first
        for proc in processes:
            proc_model = proc.get("model", "")
            if proc_model == model_name:
                logger.debug(f"Exact match found: {proc_model}")
                return (True, proc_model)

        # Check for partial match (e.g., "llama3" matches "llama3:latest")
        model_base = model_name.split(":")[0] if ":" in model_name else model_name
        for proc in processes:
            proc_model = proc.get("model", "")
            proc_base = proc_model.split(":")[0] if ":" in proc_model else proc_model
            if model_base == proc_base:
                logger.debug(f"Partial match found: {proc_model} (requested: {model_name})")
                return (True, proc_model)

        loaded_models = [p.get("model", "unknown") for p in processes]
        logger.debug(f"Model {model_name} not loaded. Currently loaded: {', '.join(loaded_models)}")
        return (False, None)

    except Timeout:
        logger.debug(f"Timeout checking model load status (timeout={timeout}s)")
        return (False, None)
    except RequestsConnectionError as e:
        logger.debug(f"Connection error checking model load status: {e}")
        return (False, None)
    except RequestException as e:
        logger.warning(f"Request error checking model load status: {e}")
        return (False, None)


def preload_model(
    model_name: str,
    base_url: str = "http://localhost:11434",
    timeout: float = 60.0,
    retries: int = 1,
    check_loaded_first: bool = True,
) -> tuple[bool, str | None]:
    """Preload a model into Ollama's memory with retry logic.

    Sends a request to Ollama to load the model into memory, which can
    speed up subsequent queries. Checks if model is already loaded first
    to avoid unnecessary preloads.

    Args:
        model_name: Name of the model to preload
        base_url: Ollama server URL
        timeout: Request timeout in seconds (increased for large models)
        retries: Number of retry attempts on failure
        check_loaded_first: Check if model is already loaded before preloading

    Returns:
        Tuple of (success: bool, error_message: str | None)
        - success: True if preload was successful or already loaded
        - error_message: Error description if failed, None if successful

    Example:
        >>> success, error = preload_model("llama3:latest")
        >>> if not success:
        ...     print(f"Preload failed: {error}")
    """
    # Check if already loaded
    if check_loaded_first:
        is_loaded, loaded_name = check_model_loaded(model_name, base_url)
        if is_loaded:
            logger.debug(f"Model {model_name} already loaded ({loaded_name})")
            return (True, None)

    logger.debug(f"Preloading model {model_name} (timeout={timeout}s, retries={retries})")

    last_error = None

    for attempt in range(retries + 1):
        try:
            # Use generate endpoint with minimal prompt to trigger model load
            # This is more reliable than /api/ps for ensuring model is ready
            response = requests.post(
                f"{base_url}/api/generate",
                json={
                    "model": model_name,
                    "prompt": "test",
                    "stream": False,
                    "options": {"num_predict": 1},
                },
                timeout=timeout,
            )

            if response.status_code == 200:
                logger.debug(f"Model {model_name} preloaded successfully")
                return (True, None)
            else:
                last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                logger.warning(f"Preload returned status {response.status_code}: {last_error}")

        except Timeout:
            last_error = f"Timeout after {timeout}s (model may still be loading)"
            if attempt < retries:
                wait_time = (attempt + 1) * 2.0
                logger.debug(
                    f"Preload timeout (attempt {attempt + 1}/{retries + 1}), retrying in {wait_time}s..."  # noqa: E501
                )
                time.sleep(wait_time)
            else:
                logger.warning(f"Preload timeout after {retries + 1} attempts: {last_error}")
                # Timeout might mean model is still loading, not necessarily failed
                # Check if it's loaded now
                is_loaded, loaded_name = check_model_loaded(model_name, base_url)
                if is_loaded:
                    logger.info(f"Model {model_name} loaded despite timeout (found: {loaded_name})")
                    return (True, None)

        except RequestsConnectionError as e:
            last_error = f"Connection error: {e}"
            if attempt < retries:
                wait_time = (attempt + 1) * 1.0
                logger.debug(
                    f"Preload connection error (attempt {attempt + 1}/{retries + 1}), retrying in {wait_time}s..."  # noqa: E501
                )
                time.sleep(wait_time)
            else:
                logger.warning(
                    f"Preload connection error after {retries + 1} attempts: {last_error}"
                )

        except RequestException as e:
            last_error = f"Request error: {e}"
            logger.warning(f"Preload request error: {last_error}")
            break  # Don't retry on non-network errors

    return (False, last_error)
