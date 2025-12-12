"""Ollama utility functions for model discovery and server management.

Provides utilities for:
- Discovering available local Ollama models
- Selecting the best model based on preferences
- Checking Ollama server status
- Starting Ollama server if needed
- Model preloading with retry logic
- Connection health checks
"""
from __future__ import annotations

import subprocess
import time
from typing import Optional, List, Dict, Any, Tuple
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError as RequestsConnectionError

from infrastructure.core.logging_utils import get_logger
from infrastructure.core.exceptions import LLMConnectionError

logger = get_logger(__name__)

# Default model preferences in order of preference
DEFAULT_MODEL_PREFERENCES = [
    "llama3-gradient:latest",  # Large context (256K), reliable, no thinking mode issues
    "llama3.1:latest",  # Good balance of speed and quality
    "llama2:latest",    # Widely available, reliable
    "gemma2:2b",        # Fast, small, good instruction following
    "gemma3:4b",        # Medium size, good quality
    "mistral:latest",   # Alternative
    "codellama:latest", # Code-focused but can do general tasks
    # Note: qwen3 models use "thinking" mode which requires special handling
]


def is_ollama_running(base_url: str = "http://localhost:11434", timeout: float = 2.0) -> bool:
    """Check if Ollama server is running and responding.
    
    Args:
        base_url: Ollama server URL
        timeout: Connection timeout in seconds
        
    Returns:
        True if Ollama is responding, False otherwise
        
    Example:
        >>> if is_ollama_running():
        ...     print("Ollama is ready")
    """
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=timeout)
        if response.status_code == 200:
            logger.debug(f"Ollama server responding at {base_url}")
            return True
        else:
            logger.warning(f"Ollama server returned status {response.status_code} at {base_url}")
            return False
    except Timeout:
        logger.debug(f"Ollama server timeout at {base_url} (timeout={timeout}s)")
        return False
    except RequestsConnectionError as e:
        logger.debug(f"Ollama server connection failed at {base_url}: {e}")
        return False
    except RequestException as e:
        logger.debug(f"Ollama server request failed at {base_url}: {e}")
        return False


def start_ollama_server(wait_seconds: float = 3.0) -> bool:
    """Attempt to start the Ollama server.
    
    Args:
        wait_seconds: How long to wait for server to start
        
    Returns:
        True if server started successfully, False otherwise
    """
    try:
        # Try to start ollama serve in background
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        # Wait for server to be ready
        time.sleep(wait_seconds)
        return is_ollama_running()
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def get_available_models(
    base_url: str = "http://localhost:11434",
    timeout: float = 5.0,
    retries: int = 2
) -> List[Dict[str, Any]]:
    """Get list of available models from Ollama with retry logic.
    
    Args:
        base_url: Ollama server URL
        timeout: Request timeout in seconds
        retries: Number of retry attempts on failure
        
    Returns:
        List of model dictionaries with 'name', 'size', etc.
        
    Example:
        >>> models = get_available_models()
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
            
        except Timeout as e:
            last_error = f"Timeout after {timeout}s"
            if attempt < retries:
                wait_time = (attempt + 1) * 0.5
                logger.debug(f"Timeout getting models (attempt {attempt + 1}/{retries + 1}), retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.warning(f"Failed to get available models after {retries + 1} attempts: {last_error}")
                
        except RequestsConnectionError as e:
            last_error = f"Connection error: {e}"
            if attempt < retries:
                wait_time = (attempt + 1) * 0.5
                logger.debug(f"Connection error (attempt {attempt + 1}/{retries + 1}), retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.warning(f"Failed to get available models after {retries + 1} attempts: {last_error}")
                
        except RequestException as e:
            last_error = f"Request error: {e}"
            logger.warning(f"Failed to get available models: {last_error}")
            break  # Don't retry on non-network errors
    
    return []


def get_model_names(base_url: str = "http://localhost:11434") -> List[str]:
    """Get list of available model names from Ollama.
    
    Args:
        base_url: Ollama server URL
        
    Returns:
        List of model names (e.g., ["llama3:latest", "mistral:7b"])
    """
    models = get_available_models(base_url)
    return [m["name"] for m in models]


def select_best_model(
    preferences: Optional[List[str]] = None,
    base_url: str = "http://localhost:11434"
) -> Optional[str]:
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


def select_small_fast_model(base_url: str = "http://localhost:11434") -> Optional[str]:
    """Select a small, fast model for testing.
    
    Prioritizes smaller models for faster test execution.
    
    Args:
        base_url: Ollama server URL
        
    Returns:
        Model name to use, or None if no models available
    """
    fast_preferences = [
        "smollm2",
        "gemma2:2b",
        "gemma3:4b",
        "llama2:latest",
        "mistral:latest",
    ]
    return select_best_model(fast_preferences, base_url)


def ensure_ollama_ready(
    base_url: str = "http://localhost:11434",
    auto_start: bool = True
) -> bool:
    """Ensure Ollama server is running and has models available.
    
    Args:
        base_url: Ollama server URL
        auto_start: Whether to attempt starting Ollama if not running
        
    Returns:
        True if Ollama is ready with models, False otherwise
    """
    # Check if running
    if not is_ollama_running(base_url):
        if auto_start:
            logger.info("Ollama not running, attempting to start...")
            if not start_ollama_server():
                logger.warning("Failed to start Ollama server")
                return False
        else:
            return False
    
    # Check for available models
    models = get_model_names(base_url)
    if not models:
        logger.warning("No Ollama models available. Install with: ollama pull <model>")
        return False
    
    logger.info(f"Ollama ready with {len(models)} model(s): {', '.join(models[:5])}")
    return True


def get_model_info(model_name: str, base_url: str = "http://localhost:11434") -> Optional[Dict[str, Any]]:
    """Get detailed information about a specific model.
    
    Args:
        model_name: Name of the model
        base_url: Ollama server URL
        
    Returns:
        Model info dictionary or None if not found
    """
    models = get_available_models(base_url)
    for model in models:
        if model["name"] == model_name or model_name in model["name"]:
            return model
    return None


def check_model_loaded(
    model_name: str,
    base_url: str = "http://localhost:11434",
    timeout: float = 2.0
) -> Tuple[bool, Optional[str]]:
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
    check_loaded_first: bool = True
) -> Tuple[bool, Optional[str]]:
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
                    "options": {"num_predict": 1}
                },
                timeout=timeout
            )
            
            if response.status_code == 200:
                logger.debug(f"Model {model_name} preloaded successfully")
                return (True, None)
            else:
                last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                logger.warning(f"Preload returned status {response.status_code}: {last_error}")
                
        except Timeout as e:
            last_error = f"Timeout after {timeout}s (model may still be loading)"
            if attempt < retries:
                wait_time = (attempt + 1) * 2.0
                logger.debug(f"Preload timeout (attempt {attempt + 1}/{retries + 1}), retrying in {wait_time}s...")
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
                logger.debug(f"Preload connection error (attempt {attempt + 1}/{retries + 1}), retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.warning(f"Preload connection error after {retries + 1} attempts: {last_error}")
                
        except RequestException as e:
            last_error = f"Request error: {e}"
            logger.warning(f"Preload request error: {last_error}")
            break  # Don't retry on non-network errors
    
    return (False, last_error)

